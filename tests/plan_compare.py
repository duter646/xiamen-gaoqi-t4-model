"""Rasterise actual old/new GLB triangles into the SAME guide and overhead frames."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1]; OUT=R/'assets/plan-compare';OUT.mkdir(exist_ok=True)
reg=json.loads((R/'assets/departure-map-registration.json').read_text());aff=np.array(reg['affine_xz_to_uv'])
colors={'checkin':(220,55,140),'security':(231,117,15),'commercial':(0,147,158),'other':(114,94,155)}
source=Image.open(R/'references/t4-2f-map.jpg').convert('RGB').resize((1809,1376))
crop=(730,550,1640,1170);scale=4;size=(1640,540)
# Output pixel -> world XZ -> source UV. Fixed exterior anchors for BOTH revisions.
T=np.array([[1/scale,0],[0,1/scale],[-45,-5]])
coeff=T[:2]@aff[:2];offset=T[2]@aff[:2]+aff[2]
source.transform(size,Image.Transform.AFFINE,(coeff[0,0],coeff[1,0],offset[0],coeff[0,1],coeff[1,1],offset[1]),Image.Resampling.BICUBIC).save(OUT/'top-map.png')
source.crop(crop).save(OUT/'guide-map.png')
def category(node):
    name=node['name'];m=node['extras']
    if 'plan_category' in m:return m['plan_category']
    if name.startswith(('K_bank','L_bank','K_core','L_core','map_K','map_L','checkin_round')):return 'checkin'
    if name.startswith(('security','rear_service_boundary')):return 'security'
    if name.startswith(('commercial','map_west','map_east','shopping')):return 'commercial'
    return 'other'
manifest={'affine_xz_to_uv':aff.tolist(),'anchor_rms_px':float(np.sqrt(np.mean(np.sum(np.array(reg['anchor_residual_px'])**2,axis=1)))),'limits':['Exterior-anchor affine registration held fixed between revisions','Guide is illustrative axonometric; top silhouettes are not surveyed footprints','Triangulated GLB floor projections, not hand-redrawn model outlines','Projection deliberately removes height displacement; vertical section needs photographs'],'revisions':{}}
for rev,path in [('before',R/'archive/r4-layout/xiamen-gaoqi-t4.glb'),('after',R/'assets/xiamen-gaoqi-t4.glb')]:
    raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=28+jl
    masks={frame:{cat:Image.new('L',(1809,1376) if frame=='guide' else size) for cat in colors} for frame in ['guide','top']}
    draws={f:{c:ImageDraw.Draw(im) for c,im in mm.items()} for f,mm in masks.items()};counts={c:0 for c in colors}
    for node in doc['nodes']:
        m=node['extras']
        if m.get('layer') not in ['2','U'] or m.get('kind') not in ['wall','fixture','support','detail']:continue
        prim=doc['meshes'][node['mesh']]['primitives'][0];a=doc['accessors'][prim['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
        pts=np.frombuffer(raw,dtype='<f4',offset=binary+v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*3).reshape(-1,3,3)
        cat=category(node);counts[cat]+=1
        for tri in pts:
            if tri[:,2].max()<0 or tri[:,2].min()>114:continue
            xz=tri[:,[0,2]];edge=xz[1:]-xz[0]
            if abs(np.linalg.det(edge))<1e-5:continue
            uv=xz@aff[:2]+aff[2];top=(xz-np.array([-45,-5]))*scale
            for frame,p in [('guide',uv),('top',top)]:draws[frame][cat].polygon([tuple(q) for q in p],fill=255)
    for frame,mm in masks.items():
        combined=Image.new('RGBA',next(iter(mm.values())).size)
        for cat,mask in mm.items():
            # Silhouette boundary of the actual mesh union; no triangle-wire clutter.
            edge=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)),mask.filter(ImageFilter.MinFilter(3)))
            alpha=mask.point(lambda p:int(p*.42));alpha=ImageChops.lighter(alpha,edge)
            layer=Image.new('RGBA',mask.size,colors[cat]+(0,));layer.putalpha(alpha)
            combined=Image.alpha_composite(combined,layer)
            if frame=='guide':layer=layer.crop(crop)
            layer.save(OUT/f'{frame}-{rev}-{cat}.png')
        if frame=='guide':combined=combined.crop(crop)
        base=Image.open(OUT/f'{frame}-map.png').convert('RGBA');Image.alpha_composite(base,combined).convert('RGB').save(OUT/f'{frame}-{rev}-overlay.jpg',quality=94)
    manifest['revisions'][rev]={'sha256':hashlib.sha256(raw).hexdigest(),'mesh_counts':counts}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['revisions']))
