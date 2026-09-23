from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import hashlib,json,urllib.request
R=Path('.')
for ref,model,out in [('references/revision2/arrival-photo.jpg','tests/mezzanine-clean.png','tests/arrival-comparison.jpg'),('references/revision2/annotated-bridge-roof.png','tests/bridge-clean.png','tests/bridge-roof-comparison.jpg'),('references/revision2/concourse-rise-reference.png','tests/gallery-clean.png','tests/concourse-rise-comparison.jpg')]:
 canvas=Image.new('RGB',(1600,640),'white');d=ImageDraw.Draw(canvas)
 for i,(p,label) in enumerate([(ref,'USER REFERENCE'),(model,'REVISED MODEL - APPROXIMATE CAMERA')]):
  im=ImageOps.contain(Image.open(R/p).convert('RGB'),(800,600));canvas.paste(im,(i*800+(800-im.width)//2,30+(600-im.height)//2));d.text((i*800+12,10),label,fill=(15,30,40))
 canvas.save(R/out,quality=92)
files=['index.html','app.js','style.css','compare.html','arrival-finger-compare.html','assets/arrival-finger-compare/report.json','assets/plan-compare/manifest.json','assets/xiamen-gaoqi-t4.glb','assets/routes.json','assets/components.json','assets/bridge-branches.json','assets/departure-profile.json','EVIDENCE.md','REPORT.md']
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));manifest={}
for name in files:
 body=(R/name).read_bytes();served=opener.open('http://127.0.0.1:8767/'+name+'?delivery=r5',timeout=20).read()
 manifest[name]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'http_matches_disk':body==served}
 assert body==served,name
sha=manifest['assets/xiamen-gaoqi-t4.glb']['sha256']
for name in ['geometry-validation.json','map-validation.json','viewer-validation.json','photo-validation.json','compare-validation.json']:assert json.loads((R/'tests'/name).read_text())['sha256']==sha,name
(R/'tests/delivery-manifest.json').write_text(json.dumps(manifest,indent=2));print('Final HTTP, geometry, map, viewer and photo hashes agree:',sha)
