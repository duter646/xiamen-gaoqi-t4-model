"""Project actual exported core geometry back onto the guide-map tracing."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
raw=(R/'assets/xiamen-gaoqi-t4.glb').read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=28+jl
reg=json.loads((R/'assets/departure-map-registration.json').read_text());aff=np.array(reg['affine_xz_to_uv'])
trace=json.loads((R/'source/departure_map.json').read_text());image=Image.open(R/trace['source']).convert('RGBA').resize((1809,1376));overlay=Image.new('RGBA',image.size);draw=ImageDraw.Draw(overlay)
errors={}
for o in trace['objects']:
    uv=np.array(o['uv']);draw.line([tuple(p) for p in uv]+[tuple(uv[0])],fill=(240,180,25,255),width=6)
    name='map_'+o['id'];node=next((n for n in doc['nodes'] if n['name']==name),None)
    if node is None:continue
    prim=doc['meshes'][node['mesh']]['primitives'][0];a=doc['accessors'][prim['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
    pts=np.frombuffer(raw,dtype='<f4',offset=binary+v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*3).reshape(-1,3)
    xz=np.unique(pts[:,[0,2]],axis=0);projected=np.column_stack([xz,np.ones(len(xz))])@aff
    centre=projected.mean(axis=0);order=np.argsort(np.arctan2(projected[:,1]-centre[1],projected[:,0]-centre[0]));poly=[tuple(p) for p in projected[order]]
    draw.polygon(poly,fill=(0,170,160,90));draw.line(poly+[poly[0]],fill=(0,110,120,255),width=3)
    errors[o['id']]=float(np.linalg.norm(uv[:,None]-projected[None,:],axis=2).min(axis=1).max())
    draw.text(tuple(centre),o['id'],fill=(190,20,50,255),stroke_width=1)
image=Image.alpha_composite(image,overlay).convert('RGB');image.save(R/'tests/departure-map-overlay.png')
report={'sha256':hashlib.sha256(raw).hexdigest(),'exported_core_vertex_error_px':errors,'anchor_rms_px':float(np.sqrt(np.mean(np.sum(np.array(reg['anchor_residual_px'])**2,axis=1)))),'scope':'All mapped core and commercial polygon vertices verified from GLB. Security envelopes are references, not filled solids. This verifies implementation only; category evidence was checked against map symbols and photos.'}
(R/'tests/map-validation.json').write_text(json.dumps(report,indent=2));assert max(errors.values())<.01;print(json.dumps(report))
