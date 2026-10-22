import cv2, numpy as np, json
im=cv2.imread('planta.png')[:,:,:3].astype(int)
mx=im.max(2); mn=im.min(2)
D=((mx<95)&((mx-mn)<40)).astype(np.uint8)
D=cv2.morphologyEx(D, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
Hh,Ww=D.shape
# approximate wall lines: (orientation, fixed, a0, a1, kind)
# kind: ext=exterior wall, int=interior, para=parapet (varanda edge), gl=glass-door line
LINES=[
 ('h', 79, 288,1258,'ext'),
 ('h', 466,135, 520,'int'),
 ('h', 464,505, 792,'int'),
 ('h', 604,505, 792,'int'),
 ('h', 493,858,1092,'int'),
 ('h', 734,212, 792,'int'),
 ('h', 864,528, 874,'int'),
 ('h', 988, 38, 872,'ext'),
 ('h', 806, 38, 218,'ext'),
 ('h', 184,1088,1252,'int'),
 ('h', 456,1088,1252,'int'),
 ('h', 576,1088,1252,'int'),
 ('h', 730,1088,1252,'int'),
 ('h', 801,866,1256,'ext'),
 ('v', 510, 79, 606,'gl'),
 ('v', 612,464, 606,'int'),
 ('v', 785,462, 740,'int'),
 ('v', 869,490, 990,'int'),
 ('v',1092,182, 803,'int'),
 ('v',1250, 79, 803,'ext'),
 ('v', 215,464, 990,'gl'),
 ('v', 140,462, 808,'ext'),
 ('v',  42,804, 990,'ext'),
 ('v', 534,864, 990,'int'),
]
def scan(o,f,a0,a1):
    best=None
    for c in range(f-7,f+8):
        if o=='h': s=D[c-3:c+4, a0:a1].sum()
        else: s=D[a0:a1, c-3:c+4].sum()
        if best is None or s>best[0]: best=(s,c)
    c=best[1]
    # thickness from row coverage
    rows=[]
    for k in range(c-9,c+10):
        cov=D[k,a0:a1].mean() if o=='h' else D[a0:a1,k].mean()
        rows.append((k,cov))
    mxcov=max(r[1] for r in rows)
    band=[k for k,cv in rows if cv>0.45*mxcov]
    # contiguous band around c
    lo=c; hi=c
    while lo-1 in band: lo-=1
    while hi+1 in band: hi+=1
    prof=[]
    for t in range(a0,a1):
        v=D[lo-1:hi+2,t] if o=='h' else D[t,lo-1:hi+2]
        prof.append(v.mean())
    prof=np.array(prof)
    lab=np.where(prof>0.62,2,np.where(prof>0.12,1,0))
    # median smooth
    k=5; pad=np.pad(lab,(k//2,k//2),mode='edge')
    lab=np.array([np.median(pad[i:i+k]) for i in range(len(lab))]).astype(int)
    runs=[]; s=0
    for i in range(1,len(lab)+1):
        if i==len(lab) or lab[i]!=lab[s]:
            runs.append([a0+s,a0+i,int(lab[s])]); s=i
    # merge tiny runs
    changed=True
    while changed:
        changed=False
        for i,r in enumerate(runs):
            if r[1]-r[0]<5 and len(runs)>1:
                j=i-1 if i>0 else i+1
                if i>0 and i<len(runs)-1 and (runs[i+1][1]-runs[i+1][0])>(runs[i-1][1]-runs[i-1][0]): j=i+1
                runs[j]=[min(runs[j][0],r[0]),max(runs[j][1],r[1]),runs[j][2]]
                runs.pop(i); changed=True; break
        # merge equal neighbours
        i=0
        while i<len(runs)-1:
            if runs[i][2]==runs[i+1][2]:
                runs[i]=[runs[i][0],runs[i+1][1],runs[i][2]]; runs.pop(i+1); changed=True
            else: i+=1
    return dict(o=o,c=(lo+hi+1)/2,lo=lo,hi=hi+1,runs=runs)
out=[]
for (o,f,a0,a1,kind) in LINES:
    r=scan(o,f,a0,a1); r['kind']=kind; out.append(r)
    print(o, f, '->', r['c'], 'thick', r['hi']-r['lo'], kind, [(a,b,['gap','thin','solid'][t]) for a,b,t in r['runs']])
json.dump(out,open('/tmp/claude-0/scan.json','w'))
base=cv2.imread('planta.png')[:,:,:3]
vis=(base*0.45+255*0.25).astype(np.uint8)
col={2:(0,0,220),1:(230,140,0),0:(0,200,0)}
for r in out:
    for a,b,t in r['runs']:
        if r['o']=='h': cv2.rectangle(vis,(a,r['lo']),(b,r['hi']),col[t],-1 if t else 1)
        else: cv2.rectangle(vis,(r['lo'],a),(r['hi'],b),col[t],-1 if t else 1)
cv2.imwrite('scan.png',vis)
