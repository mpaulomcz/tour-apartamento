import cv2, numpy as np, json, math
exec(open('/tmp/claude-0/scan.py').read().split("out=[]")[0])  # reuse D, scan(), LINES
# fixes from inspection
LINES=[l for l in LINES if not (l[0]=='h' and l[1]==734)] + [('h',734,212,869,'int')]
PARA_V={42,140}            # vertical lines that are balcony parapets
walls=[]
def add(kind,o,c,a,b,th,line):
    walls.append(dict(type=kind,o=o,c=float(c),a=int(a),b=int(b),t=float(th),line=line))
for (o,f,a0,a1,lk) in LINES:
    r=scan(o,f,a0,a1); th=r['hi']-r['lo']
    for a,b,t in r['runs']:
        if b-a<6: continue
        if t==2:
            kind='wall'
            if o=='v' and f in PARA_V: kind='parapet'
            if o=='h' and f==988 and b<=230: kind='parapet'
            if o=='h' and f==806:
                # split at x=140: left part is balcony edge, right part separates var.tec
                if a<140: add('parapet',o,r['c'],a,140,th,lk); a=140
            add(kind,o,r['c'],a,b,th,lk)
        elif t==1:
            add('glassdoor' if lk=='gl' else 'window',o,r['c'],a,b,th,lk)
        else:
            if 40<=b-a<=90: add('door',o,r['c'],a,b,th,lk)
# fix: small balcony bottom window? keep as detected
# diagonal parapet (fitted): centre line
diag=dict(type='parapet',o='d',p0=[290.6,80.0],p1=[139.6,463.0],t=14.5)
json.dump(dict(walls=walls,diag=diag),open('/tmp/claude-0/walls.json','w'),indent=0)
for w in walls: print(w['type'],w['o'],round(w['c'],1),w['a'],w['b'],w['t'])
# ---- barrier mask for rooms
Hh,Ww=D.shape
B=np.zeros((Hh,Ww),np.uint8)
for w in walls:
    h=w['t']/2+1
    if w['o']=='h': cv2.rectangle(B,(w['a'],int(w['c']-h)),(w['b'],int(w['c']+h)),255,-1)
    else: cv2.rectangle(B,(int(w['c']-h),w['a']),(int(w['c']+h),w['b']),255,-1)
cv2.line(B,tuple(map(int,diag['p0'])),tuple(map(int,diag['p1'])),255,15)
np.save('/tmp/claude-0/B.npy',B)
