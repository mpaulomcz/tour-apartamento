import cv2, numpy as np, json
J=json.load(open('/tmp/claude-0/walls.json'))
W=J['walls']
# cleanup: merge tiny windows into walls, merge window fragments
def key(w): return (w['o'],round(w['c'],1))
out=[]
for w in sorted(W,key=lambda w:(w['o'],w['c'],w['a'])):
    if w['type']=='window' and w['b']-w['a']<15: w['type']='wall'
    if out and key(out[-1])==key(w) and out[-1]['type']==w['type'] and w['a']-out[-1]['b']<=10:
        out[-1]['b']=w['b']; continue
    out.append(w)
W=out
J['walls']=W
json.dump(J,open('/tmp/claude-0/walls.json','w'))
B=np.zeros((1114,1300),np.uint8)
for w in W:
    h=w['t']/2
    if w['o']=='h': cv2.rectangle(B,(w['a'],int(round(w['c']-h))),(w['b'],int(round(w['c']+h))),255,-1)
    else: cv2.rectangle(B,(int(round(w['c']-h)),w['a']),(int(round(w['c']+h)),w['b']),255,-1)
d=J['diag']; cv2.line(B,tuple(map(int,d['p0'])),tuple(map(int,d['p1'])),255,15)
cv2.imwrite('barrier.png',B)
seeds={
 'Varanda gourmet':(390,250),'Estar / Jantar / Cozinha':(700,300),'Área de serviço':(1140,300),
 'W.C. serviço':(1170,520),'Suíte 2':(1000,650),'W.C. suíte 2':(1150,660),'Vazio técnico':(1170,770),
 'Lavabo':(555,540),'W.C. social':(700,550),'Suíte 1':(360,600),'Suíte master':(370,850),
 'W.C. master':(650,930),'Varanda técnica':(175,600),'Varanda master':(120,900),
}
lab=np.zeros_like(B,np.int32); rooms=[]
for i,(name,(x,y)) in enumerate(seeds.items()):
    m=np.zeros((1116,1302),np.uint8); m[1:-1,1:-1]=B
    f=np.zeros_like(B)
    tmp=B.copy()
    cv2.floodFill(tmp,m,(x,y),128)
    reg=(tmp==128)
    area=int(reg.sum())
    touches=reg[0,:].any() or reg[-1,:].any() or reg[:,0].any() or reg[:,-1].any()
    cnts,_=cv2.findContours(reg.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(cnts,key=cv2.contourArea)
    poly=cv2.approxPolyDP(c,2.0,True)[:,0,:].tolist()
    rooms.append(dict(name=name,seed=[x,y],areaPx=area,leak=bool(touches),poly=poly))
    lab[reg]=i+1
    print(f"{name:28s} {area:7d}px  leak={touches}  verts={len(poly)}")
json.dump(rooms,open('/tmp/claude-0/rooms.json','w'))
base=cv2.imread('planta.png')[:,:,:3]
rng=np.random.RandomState(3); cols=rng.randint(60,255,(len(seeds)+1,3)); cols[0]=0
vis=base.copy(); m=lab>0
vis[m]=(base[m]*0.4+cols[lab[m]]*0.6).astype(np.uint8)
vis[B>0]=(0,0,0)
cv2.imwrite('rooms.png',vis)
