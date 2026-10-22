"""Texturas procedurais v3 — mármore com veios naturais (campo de ruído deformado), madeira com fibra vertical
realista, porcelanato pedra para áreas molhadas e trama de tecido. Reaproveita utilitários da v2.
Uso: python3 gen_textures3.py [nome ...]"""
import numpy as np, json, os, sys
from PIL import Image

OUT = 'tex'
MANP = f'{OUT}/manifest.json'
MAN = json.load(open(MANP))
ONLY = set(sys.argv[1:])
TAU = 2 * np.pi


def noise(n, sx, sy=None, seed=0):
    """Ruído gaussiano periódico; sx, sy = tamanho típico do detalhe em px (ao longo de x e de y)."""
    sy = sx if sy is None else sy
    w = np.random.default_rng(seed).standard_normal((n, n)).astype(np.float32)
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    filt = np.exp(-0.5 * (TAU ** 2) * ((fx * sx) ** 2 + (fy * sy) ** 2) / 4)
    o = np.real(np.fft.ifft2(np.fft.fft2(w) * filt)).astype(np.float32)
    o -= o.mean(); return o / (o.std() + 1e-9)


def fbm(n, sx, sy=None, octaves=5, seed=0, gain=0.5):
    sy = sx if sy is None else sy
    acc = np.zeros((n, n), np.float32); a = 1.0; t = 0
    for o in range(octaves):
        acc += a * noise(n, max(sx / 2 ** o, 0.6), max(sy / 2 ** o, 0.6), seed * 31 + o); t += a; a *= gain
    return acc / t


def warp_sample(f, dy, dx):
    """Amostragem bilinear periódica de f deslocada por (dy, dx) em px."""
    n = f.shape[0]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    y = (yy + dy) % n; x = (xx + dx) % n
    y0 = np.floor(y).astype(np.int32); x0 = np.floor(x).astype(np.int32); fy = y - y0; fx = x - x0
    y1 = (y0 + 1) % n; x1 = (x0 + 1) % n
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x1] * fx * (1 - fy) + f[y1, x0] * (1 - fx) * fy + f[y1, x1] * fx * fy)


def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
def srgb2lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin2srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def L(h): return srgb2lin(hexc(h))


def mix(a, b, t):
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32); t = np.asarray(t, np.float32)
    if a.ndim == 1: a = a[None, None, :]
    if b.ndim == 1: b = b[None, None, :]
    return a * (1 - t[..., None]) + b * t[..., None]


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def normal_map(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nn = np.stack([-dx, dy, np.ones_like(h)], -1)
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    return ((nn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


def want(name): return not ONLY or name in ONLY


def save(name, col, height, rough, strength, size_m, label, note, aux_res=None, q=90):
    Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{OUT}/{name}_col.jpg', quality=q, optimize=True)
    nm = Image.fromarray(normal_map(height, strength))
    rg = Image.fromarray((np.clip(rough, 0, 1) * 255 + 0.5).astype(np.uint8))
    if aux_res and aux_res != col.shape[0]:
        nm = nm.resize((aux_res, aux_res), Image.LANCZOS); rg = rg.resize((aux_res, aux_res), Image.LANCZOS)
    nm.save(f'{OUT}/{name}_nor.jpg', quality=90, optimize=True)
    rg.save(f'{OUT}/{name}_rgh.jpg', quality=88, optimize=True)
    MAN[name] = dict(size=size_m, label=label, note=note)
    print('ok', name, col.shape[0])


# ---------------------------------------------------------------- mármore: veios nas linhas de nível zero de um ruído deformado
def marble(n, seed, base_a, base_b, vein, vein2, gold=None, main=1.0, sec=1.0, hair=1.0, stretch=5.0, scale=1.0):
    """Veios longos e sinuosos: cruzamentos de zero de um ruído bem alongado, com deformação de domínio
    em escala grande (curvas amplas) e pequena (borda viva), largura e intensidade variando ao longo do veio."""
    s = n * scale
    wa = fbm(n, s / 3, None, 4, seed + 1) * s * 0.14; wb = fbm(n, s / 3, None, 4, seed + 2) * s * 0.14
    wc = fbm(n, s / 30, None, 3, seed + 3) * s * 0.006; wd = fbm(n, s / 30, None, 3, seed + 4) * s * 0.006
    F1 = warp_sample(fbm(n, s / 3.0, s / 3.0 * stretch, 3, seed + 5, 0.4), wa + wc, wb + wd)
    F2 = warp_sample(fbm(n, s / 6.5, s / 6.5 * stretch * 0.75, 3, seed + 6, 0.45), wa * 0.9 + wd * 2, wb * 0.9 + wc * 2)
    F3 = warp_sample(fbm(n, s / 14, s / 14 * stretch * 0.5, 3, seed + 7, 0.5), wa + wc * 3, wb + wd * 3)
    wmod = 0.45 + 1.1 * smooth(-1.3, 1.5, fbm(n, s / 5, s / 2, 3, seed + 8))
    amod = smooth(-1.0, 0.5, fbm(n, s / 4, s / 1.5, 3, seed + 9))
    v1 = np.exp(-(F1 / (0.028 * wmod)) ** 2) * (0.4 + 0.6 * amod)
    halo = np.exp(-(F1 / (0.11 * wmod)) ** 2) * (0.3 + 0.7 * amod)
    near = np.exp(-(F1 / 0.7) ** 2)
    v2 = np.exp(-(F2 / (0.022 * (0.6 + wmod))) ** 2) * smooth(-0.8, 0.9, fbm(n, s / 4, s / 1.5, 3, seed + 10)) * (0.4 + 0.6 * near)
    v3 = np.exp(-(F3 / 0.03) ** 2) * near * smooth(0.2, 1.3, fbm(n, s / 6, s / 3, 3, seed + 11))
    cloud = fbm(n, s / 2.2, s / 1.2, 6, seed + 12); spot = fbm(n, s / 40, None, 3, seed + 13)
    col = mix(L(base_a), L(base_b), np.clip(0.5 + 0.3 * cloud + 0.05 * spot, 0, 1))
    col = mix(col, L(vein2), np.clip(halo * 0.14 * main, 0, 1))
    col = mix(col, L(vein2), np.clip((v2 * 0.5 * sec + v3 * 0.3 * hair), 0, 1))
    col = mix(col, L(vein), np.clip(v1 * 0.85 * main, 0, 1))
    if gold is not None:
        gm = smooth(0.2, 1.1, fbm(n, s / 3, None, 3, seed + 14)) * np.clip(v1 + halo * 0.5, 0, 1)
        col = mix(col, L(gold), np.clip(gm * 0.5, 0, 1))
    return col, np.clip(v1 + 0.5 * v2, 0, 1), cloud


def grout_grid(N, ppm, tw, th, joint_mm):
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    gu = (xx / (tw * ppm)) % 1; gv = (yy / (th * ppm)) % 1
    d = np.minimum(np.minimum(gu, 1 - gu) * tw * ppm, np.minimum(gv, 1 - gv) * th * ppm)
    jp = joint_mm / 1000 * ppm / 2
    return 1 - smooth(jp, jp + 1.0, d), smooth(jp, jp + 4.0, d), (np.floor(yy / (th * ppm)) * 97 + np.floor(xx / (tw * ppm))).astype(np.int64)


if want('piso_porcelanato'):
    N = 2048; size = 1.8; ppm = N / size; tn = N // 2
    col = np.zeros((N, N, 3), np.float32); vein = np.zeros((N, N), np.float32)
    k = 0
    for i in range(2):
        for j in range(2):
            c, v, _ = marble(tn, 300 + 17 * k, '#f4f2ee', '#e9e6e0', '#8d8984', '#b5b0a9', gold='#b9a382', main=1.0, sec=0.9, hair=0.8)
            rot = (i * 2 + j) % 4
            c = np.rot90(c, rot); v = np.rot90(v, rot)
            tone = 1 + 0.012 * (k - 1.5)
            col[i * tn:(i + 1) * tn, j * tn:(j + 1) * tn] = c * tone; vein[i * tn:(i + 1) * tn, j * tn:(j + 1) * tn] = v
            k += 1
    grout, edge, _ = grout_grid(N, ppm, 0.9, 0.9, 2.0)
    col = mix(col, L('#d3cfc8'), grout)
    h = edge
    rg = 0.06 + 0.04 * vein + 0.7 * grout + 0.015 * fbm(N, 400, None, 3, 77)
    save('piso_porcelanato', lin2srgb(col), h, rg, 1.6, [size, size], 'Porcelanato marmorizado', 'Placa 90 × 90 cm polida, rejunte 2 mm', aux_res=1024)

if want('parede_banho'):
    N = 1024; size = 1.2; ppm = N / size
    c, v, _ = marble(N, 520, '#f2f0ec', '#e6e3dd', '#9c9891', '#bdb8b1', main=0.75, sec=0.7, hair=0.6, scale=1.1)
    grout, edge, _ = grout_grid(N, ppm, 0.6, 1.2, 1.5)
    col = mix(c, L('#d2cec7'), grout)
    save('parede_banho', lin2srgb(col), edge, 0.12 + 0.05 * v + 0.6 * grout, 1.6, [size, size], 'Porcelanato de parede', 'Placa 60 × 120 cm')

if want('mesa_marmore'):
    N = 1024
    c, v, cl = marble(N, 611, '#f6f5f2', '#e8e6e2', '#7b7f84', '#a6a9ad', main=0.85, sec=1.0, hair=1.0, stretch=4.0)
    save('mesa_marmore', lin2srgb(c), 0.02 * cl, 0.06 + 0.04 * v, 0.4, [1.6, 1.6], 'Mármore Carrara', 'Polido, peça única')

# ---------------------------------------------------------------- porcelanato pedra (áreas molhadas)
if want('piso_molhado'):
    N = 1024; size = 1.2; ppm = N / size
    grout, edge, tid = grout_grid(N, ppm, 0.6, 0.6, 2.0)
    r = np.random.default_rng(33); tone = 1 + 0.03 * r.standard_normal(100000)[tid % 100000]
    big = fbm(N, 300, None, 5, 31); mid = fbm(N, 40, None, 4, 32); grain = noise(N, 1.1, None, 34)
    fleck = smooth(2.2, 3.0, noise(N, 1.6, None, 35)); fos = smooth(1.6, 2.6, fbm(N, 14, 5, 3, 36))
    lum = 0.5 + 0.18 * big + 0.08 * mid + 0.05 * grain - 0.12 * fos
    col = mix(L('#bfbab2'), L('#dcd8d1'), np.clip(lum, 0, 1)) * tone[..., None]
    col = mix(col, L('#9a958d'), fleck * 0.5)
    col = mix(col, L('#a7a39c'), grout)
    h = edge + 0.03 * grain - 0.05 * fleck
    save('piso_molhado', lin2srgb(col), h, 0.38 + 0.05 * mid + 0.4 * grout, 1.6, [size, size], 'Porcelanato acetinado', 'Placa 60 × 60 cm, acabamento pedra')


# ---------------------------------------------------------------- madeira: fibra vertical (ao longo de v), lâminas emendadas
def veneer(name, size, early, late, seed, label, note, leaves=5, ring_px=(9, 22), cathedral=0.45, contrast=0.85,
           streak=0.35, pores=0.45, rough=(0.36, 0.52), tone_var=0.06, fleck=0.0, N=1024, sat=1.0):
    if not want(name): return
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    lw = N / leaves; li = np.floor(xx / lw).astype(np.int32); lx = (xx - li * lw) / lw       # lâmina e posição dentro dela
    # deformações em várias escalas, alongadas ao longo da fibra (y)
    w1 = fbm(N, 24, 420, 5, seed + 1); w2 = fbm(N, 6, 90, 4, seed + 2); w3 = fbm(N, 140, 900, 3, seed + 3)
    cath = r.random(leaves + 1) < cathedral
    cx = r.uniform(0.2, 0.8, leaves + 1); amp = r.uniform(0.6, 1.4, leaves + 1); ph = r.uniform(0, 1, leaves + 1)
    dens = r.uniform(1 / ring_px[1], 1 / ring_px[0], leaves + 1) * lw
    # coordenada de anel: reta (fibra paralela) ou catedral (parábolas que fecham ao longo de y)
    yv = yy / N
    Rs = lx * 1.0 + 0.010 * w1 + 0.003 * w2 + 0.03 * w3
    Rc = np.sqrt((lx - cx[li]) ** 2 * 1.0 + 0.0001) - 0.18 * amp[li] * (0.5 + 0.5 * np.sin(TAU * (yv * 1.0 + ph[li]))) + 0.010 * w1 + 0.003 * w2
    R = np.where(cath[li], Rc, Rs)
    rings = R * dens[li] + ph[li] * 7
    f = rings % 1.0
    ringid = np.floor(rings).astype(np.int64)
    rc = 0.55 + 0.45 * np.random.default_rng(seed + 9).random(4096)[(ringid + li * 131) % 4096]   # contraste de cada anel
    late_b = (smooth(0.55, 0.92, f) * (1 - smooth(0.96, 1.0, f))) * rc
    st = noise(N, 1.0, 70, seed + 4); st2 = noise(N, 2.5, 220, seed + 5)
    pr = smooth(1.9, 2.8, noise(N, 0.8, 9, seed + 6)) * (0.35 + 0.65 * late_b)
    low = fbm(N, 260, 600, 3, seed + 7)
    t = np.clip(late_b * contrast + streak * (0.08 * st + 0.10 * st2) + 0.12 * low, 0, 1)
    col = mix(L(early), L(late), t)
    tone = 1 + tone_var * r.standard_normal(leaves + 1)
    col = col * tone[li][..., None]
    if fleck > 0:   # raios medulares do carvalho: pequenas manchas claras atravessando a fibra
        fl = smooth(2.3, 3.0, noise(N, 5, 1.2, seed + 8)) * fleck
        col = mix(col, col * 1.18, fl)
    col *= (1 - pores * pr)[..., None]
    g = col.mean(-1, keepdims=True); col = g + (col - g) * sat
    seam = smooth(0, 1.5, np.minimum(lx, 1 - lx) * lw)
    col *= (0.93 + 0.07 * seam)[..., None]
    h = 0.04 * late_b - 0.08 * pr + 0.01 * st + 0.1 * seam
    rg = rough[0] + (rough[1] - rough[0]) * (0.6 * pr + 0.2 * late_b) + 0.02 * low
    save(name, lin2srgb(col), h, rg, 1.4, [size, size], label, note)


veneer('madeira_marcenaria', 1.2, '#cfae86', '#a8845d', 401, 'Carvalho', 'Lâmina natural, fibra vertical', leaves=6, ring_px=(7, 16),
       cathedral=0.35, contrast=0.55, streak=0.55, pores=0.35, fleck=0.35, rough=(0.42, 0.58), sat=0.9)
veneer('mesa_nogueira', 1.6, '#6f452c', '#4a2c1c', 402, 'Nogueira', 'Lâmina natural, verniz acetinado', leaves=4, ring_px=(16, 40),
       cathedral=0.7, contrast=0.5, streak=0.75, pores=0.35, rough=(0.3, 0.45))
veneer('mesa_freijo', 1.6, '#d2a877', '#a87a48', 403, 'Freijó claro', 'Madeira maciça, óleo natural', leaves=5, ring_px=(9, 22),
       cathedral=0.5, contrast=0.6, streak=0.6, pores=0.4, rough=(0.4, 0.55))

# ---------------------------------------------------------------- deck de cumaru: réguas com fibra, juntas e desgaste
if want('piso_deck'):
    N = 1024; size = 2.24; ppm = N / size; pw, pl = 0.14, 1.12
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    rows = int(round(size / pw)); per = int(round(size / pl)); r = np.random.default_rng(41)
    rowf = yy / N * rows; row = np.floor(rowf).astype(np.int32); stag = r.random(rows + 1)
    uf = (xx / N * per + stag[row]) % per; ci = np.floor(uf).astype(np.int32); pid = row * 8 + ci
    lu = (uf - ci) * pl; lv = (rowf - row) * pw
    st = noise(N, 90, 0.9, 42); st2 = noise(N, 260, 2.4, 43); low = fbm(N, 600, 120, 3, 44)
    tone = 1 + 0.12 * r.standard_normal(rows * 8 + 8); hue = 0.05 * r.standard_normal(rows * 8 + 8)
    base = mix(L('#8f5f42'), L('#5e3923'), np.clip(0.45 + 0.15 * st + 0.18 * st2 + 0.1 * low, 0, 1))
    base = base * tone[pid][..., None] * np.stack([1 + hue[pid], np.ones_like(lu), 1 - hue[pid]], -1)
    weather = smooth(0.2, 1.4, fbm(N, 200, 60, 3, 45)) * 0.18
    base = mix(base, L('#9a8a7a'), weather)
    d = np.minimum(np.minimum(lu, pl - lu), np.minimum(lv, pw - lv)) * 1000
    gap = smooth(2.5, 3.6, d); bev = smooth(2.5, 6.0, d)
    base *= (0.18 + 0.82 * gap)[..., None] * (0.88 + 0.12 * bev)[..., None]
    save('piso_deck', lin2srgb(base), 0.6 * gap + 0.3 * bev + 0.02 * st, 0.6 + 0.2 * (1 - gap) + 0.08 * weather, 2.6, [size, size],
         'Deck de cumaru', 'Régua 1,12 × 0,14 m, junta 6 mm')

# ---------------------------------------------------------------- trama de tecido (normal e rugosidade, cor neutra)
if want('tecido'):
    N = 512; k = 64     # 64 fios em 5 cm: ~0,8 mm por fio
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
    slx = fbm(N, 200, 3, 3, 151); sly = fbm(N, 3, 200, 3, 152)
    wx = 0.5 + 0.5 * np.cos(TAU * (xx * k + 0.05 * sly)); wy = 0.5 + 0.5 * np.cos(TAU * (yy * k + 0.05 * slx))
    over = ((np.floor(xx * k * 2) + np.floor(yy * k * 2)) % 2 == 0)
    weave = np.where(over, wx, wy); fib = noise(N, 0.7, None, 153)
    lum = 0.88 + 0.08 * (weave - 0.5) + 0.04 * np.where(over, sly, slx) + 0.02 * fib
    col = np.stack([lum, lum, lum], -1)
    save('tecido', col, weave * 0.9 + 0.12 * fib + 0.1 * np.where(over, sly, slx), 0.9 + 0.06 * fib, 2.2, [0.05, 0.05], 'Tecido', 'Trama de algodão')

json.dump(MAN, open(MANP, 'w'), ensure_ascii=False, indent=1)
