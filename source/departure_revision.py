"""Departure hall rebuilt from registered guide-map objects and checked photographs."""
import json
import numpy as np

def build(c):
    M,ROOT,D,U=c['M'],c['ROOT'],c['D'],c['U'];box,slab,meta,rail,sign,stairs=[c[k] for k in ['box','slab','meta','rail','sign','stairs']]
    white,glass,steel,dark,gold,floor,light=[c[k] for k in ['white','glass','steel','dark','gold','floor','light']]
    data=json.loads((ROOT/'source/departure_map.json').read_text(encoding='utf-8'))
    world=np.array([[*a['xz'],1] for a in data['anchors']]);uv=np.array([a['uv'] for a in data['anchors']]);affine=np.linalg.lstsq(world,uv,rcond=None)[0]
    objects={}
    for obj in data['objects']:
        xz=np.linalg.solve(affine[:2].T,(np.array(obj['uv'])-affine[2]).T).T
        objects[obj['id']]=xz
    register={'affine_xz_to_uv':affine.tolist(),'anchor_residual_px':(world@affine-uv).tolist(),'objects':{k:v.tolist() for k,v in objects.items()}}
    (ROOT/'assets/departure-map-registration.json').write_text(json.dumps(register,indent=2),encoding='utf-8')
    def triangulate(points):
        # Ear clipping preserves concave stepped/scalloped footprints.
        pts=np.asarray(points); ids=list(range(len(pts))); result=[]
        cross=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
        if sum(cross(pts[i],pts[(i+1)%len(pts)]) for i in ids)<0:ids.reverse()
        while len(ids)>3:
            for j,b in enumerate(ids):
                a,c0=ids[j-1],ids[(j+1)%len(ids)];A,B,C=pts[[a,b,c0]]
                if cross(B-A,C-B)<=1e-8:continue
                if any(min(cross(B-A,pts[k]-A),cross(C-B,pts[k]-B),cross(A-C,pts[k]-C))>=-1e-8 for k in ids if k not in [a,b,c0]):continue
                result.append([a,b,c0]);ids.pop(j);break
            else:raise ValueError('Invalid traced polygon')
        return result+[ids]
    def prism(name,points,y0,y1,material,kind='wall',category='commercial'):
        n=len(points);v=[[x,y,z] for y in [y0,y1] for x,z in points];f=[]
        for a,b,c0 in triangulate(points):f.extend([[a,c0,b],[n+a,n+b,n+c0]])
        for i in range(n):j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i]])
        M.mesh(name,material,v,f,meta('2',kind,evidence='P01 source-coordinate tracing',certainty='diagram-registered',plan_category=category))
    def beam(name,a,b,y0,y1,width,material=white,category='security'):
        a,b=np.array(a),np.array(b);v=b-a;n=np.array([-v[1],v[0]])/np.linalg.norm(v)*width/2
        prism(name,[a+n,b+n,b-n,a-n],y0,y1,material,category=category)
    # Check-in occupies the front of the adjacent K/L islands, not the outer scanner banks.
    for name in ['K_core','L_core']:
        prism('map_'+name,objects[name],D,U-.25,white,category='checkin')
        q=objects[name];a,b=q[3],q[2];axis=(b-a)/np.linalg.norm(b-a);normal=np.array([-axis[1],axis[0]])
        for i,t in enumerate(np.linspace(.05,.95,max(5,round(np.linalg.norm(b-a)/3.2)))):
            centre=a*(1-t)+b*t+normal*1.1
            pts=[centre+axis*u+normal*v for u,v in [(-1.15,-.6),(1.15,-.6),(1.15,.6),(-1.15,.6)]]
            prism(name+'_desk_'+str(i),pts,D,D+1.05,steel,'fixture','checkin')
            beam(name+'_screen_'+str(i),centre-axis*.9,centre+axis*.9,D+2,D+2.8,.15,dark,'checkin')
            M.rod(name+'_post',steel,[centre[0],D+1,centre[1]],[centre[0],D+2,centre[1]],.06,8,meta=meta('2','support',plan_category='checkin'))
        centre=(a+b)/2+normal*2;sign(name+'_sign',c['labels'][4 if name=='K_core' else 5],centre[0],D+3.5,centre[1],13,'2',D+2.8)
    for o in data['objects']:
        if o['type']=='commercial':
            prism('map_'+o['id'],objects[o['id']],D,U-.25,white,category='commercial')
            # Blue guide silhouettes locate service/commercial volumes; unseen shop partitions are omitted.
    # Two independent security banks flank the islands. Each belt follows the source bank's depth.
    openings=[]
    for name,count in [('security_west',12),('security_east',10)]:
        q=objects[name];a,b=(q[0]+q[3])/2,(q[1]+q[2])/2
        axis=(b-a)/np.linalg.norm(b-a);depth=((q[3]-q[0])+(q[2]-q[1]))/2
        for i,t in enumerate(np.linspace(.025,.975,count)):
            centre=a*(1-t)+b*t;front=centre+depth*.46;back=centre-depth*.46
            beam(name+'_belt_'+str(i),back,front,D+.35,D+.85,1.25,steel)
            beam(name+'_scanner_'+str(i),centre-depth*.10,centre+depth*.10,D+.85,D+1.7,1.5,dark)
            door=centre+axis*2
            for side in [-.55,.55]:beam(name+'_portal_'+str(i)+'_'+str(side),door+axis*side-depth*.015,door+axis*side+depth*.015,D,D+2.35,.14,steel)
            beam(name+'_portal_header_'+str(i),door-axis*.62,door+axis*.62,D+2.25,D+2.4,.24,steel)
        beam(name+'_header',a,b,D+3.1,U,.35,white)
        mid=(a+b)/2;sign(name+'_sign',c['labels'][3],mid[0],D+3.9,mid[1]+1,17,'2',D+3.1)
        openings.append([a.tolist(),b.tolist()])
    # Close gaps between traced banks and cores; the secure boundary intersects the solid cores.
    # These short joins are inferred, not evidence for the map's hidden interior partitions.
    west,east=openings
    for name,a,b in [('west_end',[-36,west[0][1]],west[0]),('west_core',west[1],[150,west[1][1]]),('east_core',[220,east[0][1]],east[0]),('east_end',east[1],[358,east[1][1]])]:
        beam('security_join_'+name,a,b,D,U,.3)
    register['security_openings_xz']=openings
    (ROOT/'assets/departure-map-registration.json').write_text(json.dumps(register,indent=2),encoding='utf-8')
    # Commercial frontage faces the uninterrupted airside spine; no invented west-only upper crosswalk.
    for o in data['objects']:
        if not o['id'].startswith('rear_shop'):continue
        q=objects[o['id']];front=q[np.argmax(q[:,1])];sign(o['id']+'_sign',c['labels'][8],front[0],D+2.6,front[1]+.15,7,'2',D+1.9)
    # Forecourt furnishings and columns preserve the open central hall shown in the map.
    for x in [48,113,178,243,308]:
        for z in [77,96]:
            M.rod('hall_planter',white,[x,D,z],[x,D+.7,z],2.1,24,meta=meta('2','fixture'))
            M.rod('hall_shrub',c['green'],[x,D+.7,z],[x,D+1.3,z],1.8,12,r2=1.3,meta=meta('2','fixture'))
            M.rod('hall_palm_trunk',gold,[x,D+.7,z],[x,D+6,z],.16,10,meta=meta('2','fixture'))
            for t in np.linspace(0,2*np.pi,12,endpoint=False):
                tip=[x+3*np.cos(t),D+5.4,z+3*np.sin(t)];M.beam('hall_palm_fronds',c['green'],[x,D+6,z],tip,.5,.045,meta('2','fixture'))
    for x in range(-25,350,8):
        for z in [65,86,106]:box('hall_floor_inlay',dark,[x,x+2,D+.005,D+.018,z,z+1.8],'2','marking')
    sign('departures_sign',c['labels'][1],80,D+3,108,15,'2',D)
