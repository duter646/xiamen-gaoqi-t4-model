"""Read exported GLB triangles; rasterise actual slices and floor support for circulation QA."""
from pathlib import Path
from collections import deque
import json, struct, hashlib, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'assets/xiamen-gaoqi-t4.glb').read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=20+jl+8
parts=[]
for node in doc['nodes']:
    prim=doc['meshes'][node['mesh']]['primitives'][0];acc=doc['accessors'][prim['attributes']['POSITION']];view=doc['bufferViews'][acc['bufferView']]
    v=np.frombuffer(raw,dtype='<f4',offset=binary+view.get('byteOffset',0)+acc.get('byteOffset',0),count=acc['count']*3).reshape(-1,3)
    assert np.isfinite(v).all(),node['name'];parts.append((node,v.reshape(-1,3,3)))
# Extract the walking surface from exported floor vertices, independently of source parameters.
concourse_tri=np.concatenate([t for n,t in parts if n['name'] in ['F2_concourse_slab','F2_connector_floor']])
concourse_vertices=concourse_tri.reshape(-1,3)
profile_knots=np.array([(z,float(concourse_vertices[np.abs(concourse_vertices[:,2]-z)<1e-5,1].max())) for z in np.unique(concourse_vertices[:,2])])
def actual_departure_y(z):return np.interp(z,profile_knots[:,0],profile_knots[:,1])
STEP=.25;X0=-45;Z0=-328;W=1640;H=1920
def pixel(x,z):return (int(round((x-X0)/STEP)),int(round((z-Z0)/STEP)))
def draw_polygon(d,pts,fill):d.polygon([pixel(x,z) for x,z in pts],fill=fill)
def slice_grid(level):
    support=Image.new('L',(W,H));sd=ImageDraw.Draw(support);obstacles=Image.new('L',(W,H));od=ImageDraw.Draw(obstacles)
    for node,tri in parts:
        m=node['extras']
        if level==8:
            tri=tri.copy();tri[:,:,1]-=actual_departure_y(tri[:,:,2])-8
        if m['layer'] in ['site','bridges']:continue
        lo=tri[:,:,1].min();hi=tri[:,:,1].max()
        if m['kind'] in ['floor','stair'] and abs(hi-level)<.035:
            for t in tri:
                if np.ptp(t[:,1])<.001 and abs(t[0,1]-level)<.035:draw_polygon(sd,t[:,[0,2]],255)
        for y in [level+.25,level+1,level+1.75]:
            if y<lo or y>hi:continue
            candidates=tri[(tri[:,:,1].min(axis=1)<=y)&(tri[:,:,1].max(axis=1)>=y)]
            for t in candidates:
                pts=[]
                for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
                    if (a[1]-y)*(b[1]-y)<=0 and abs(b[1]-a[1])>1e-7:
                        q=a+(b-a)*((y-a[1])/(b[1]-a[1]));pts.append(pixel(q[0],q[2]))
                if len(pts)>=2:od.line(pts[:2],fill=255,width=1)
    # 0.25 m lateral clearance from actual sliced solids and floor edges.
    support=support.filter(ImageFilter.MinFilter(3));obstacles=obstacles.filter(ImageFilter.MaxFilter(3))
    free=(np.array(support)>0)&(np.array(obstacles)==0)
    im=Image.fromarray(np.where(free,230,40).astype('uint8'));im.save(ROOT/f'tests/navigation-{level:g}.png')
    return free
def reachable(free,a,b,seal=None):
    mask=free.copy()
    if seal:
        im=Image.new('L',(W,H));
        for line in (seal if isinstance(seal[0][0],list) else [seal]):ImageDraw.Draw(im).line([pixel(*p) for p in line],fill=255,width=5)
        mask[np.array(im)>0]=False
    sx,sz=pixel(*a);tx,tz=pixel(*b)
    if not mask[sz,sx] or not mask[tz,tx]:return False
    q=deque([(sz,sx)]);mask[sz,sx]=False
    while q:
        z,x=q.popleft()
        if z==tz and x==tx:return True
        for dz,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            zz,xx=z+dz,x+dx
            if 0<=zz<H and 0<=xx<W and mask[zz,xx]:mask[zz,xx]=False;q.append((zz,xx))
    return False
grids={y:slice_grid(y) for y in [0,4,8]}
results={}
results['departure_public_to_gate']=reachable(grids[8],(43.4,100),(4,-310))
results['closing_security_blocks_bypass']=not reachable(grids[8],(43.4,100),(4,-310),json.loads((ROOT/'assets/departure-map-registration.json').read_text())['security_openings_xz'])
openings=json.loads((ROOT/'assets/departure-map-registration.json').read_text())['security_openings_xz']
results['west_security_independently_reaches_gate']=reachable(grids[8],(43.4,100),(4,-310),[openings[1]])
results['east_security_independently_reaches_gate']=reachable(grids[8],(43.4,100),(4,-310),[openings[0]])
results['arrival_mezzanine_continuous']=reachable(grids[4],(25,-310),(25,-5.5))
results['claim_to_arrival_exit']=reachable(grids[0],(48,45),(76,100))
results['closing_arrival_exit_blocks_reverse_bypass']=not reachable(grids[0],(48,45),(76,100),[(63,80),(77,80)])
routes=json.loads((ROOT/'assets/routes.json').read_text(encoding='utf-8'))['routes'];blocked=[]
for route in routes:
    for a,b in zip(route['points'],route['points'][1:]):
        if route['type']!='departure' and abs(a[1]-b[1])>.01:continue
        y=8 if route['type']=='departure' else round(a[1]);grid=grids.get(y)
        if grid is None:continue
        for t in np.linspace(0,1,max(2,int(math.dist(a,b)/.25))):
            q=np.array(a)*(1-t)+np.array(b)*t;x,z=q[0],q[2]
            # Report only terminal interior, excluding landside doorstep and bridge end.
            if z>112 or x< -21 or (z<0 and x>29):continue
            ix,iz=pixel(x,z)
            if not grid[iz,ix] or (route['type']=='departure' and abs(q[1]-.1-actual_departure_y(z))>.08):blocked.append({'route':route['id'],'point':q.round(2).tolist()});break
results['route_samples_clear']=not blocked
# Validate stair endpoints and landings against real horizontal triangles (including steps).
def support_height(x,z,target):
    found=[]
    for node,tri in parts:
        if node['extras']['kind'] not in ['floor','stair']:continue
        candidates=tri[(tri[:,:,0].min(axis=1)<=x+.001)&(tri[:,:,0].max(axis=1)>=x-.001)&(tri[:,:,2].min(axis=1)<=z+.001)&(tri[:,:,2].max(axis=1)>=z-.001)&(np.ptp(tri[:,:,1],axis=1)<.001)]
        for t in candidates:
            a,b,c=t[:,[0,2]];q=np.array([x,z]);cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
            signs=[cross(b-a,q-a),cross(c-b,q-b),cross(a-c,q-c)]
            if min(signs)>=-.001 or max(signs)<=.001:found.append(float(t[0,1]))
    return any(abs(y-target)<.21 for y in found)
results['arrival_stair_support']=all(support_height(4,-4+11*t,4*(1-t)) for t in np.linspace(0,1,80))
# R4 replaces the local stairs with long sloping branches. Test their actual triangles.
def surface_heights(tri,x,z):
    a=tri[:,0];u=tri[:,1]-a;v=tri[:,2]-a
    det=u[:,0]*v[:,2]-v[:,0]*u[:,2];valid=np.abs(det)>1e-8
    a=a[valid];u=u[valid];v=v[valid];det=det[valid]
    qx=x-a[:,0];qz=z-a[:,2]
    w1=(qx*v[:,2]-v[:,0]*qz)/det;w2=(u[:,0]*qz-qx*u[:,2])/det
    inside=(w1>=-1e-5)&(w2>=-1e-5)&(w1+w2<=1.00001)
    return (a[:,1]+w1*u[:,1]+w2*v[:,1])[inside]
bridge_specs=json.loads((ROOT/'assets/bridge-branches.json').read_text())
bridge_checks=[];head_checks=[]
for branch in bridge_specs:
    prefix='bridge_'+branch['gate']
    triangles=next(t for n,t in parts if n['name']==prefix+'_'+branch['branch']+'_ramp')
    obstacles=[t for n,t in parts if n['name'].startswith(prefix+'_') and n['extras']['kind'] in ['wall','roof','support']]
    for t in np.linspace(0,1,21):
        x,y,z=np.array(branch['start'])*(1-t)+np.array(branch['end'])*t
        bridge_checks.append(any(abs(h-y)<.015 for h in surface_heights(triangles,x,z)))
        head_checks.append(not any(any((hs>y+.2)&(hs<y+1.9)) for tri in obstacles if len(hs:=surface_heights(tri,x,z))))
results['bridge_sloping_branches_supported']=all(bridge_checks)
results['bridge_branch_headroom_samples']=all(head_checks)
results['obsolete_bridge_towers_removed']=not any('_departure_stairs' in n['name'] or '_connector_roof' in n['name'] for n,t in parts)
sky=next(t for n,t in parts if n['name']=='finger_roof_swept_skylight').reshape(-1,3)
ends=[sky[np.abs(sky[:,2]-z)<.01,0] for z in [-324,1]]
mid=sky[np.abs(sky[:,2]+161.5)<.01,0]
main_sky=next(t for n,t in parts if n['name']=='central_roof_skylight').reshape(-1,3)
results['main_roof_offcentre_spine']=main_sky[:,0].min()>190 and main_sky[:,0].max()<235
results['old_main_roof_meshes_removed']=not any(n['name'] in ['main_roof_-43','main_roof_168'] for n,t in parts)
results['skylight_taper_and_sweep']=bool(all(np.ptp(e)<1 for e in ends) and np.ptp(mid)>12 and ends[0].mean()< -23 and ends[1].mean()>30)
rise=json.loads((ROOT/'assets/departure-profile.json').read_text())
results['raised_concourse_height']=abs(actual_departure_y(rise['end_z'])-actual_departure_y(rise['start_z'])-rise['height'])<.001
ramp_samples=[]
for z in np.linspace(rise['end_z'],rise['start_z'],97):
    expected=rise['base']+rise['height']*(rise['start_z']-z)/(rise['start_z']-rise['end_z'])
    ramp_samples.append(any(abs(h-expected)<.01 for h in surface_heights(concourse_tri,-4+4.5*(rise['start_z']-z)/(rise['start_z']-rise['end_z']),z)))
results['entrance_ramp_continuous_support']=all(ramp_samples)
connector_tri=next(t for n,t in parts if n['name']=='F2_connector_floor')
results['connector_is_narrow_not_full_width']=np.ptp(connector_tri.reshape(-1,3)[:,0])<17
results['old_wide_root_floor_removed']=not any(abs(h-actual_departure_y(-10))<.02 for x in [-18,20] for h in surface_heights(concourse_tri,x,-10))
results['connector_links_both_landings']=reachable(grids[8],(-4,3),(.5,-26))
results['bridge_departure_matches_raised_floor']=all(abs(b['start'][1]-actual_departure_y(b['start'][2]))<.001 for b in bridge_specs if b['branch']=='departure')
results['arrival_floor_remains_independent']=support_height(25,-150,4)
site=json.loads((ROOT/'source/site.json').read_text(encoding='utf-8'))
results['arrival_outer_daylight_void']=all(not support_height(28,z,actual_departure_y(z)) and support_height(24,z,actual_departure_y(z)) and support_height(27,z,4) for z in [-290,-250,-210,-170,-130])
# Independent overall footprint comparison; OSM itself is an approximate map outline.
reference=Image.new('L',(W,H));rd=ImageDraw.Draw(reference);draw_polygon(rd,site['outline'],255)
footprint=Image.new('L',(W,H));fd=ImageDraw.Draw(footprint)
for node,tri in parts:
    if node['name'].startswith(('main_roof_','central_roof_skylight','finger_roof')) and node['extras']['kind']=='roof':
        for t in tri:draw_polygon(fd,t[:,[0,2]],255)
ref=np.array(reference)>0;built=np.array(footprint)>0
intersection=(ref&built).sum();union=(ref|built).sum();iou=float(intersection/union)
overlay=np.full((H,W,3),245,np.uint8);overlay[ref]=[53,149,190];overlay[built]=[226,164,60];overlay[ref&built]=[93,134,129]
Image.fromarray(overlay).save(ROOT/'tests/footprint-overlay.png')
results={k:bool(v) for k,v in results.items()}
report={'sha256':hashlib.sha256(raw).hexdigest(),'method':'GLB triangle horizontal slices at +0.25/+1/+1.75 m; floor triangles; 0.25 m grid with 0.25 m clearance; four-neighbour flood fill','checks':results,'blocked_route_samples':blocked,'limits':['Bridge aircraft shared-end switching not simulated or included in no-bypass proof','No full all-pairs mesh collision certification','Floor transitions limited to modelled arrival stair; hidden service and remote areas not reconstructed']}
report['departure_profile_from_GLB']=profile_knots.tolist()
report['departure_navigation_note']='Departure obstacles flattened relative to the actual exported floor profile before slicing; ramp support independently sampled in 3D.'
report['roof_OSM_footprint_IoU']=iou
report['footprint_note']='Green overlap, blue OSM only, ochre model only. Map alignment, not survey accuracy. Camera-matched photo residuals are not measured.'
(ROOT/'tests/geometry-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(results));print('blocked',blocked[:15])
if not all(results.values()):raise SystemExit(1)

