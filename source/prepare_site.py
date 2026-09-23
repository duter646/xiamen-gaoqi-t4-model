import json, math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'references/osm-t4-way.json').read_text(encoding='utf-8'))['elements']
nodes = {n['id']: n for n in data if n['type']=='node'}
way = next(n for n in data if n['type']=='way')
lat, lon = 24.5465955, 118.1413890
theta = math.radians(38)
def coord(n):
    east=(n['lon']-lon)*111320*math.cos(math.radians(lat))
    north=(n['lat']-lat)*111320
    return [round(east*math.cos(theta)+north*math.sin(theta),3),round(east*math.sin(theta)-north*math.cos(theta),3)]
p=[coord(nodes[i]) for i in way['nodes']]
g=[{'ref':n['tags']['ref'],'xz':coord(n)} for n in nodes.values() if n.get('tags',{}).get('aeroway')=='gate']
(ROOT/'source/site.json').write_text(json.dumps({'origin':[lat,lon],'rotation_degrees':38,'outline':p,'gates':g},indent=2),encoding='utf-8')
im=Image.new('RGB',(1100,1000),'white'); d=ImageDraw.Draw(im)
def px(p): return (170+p[0]*1.8,740+p[1]*1.8)
d.polygon([px(v) for v in p],fill='#dee6e9',outline='#233844',width=2)
for i,v in enumerate(p):
    if i%3==0:d.text(px(v),str(i),fill='black')
for n in g:d.text(px(n['xz']),n['ref'],fill='red')
for x in range(-50,401,50):
    for z in range(-350,151,50):d.text(px([x,z]),f'{x},{z}',fill='#4488aa')
im.save(ROOT/'tests/osm-plan.png')
print(p)

