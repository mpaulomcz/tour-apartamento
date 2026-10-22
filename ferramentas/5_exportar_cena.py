import time, subprocess, json
from playwright.sync_api import sync_playwright
srv = subprocess.Popen(['python3', '-m', 'http.server', '8810', '-d', '/home/claude/casa/test_site'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.8); logs = []
OUT = '/tmp/claude-0/pano'
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        pg = b.new_page(viewport={'width': 800, 'height': 500}, accept_downloads=True)
        pg.on('console', lambda m: logs.append(m.text)); pg.on('pageerror', lambda e: logs.append('ERR ' + str(e)))
        pg.add_init_script("localStorage.setItem('tour-ajuda-v2','1')")
        pg.goto('http://localhost:8810/index.html'); pg.wait_for_timeout(5000)
        pg.evaluate('__casa.intro.progress(1)'); pg.evaluate('__casa.startVisit(__casa.VIEWS[2])')
        for _ in range(60):
            pg.wait_for_timeout(1000)
            if pg.evaluate('__casa.EX.blend >= 1 && __casa.pending() === 0'): break
        pg.wait_for_timeout(6000)   # modelos glTF e tecidos
        meta = pg.evaluate("""() => {
          const C = __casa, T = C.toWorld, sp = C.getSpots(), m = new C.camera.matrix.constructor(), p = new C.camera.position.constructor(), out = [];
          if (sp) for (let i = 0; i < sp.count; i++) { sp.getMatrixAt(i, m); p.setFromMatrixPosition(m); out.push([p.x, p.y, p.z]); }
          return { H: C.H, eye: C.EYE_V, sun: [C.SUN_DIR.x, C.SUN_DIR.y, C.SUN_DIR.z], spots: out,
            lamps: C.getLamps().filter(l => l.parent === C.scene).map(l => ({ p: [l.position.x, l.position.y, l.position.z], k: l.userData.k })),
            views: C.VIEWS.map(v => { const [x, z] = T(v.p[0], v.p[1]); return { name: v.name, i: v.i, x, z, yaw: C.viewYaw(v) }; }) };
        }""")
        json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1)
        print('spots', len(meta['spots']), 'views', len(meta['views']))
        with pg.expect_download(timeout=600000) as dl:
            pg.evaluate("""async () => {
              const { GLTFExporter } = await import('three/addons/exporters/GLTFExporter.js');
              const C = __casa, hide = [];
              const hideObj = o => { if (o && o.visible) { o.visible = false; hide.push(o); } };
              C.house.traverse(o => {
                if (o.isInstancedMesh) hideObj(o);                                     // spots viram luzes no Blender
                if (o.isMesh && o.material && (o.material.isShaderMaterial || o.material.colorWrite === false || o.material.blending === 2 || o.material.isMeshBasicMaterial && o.material.transparent)) hideObj(o);
              });
              hideObj(C.getHall());
              const glb = await new GLTFExporter().parseAsync(C.house, { binary: true, onlyVisible: true, maxTextureSize: 2048 });
              hide.forEach(o => o.visible = true);
              const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([glb], { type: 'model/gltf-binary' })); a.download = 'casa.glb'; document.body.appendChild(a); a.click();
            }""")
        dl.value.save_as(f'{OUT}/casa.glb')
        b.close()
finally:
    srv.terminate()
print([l[:200] for l in logs if 'TUNNEL' not in l][:20])
