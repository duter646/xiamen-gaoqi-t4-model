"""Read each exported GLB, and project the two audited floor areas onto source maps."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1];out=R/'assets/arrival-finger-compare';out.mkdir(exist_ok=True)
spec=json.loads((R/'source/arrival-finger-map.json').read_text(encoding='utf-8'));report={}
for area,d in spec.items():
 aff=np.array(d['affine']);base=Image.open(R/d['source']).resize((1809,1376)).convert('RGBA');base.crop(d['crop']).save(out/f'{area}-map.png')
 report[area]={'anchor_rms_px':d['rms_px'],'limits':'Illustrative guide, independent exterior anchors; height removed. Internal walls, modules and dimensions are not surveyed.','versions':{}}
 for rev,p in [('before',R/'archive/r5-layout/xiamen-gaoqi-t4.glb'),('after',R/'assets/xiamen-gaoqi-t4.glb')]:
  raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=28+jl
  masks=[Image.new('L',base.size) for i in range(3)];draws=[ImageDraw.Draw(m) for m in masks];count=[0,0,0];centres={}
  for node in doc['nodes']:
   m=node['extras'];name=node['name']
   if m.get('layer')!=d['layer'] or m.get('kind') not in ['wall','fixture','rail','support']:continue
   a=doc['accessors'][doc['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
   pts=np.frombuffer(raw,dtype='<f4',offset=binary+v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*3).reshape(-1,3,3)
   if area=='finger' and pts[:,:,2].min()>-23:continue
   if area=='arrival' and name.startswith('belt_') and name.endswith('_base'):centres[name]=((pts.min(axis=(0,1))+pts.max(axis=(0,1)))/2)[[0,2]].tolist()
   cat=0 if name.startswith(('belt_','seat_')) else 1 if name.startswith(('arrival_exit','arrival_feature','finger_service')) else 2
   count[cat]+=1
   for t in pts:
    if area=='finger' and t[:,2].max()>-23:continue
    xz=t[:,[0,2]]
    if abs(np.linalg.det(xz[1:]-xz[0]))<1e-6:continue
    draws[cat].polygon([tuple(q) for q in xz@aff[:2]+aff[2]],fill=255)
  combined=Image.new('RGBA',base.size)
  for cat,color in enumerate([(220,55,140),(0,147,158),(225,140,20)]):
   m=masks[cat];edge=ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m.filter(ImageFilter.MinFilter(3)));alpha=ImageChops.lighter(m.point(lambda x:round(x*.5)),edge)
   layer=Image.new('RGBA',base.size,color+(0,));layer.putalpha(alpha);combined=Image.alpha_composite(combined,layer)
  combined.crop(d['crop']).save(out/f'{area}-{rev}.png');Image.alpha_composite(base,combined).crop(d['crop']).convert('RGB').save(out/f'{area}-{rev}-overlay.jpg',quality=94)
  report[area]['versions'][rev]={'sha256':hashlib.sha256(raw).hexdigest(),'category_mesh_count':count,'belt_centres_xz':centres}
report['findings']=['P02 belts 21–25 were spaced 46 m apart; guide-registered centres have roughly 20–23 m spacing. Belts shortened from 33 m to 22 m; widths and end shape remain inferred.','P01 west service/shop clusters were missing; add four groups and retain clear gate apertures. Waiting banks concentrated east, with short west banks between services.','Gate order 61/63/65/67/69/71/72 east and 62/66/68/70/73 west agrees with P01; OSM longitudinal coordinates retained, not claimed metrically verified.','Arrival controlled exit and mezzanine links pass mesh navigation; detailed arrival end service volumes and map 25-adjacent unnumbered U-shape remain unresolved and have not been guessed as a sixth belt.']
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Arrival/finger before-after actual mesh projections generated')
