"""Photo-observed arrival gallery: outer daylight void and inner solid wall."""
import math
import numpy as np
from PIL import Image

def build(c):
    M,ROOT,A,D=c['M'],c['ROOT'],c['A'],c['D'];box,meta,rail=c['box'],c['meta'],c['rail']
    white,steel,gold,green,light=[c[k] for k in ['white','steel','gold','green','light']]
    # Seamless mathematical wave textile. The photo is not pasted onto the model.
    size=512;y,x=np.mgrid[0:size,0:size];u=x/size;v=y/size
    band=np.floor((u+.075*np.sin(v*4*np.pi))*6).astype(int)%4
    colours=np.array([[38,48,67],[65,76,92],[108,115,112],[53,64,83]])
    arr=colours[band];rng=np.random.default_rng(40);arr=np.clip(arr+rng.integers(-6,7,(size,size,1)),0,255).astype('uint8')
    p=ROOT/'assets/arrival-wave-carpet.png';Image.fromarray(arr).save(p);M.textures.append(p)
    mat=c['blue'];M.materials[mat]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture={'index':len(M.textures)-1})
    for a in M.parts.values():
        if a['mat']==mat:a['uv']=[[v[0]/.9,v[2]/1.2] for v in a['v']]
    # Warm panels and photo-observed feature display outlines on the inner wall.
    olive=M.material('Arrival feature wall olive',[.36,.38,.13],0,.72)
    palette=[M.material('Display blue',[.20,.46,.64],0,.6),M.material('Display pink',[.67,.38,.57],0,.6),M.material('Display pale',[.56,.69,.70],0,.6)]
    for z0,z1 in [(-286,-263),(-222,-201),(-155,-134),(-56,-40)]:
        box('arrival_feature_back_'+str(z0),olive,[20.06,20.12,A,D-.63,z0,z1],'M','detail',evidence='R2 arrival photo; feature motif, approximate content')
        for j,z in enumerate(np.arange(z0+1.8,z1-1,2.1)):
            cy=A+1.85+(.42 if j%2 else 0);rz=1;ry=1.45
            verts=[[20.16,cy+ry*math.sin(t),z+rz*math.cos(t)] for t in np.linspace(0,2*math.pi,6,endpoint=False)]
            M.mesh('arrival_hex_display',palette[j%3],verts,[[0,i,i+1] for i in range(1,5)],meta('M','detail',evidence='R2 hexagonal wall display; graphics not replicated'))
            for a,b in zip(verts,verts[1:]+verts[:1]):M.rod('arrival_display_frames',white,a,b,.035,6,meta=meta('M','detail'))
    # Low guard and rectangular flower planters along the inclined outer curtain.
    for z in range(-307,-12,16):
        if any(abs(z-g['xz'][1])<5 for g in c['SITE']['gates'] if g['xz'][0]>0):continue
        box('arrival_planter_'+str(z),white,[28.9,29.8,A,A+.72,z-2,z+2],'M','fixture',evidence='R2 planters against curtain')
        box('arrival_plant_soil_'+str(z),gold,[29,29.7,A+.72,A+.76,z-1.9,z+1.9],'M','fixture')
        for dz in np.linspace(-1.65,1.65,8):
            M.rod('arrival_foliage',green,[29.35,A+.76,z+dz],[29.35,A+1.25,z+dz],.21,7,r2=.3,meta=meta('M','fixture'))
            M.rod('arrival_flowers',palette[1],[29.35,A+1.25,z+dz],[29.35,A+1.37,z+dz],.1,6,r2=.16,meta=meta('M','fixture'))
        rail('arrival_low_guard_'+str(z),[28.7,A,z-2.5],[28.7,A,z+2.5],'M')
