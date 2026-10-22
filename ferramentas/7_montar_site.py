"""Site público (GitHub Pages): shell site.html + motor site.js."""
import os, shutil, json
from PIL import Image
app = open('site.js', encoding='utf-8').read()
data = open('data.json', encoding='utf-8').read()
tex = open('tex/manifest.json', encoding='utf-8').read()
texsrc = ("Object.assign((n, suf) => `tex/${Math.min(innerWidth, innerHeight) < 700 ? 'm/' : ''}${n}_${suf}.webp`, { plan: 'planta.webp', env: 'env/lebombo_1k_log.png', "
          "sky: 'env/ceu.jpg', m: k => `models/${k}.glb` })")
app = app.replace('/*DATA*/', data).replace('/*TEX*/', tex).replace('/*TEXSRC*/', texsrc)
# panoramas 360° disponíveis (pastas pano/<largura>/NN.jpg)
PANO_SIZES = sorted(int(d) for d in os.listdir('pano') if d.isdigit()) if os.path.isdir('pano') else []
app = app.replace('/*PANO*/[]', json.dumps(PANO_SIZES))

shell = open('site.html', encoding='utf-8').read()
head, body = shell.split('<!--BODY-->')
BASE = 'https://mpaulomcz.github.io/tour-apartamento/'
og = (f'<meta property="og:image" content="{BASE}og.jpg">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
      f'<meta property="og:url" content="{BASE}">\n<meta name="twitter:card" content="summary_large_image">')
head = head.replace('<!--OG_IMAGE-->', og)
body = body.replace('/*APP*/', app)
cdn = ('<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",'
       '"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>')
loc = ('<script type="importmap">{"imports":{"three":"/vendor/three/build/three.module.js",'
       '"three/addons/":"/vendor/three/examples/jsm/"}}</script>')
pre = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
page = pre + head + '<style>[hidden]{display:none!important}</style>\n</head>\n<body>\n' + body + '</body>\n</html>\n'

out = 'site'
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out)
shutil.copytree('dist/env', f'{out}/env'); os.makedirs(f'{out}/models')
# só as texturas que a visita usa (acabamentos fixos): menos dados para o celular
USED = ['piso_porcelanato', 'parede_pintura', 'mesa_nogueira', 'sofa_linho', 'piso_deck', 'piso_molhado', 'parede_banho', 'madeira_marcenaria',
        'quartzo', 'granito', 'travertino', 'tapete_juta', 'azulejo_metro', 'mesa_marmore', 'mesa_freijo', 'tecido']
os.makedirs(f'{out}/tex/m')
for n in USED:
    for suf in ('col', 'nor', 'rgh'):      # WebP: ~35% menor que o JPEG, suportado por todos os navegadores atuais
        im = Image.open(f'tex/{n}_{suf}.jpg'); q = 90 if suf == 'nor' else 82
        im.save(f'{out}/tex/{n}_{suf}.webp', 'WEBP', quality=q, method=6)
        im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(f'{out}/tex/m/{n}_{suf}.webp', 'WEBP', quality=q, method=6)   # celular: metade
for extra in os.listdir('models'):
    if extra.endswith('.glb'): shutil.copy(f'models/{extra}', f'{out}/models/{extra}')
shutil.copy('planta.webp', f'{out}/planta.webp')
if PANO_SIZES: shutil.copytree('pano', f'{out}/pano')
if os.path.exists('config.json'): shutil.copy('config.json', f'{out}/config.json')
if os.path.exists('og.jpg'): shutil.copy('og.jpg', f'{out}/og.jpg')
open(f'{out}/.nojekyll', 'w').write('')
open(f'{out}/index.html', 'w', encoding='utf-8').write(page.replace('<!--IMPORTMAP-->', cdn))
t = 'test_site'
if os.path.exists(t): shutil.rmtree(t)
shutil.copytree(out, t)
os.symlink('/home/claude/casa/test/vendor', f'{t}/vendor')
tt = page.replace('<!--IMPORTMAP-->', loc).replace('https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/', '/vendor/gsap/dist/')
open(f'{t}/index.html', 'w', encoding='utf-8').write(tt)
os.makedirs('/tmp/claude-0', exist_ok=True)
open('/tmp/claude-0/site_check.mjs', 'w', encoding='utf-8').write(app)
print('ok', len(page))
