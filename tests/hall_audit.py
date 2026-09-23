"""Diagnostic plan overlay and real mesh section cuts; no claim of surveyed accuracy."""
exec((__import__('pathlib').Path(__file__).parent/'map_check.py').read_text(encoding='utf-8-sig'))
from PIL import ImageFont
canvas=Image.open(R/trace['source']).convert('RGBA').resize((1809,1376));layer=Image.new('RGBA',canvas.size);d=ImageDraw.Draw(layer)
parts=[]
for node in doc['nodes']:
 prim=doc['meshes'][node['mesh']]['primitives'][0];acc=doc['accessors'][prim['attributes']['POSITION']];view=doc['bufferViews'][acc['bufferView']]
 v=np.frombuffer(raw,dtype='<f4',offset=binary+view.get('byteOffset',0)+acc.get('byteOffset',0),count=acc['count']*3).reshape(-1,3);parts.append((node,v.reshape(-1,3,3)))
 if node['extras'].get('layer') not in ['2','U']:continue
 if node['extras'].get('kind') not in ['floor','wall','fixture']:continue
 if node['name'].startswith(('seat_','finger_')):continue
 for t in v.reshape(-1,3,3):
  if np.ptp(t[:,1])>.01:continue
  pts=np.column_stack([t[:,0],t[:,2],np.ones(3)])@aff
  col=(0,230,230,100) if node['extras']['kind']=='floor' else ((240,60,140,110) if node['extras']['kind']=='wall' else (250,190,20,130))
  d.line([tuple(p) for p in pts]+[tuple(pts[0])],fill=col,width=1)
reference_neck=[(725.3,913.7),(746.7,902),(800,946.3),(779.3,960.3)]
d.line(reference_neck+[reference_neck[0]],fill=(255,160,0,255),width=5)
canvas=Image.alpha_composite(canvas,layer).convert('RGB');canvas.save(R/'tests/departure-full-audit.png')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);im=Image.new('RGB',(1500,880),'white');draw=ImageDraw.Draw(im)
for row,zcut in enumerate([35,70]):
 ybase=360+row*410
 draw.text((35,ybase-310),f'实际 GLB 剖面 Z={zcut} m · 高度未由导览图验证',font=font,fill=(25,55,65))
 for node,tri in parts:
  if node['extras'].get('layer') in ['site','bridges']:continue
  candidates=tri[(tri[:,:,2].min(axis=1)<=zcut)&(tri[:,:,2].max(axis=1)>=zcut)]
  for t in candidates:
   points=[]
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
    if (a[2]-zcut)*(b[2]-zcut)<=0 and abs(b[2]-a[2])>1e-7:
     p=a+(b-a)*(zcut-a[2])/(b[2]-a[2]);points.append((40+(p[0]+45)*3.4,ybase-p[1]*7.3))
   if len(points)>=2:draw.line(points[:2],fill=(125,75,35) if node['extras'].get('layer') in ['roof','ceiling'] else (30,95,105),width=1)
 for y in [0,4,8,13]:draw.text((1380,ybase-y*7.3-12),f'+{y} m',font=font,fill=(80,80,80))
im.save(R/'tests/departure-sections.png')
report['strict_map_correspondence']=False
report['audit_findings']=[{'object':'check-in/security','status':'Guide Safety Check symbols reinterpreted: two banks flank K/L; check-in desks only on public core faces'},{'object':'commercial','status':'Rear scalloped shopping silhouettes and stepped end blocks traced; shop internals not resolved'},{'object':'projection','status':'Interactive compare.html uses actual before/after GLB triangles with fixed exterior-anchor affine registration'},{'object':'vertical section','status':'Illustrative map does not determine measured heights; roof and floor elevations remain inferred'},{'object':'remaining detail','status':'K/L internal service notches, exact desk counts and shop interiors require further detail; source silhouettes are not measured floor footprints'}]
(R/'tests/map-audit.json').write_text(json.dumps(report,indent=2));print('Full plan audit and two actual sections generated')
