"""Renderiza panoramas 360° fotorrealistas (Cycles) do apartamento exportado do site.
Uso: python blend.py --views 0,1 --res 4096 --samples 96 --out /tmp/claude-0/pano/out [--exposure 0] [--save cena.blend]"""
import bpy, json, math, sys, os, time, argparse
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('--views', default='all'); ap.add_argument('--res', type=int, default=1024); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--out', default='/tmp/claude-0/pano/out'); ap.add_argument('--exposure', type=float, default=0.0)
ap.add_argument('--sun', type=float, default=4.0); ap.add_argument('--sky', type=float, default=0.25); ap.add_argument('--bgcam', type=float, default=1.6)
ap.add_argument('--spot', type=float, default=6.0); ap.add_argument('--look', default='AgX - Base Contrast'); ap.add_argument('--save', default='')
ap.add_argument('--night', action='store_true')
a = ap.parse_args()
D = '/tmp/claude-0/pano'
meta = json.load(open(f'{D}/meta.json'))
os.makedirs(a.out, exist_ok=True)
tb = lambda x, y, z: Vector((x, -z, y))          # three.js (y para cima) -> Blender (z para cima)

bpy.ops.wm.read_factory_settings(use_empty=True)
t0 = time.time()
bpy.ops.import_scene.gltf(filepath=f'{D}/casa.glb')
print('import s', round(time.time() - t0, 1), 'objetos', len(bpy.data.objects))
sc = bpy.context.scene

# ---------------------------------------------------------------- materiais: vidro realmente transparente, emissores coerentes
for m in bpy.data.materials:
    if not m.use_nodes: continue
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None: continue
    alpha = p.inputs['Alpha'].default_value
    if alpha < 0.5 and not p.inputs['Alpha'].is_linked:
        # vidro de janela e guarda-corpo: quase todo transparente, com um leve reflexo
        p.inputs['Alpha'].default_value = 0.08; p.inputs['Roughness'].default_value = 0.02
    if a.night:
        pass

# ---------------------------------------------------------------- céu e sol
w = bpy.data.worlds.new('Mundo'); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
sunB = tb(*meta['sun']).normalized()
elev = math.asin(max(0.01, sunB.z)); rot = math.atan2(sunB.x, sunB.y)
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_disc = False
sky.sun_elevation = elev; sky.sun_rotation = -rot + math.pi; sky.altitude = 60; sky.air_density = 1.2; sky.dust_density = 1.5
bgL = nt.nodes.new('ShaderNodeBackground'); bgL.inputs['Strength'].default_value = a.sky * (0.02 if a.night else 1)
nt.links.new(sky.outputs['Color'], bgL.inputs['Color'])
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load('/home/claude/casa/env/ceu.jpg')
mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
mp.inputs['Rotation'].default_value[2] = -rot + math.pi * 0.5
bgC = nt.nodes.new('ShaderNodeBackground'); bgC.inputs['Strength'].default_value = a.bgcam * (0.04 if a.night else 1)
nt.links.new(env.outputs['Color'], bgC.inputs['Color'])
lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac']); nt.links.new(bgL.outputs['Background'], mix.inputs[1]); nt.links.new(bgC.outputs['Background'], mix.inputs[2])
nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
if not a.night:
    sd = bpy.data.lights.new('Sol', 'SUN'); sd.energy = a.sun; sd.angle = math.radians(1.2); sd.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sol', sd); sc.collection.objects.link(so)
    so.rotation_euler = (-sunB).to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- spots embutidos no forro (luz quente)
for i, (x, y, z) in enumerate(meta['spots']):
    ld = bpy.data.lights.new(f'Spot{i}', 'AREA'); ld.shape = 'DISK'; ld.size = 0.07
    ld.energy = a.spot * (1.8 if a.night else 1); ld.color = (1.0, 0.83, 0.64); ld.spread = math.radians(100)
    lo = bpy.data.objects.new(f'Spot{i}', ld); lo.location = tb(x, y - 0.004, z); sc.collection.objects.link(lo)

# ---------------------------------------------------------------- luminárias embutidas visíveis (disco que brilha no forro)
dm = bpy.data.materials.new('SpotDisco'); dm.use_nodes = True
em = dm.node_tree.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.86, 0.7, 1); em.inputs['Strength'].default_value = 18 * (1.4 if a.night else 1)
dm.node_tree.links.new(em.outputs['Emission'], dm.node_tree.nodes['Material Output'].inputs['Surface'])
try: dm.cycles.emission_sampling = 'NONE'
except Exception: pass
tm = bpy.data.materials.new('SpotAro'); tm.use_nodes = True; tm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.92, 0.92, 0.9, 1)
for i, (x, y, z) in enumerate(meta['spots']):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.042, fill_type='NGON', location=tb(x, meta['H'] - 0.003, z), rotation=(math.pi, 0, 0))
    o = bpy.context.active_object; o.data.materials.append(dm); o.visible_shadow = False
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.055, fill_type='NGON', location=tb(x, meta['H'] - 0.0015, z), rotation=(math.pi, 0, 0))
    o = bpy.context.active_object; o.data.materials.append(tm); o.visible_shadow = False

# ---------------------------------------------------------------- laje do andar de cima (fecha frestas e cobre as varandas, como no prédio real)
bpy.ops.mesh.primitive_cube_add(size=1)
slab = bpy.context.active_object; slab.name = 'LajeSuperior'
slab.scale = (60, 60, 0.25); slab.location = (0, 0, meta['H'] + 0.125 + 0.0005)
ms = bpy.data.materials.new('Laje'); ms.use_nodes = True; slab.data.materials.append(ms)
# a laje fica acima do forro: também tampa qualquer fresta vista de baixo

# ---------------------------------------------------------------- render
sc.render.engine = 'CYCLES'; c = sc.cycles; c.device = 'CPU'
c.samples = a.samples; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.025
c.use_denoising = True
try: c.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
c.max_bounces = 6; c.diffuse_bounces = 3; c.glossy_bounces = 2; c.transmission_bounces = 2; c.transparent_max_bounces = 10; c.volume_bounces = 0
c.caustics_reflective = False; c.caustics_refractive = False; c.sample_clamp_indirect = 6.0; c.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = a.look
except Exception: print('look indisponível', a.look)
sc.view_settings.exposure = a.exposure
sc.render.resolution_x = a.res; sc.render.resolution_y = a.res // 2; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
cd = bpy.data.cameras.new('Pano'); cd.type = 'PANO'
try: cd.panorama_type = 'EQUIRECTANGULAR'
except Exception: cd.cycles.panorama_type = 'EQUIRECTANGULAR'
cam = bpy.data.objects.new('Pano', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_euler = (math.pi / 2, 0, 0)        # centro da imagem = +Y do Blender = -Z do three.js
if a.save: bpy.ops.wm.save_as_mainfile(filepath=a.save)
idx = range(len(meta['views'])) if a.views == 'all' else [int(v) for v in a.views.split(',')]
for i in idx:
    v = meta['views'][i]
    cam.location = tb(v['x'], meta['eye'], v['z'])
    sc.render.filepath = f"{a.out}/pano_{i:02d}.jpg"
    t = time.time(); bpy.ops.render.render(write_still=True)
    print('view', i, v['name'], 'render s', round(time.time() - t, 1), flush=True)
