"""Build the revised T4 reconstruction. All uncertain dimensions remain editable."""
from pathlib import Path
import json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from geometry import Model

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'source/parameters.json').read_text(encoding='utf-8'))
SITE=json.loads((ROOT/'source/site.json').read_text(encoding='utf-8'))
M=Model();A=P['arrival_mezzanine'];D=P['departure_level'];U=P['upper_mezzanine']
from concourse_profile import elevation,apply as apply_concourse_profile
def departure_y(z):return float(elevation(P,z))
white=M.material('Ivory aluminium',[.83,.85,.82],.35)
silver=M.material('Standing seam roof',[.61,.67,.68],.65,.35)
steel=M.material('Pale steel',[.7,.76,.76],.5)
glass=M.material('Blue green curtain glass',[.19,.38,.43],.2,.22,.3)
floor=M.material('Warm terrazzo',[.71,.70,.65],.08,.38)
carpet=M.material('Departure carpet',[.40,.35,.26])
blue=M.material('Arrival blue carpet',[.06,.24,.34])
dark=M.material('Graphite metal',[.045,.07,.085],.3)
gold=M.material('Warm linear ceiling',[.55,.40,.22],.2)
wood=M.material('Arrival dark wood slats',[.17,.09,.045],0,.8)
facadeglass=M.material('External solar glass',[.06,.15,.19],.25,.24,.72)
violet=M.material('Purple seating',[.31,.20,.32])
green=M.material('Planting',[.16,.31,.19])
road=M.material('Road asphalt',[.17,.20,.22])
concrete=M.material('Apron concrete',[.56,.59,.58])
lime=M.material('Wayfinding green',[.34,.57,.06])
light=M.material('Lighting',[1,.92,.72]);M.materials[light]['emissiveFactor']=[.6,.5,.32]
orange=M.material('Baggage hall marine colour',[.9,.39,.09])

def meta(layer,kind='solid',evidence='P01/P02; photo estimate',certainty='inferred',**kw):
    return dict(layer=layer,kind=kind,evidence=evidence,certainty=certainty,**kw)
def box(name,mat,bounds,layer,kind='solid',**kw):M.box(name,mat,*bounds,meta(layer,kind,**kw))
def slab(name,mat,x0,x1,z0,z1,y,layer):box(name,mat,[x0,x1,y-.28,y,z0,z1],layer,'floor')
def rail(name,a,b,layer):
    a=np.array(a,float);b=np.array(b,float)
    for k,t in enumerate(np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/2.5)))):
        p=a*(1-t)+b*t;M.rod(name+'_post',steel,p,p+[0,1.15,0],.045,6,meta=meta(layer,'rail'))
    M.rod(name+'_hand',steel,a+[0,1.15,0],b+[0,1.15,0],.065,8,meta=meta(layer,'rail'))
def stairs(name,x,z0,z1,y0,y1,width,layer):
    n=max(3,math.ceil(abs(y1-y0)/.16))
    for i in range(n):
        za=z0+(z1-z0)*i/n;zb=z0+(z1-z0)*(i+1)/n
        ya=y0+(y1-y0)*i/n;yb=y0+(y1-y0)*(i+1)/n
        box(name+f'_step{i}',dark,[x-width/2,x+width/2,min(ya,yb)-.25,max(ya,yb),min(za,zb),max(za,zb)],layer,'stair')
    for s in [-1,1]:rail(name+f'_rail{s}',[x+s*width/2,y0,z0],[x+s*width/2,y1,z1],layer)
from main_roof_revision import height as roof_y
def finger_y(x,z):
    t=float(np.clip((z+324)/325,0,1));across=(x+26)/60
    tip=18.5+2*across
    centre=-25.75+59.5*t-2*math.sin(math.pi*t)
    return (1-t)*tip+t*roof_y(x,1)+2*math.sin(math.pi*t)-1.2*math.sin(math.pi*t)*math.exp(-((x-centre)/10)**2)


def sheet(name,mat,xs,zs,height,thickness,layer='roof'):
    v=[];f=[];nx=len(xs);nz=len(zs)
    for shift in [0,-thickness]:
        v.extend([[x,height(x,z)+shift,z] for z in zs for x in xs])
    for k in range(2):
        off=k*nx*nz
        for j in range(nz-1):
            for i in range(nx-1):
                a=off+j*nx+i;b=a+1;c=b+nx;d=a+nx
                f.extend([[a,c,b],[a,d,c]] if k==0 else [[a,b,c],[a,c,d]])
    edges=[(i,i+1) for i in range(nx-1)]+[((nz-1)*nx+i+1,(nz-1)*nx+i) for i in range(nx-1)]+[(j*nx,(j+1)*nx) for j in range(nz-1)]+[((j+1)*nx+nx-1,j*nx+nx-1) for j in range(nz-1)]
    off=nx*nz
    for a,b in edges:f.extend([[a,b,b+off],[a,b+off,a+off]])
    M.mesh(name,mat,v,f,meta(layer,'roof',evidence='C01/C07/C09; roof profile inferred'))

# Original labels embedded in GLB; reference photographs are not used as textures.
labels=['厦门高崎 T4','国内出发  DEPARTURES','国内到达  ARRIVALS','安全检查  SECURITY','K 岛  CHECK-IN','L 岛  CHECK-IN','行李提取  BAGGAGE','到达夹层  ARRIVALS','商业区  SHOPS','贵宾室  LOUNGE','中转服务  TRANSFER']+[f'{g}  登机口 GATE' for g in [61,62,63,65,66,67,68,69,70,71,72,73]]+[f'{i}  行李转盘' for i in range(21,26)]+['到达出口  EXIT']
atlas=Image.new('RGB',(1024,128*len(labels)),(15,32,42));draw=ImageDraw.Draw(atlas);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',43)
for i,t in enumerate(labels):draw.rectangle([0,i*128,13,i*128+127],fill=(146,190,35));draw.text((35,i*128+30),t,font=font,fill=(242,243,229))
atlas.save(ROOT/'assets/signs.png');M.textures.append(ROOT/'assets/signs.png');signmat=M.material('Bilingual signage',[1,1,1]);M.materials[signmat]['pbrMetallicRoughness']['baseColorTexture']={'index':0}
def sign(name,text,x,y,z,w,layer,base=None):
    i=labels.index(text);h=w/8
    box(name+'_case',dark,[x-w/2-.05,x+w/2+.05,y-h/2-.05,y+h/2+.05,z-.12,z],layer,'sign')
    uv=[[0,(i+1)/len(labels)],[1,(i+1)/len(labels)],[1,i/len(labels)],[0,i/len(labels)]]
    M.mesh(name+'_rear',signmat,[[x+w/2,y-h/2,z-.13],[x-w/2,y-h/2,z-.13],[x-w/2,y+h/2,z-.13],[x+w/2,y+h/2,z-.13]],[[0,1,2],[0,2,3]],meta(layer,'sign'),uv)
    M.mesh(name,signmat,[[x-w/2,y-h/2,z+.01],[x+w/2,y-h/2,z+.01],[x+w/2,y+h/2,z+.01],[x-w/2,y+h/2,z+.01]],[[0,1,2],[0,2,3]],meta(layer,'sign'),uv)
    if base is not None:
        for sx in [-w*.36,w*.36]:M.rod(name+'_support',steel,[x+sx,base,z-.06],[x+sx,y-h/2,z-.06],.075,8,meta=meta(layer,'support'))

# Site, arrival curb and elevated departure viaduct.
slab('site_apron',concrete,-135,450,-400,220,-.34,'site')
slab('arrival_road',road,-55,377,118,137,-.05,'site')
slab('departure_viaduct',road,-43,365,114,137,D,'site')
for x in range(-30,365,22):
    M.rod('viaduct_piers',concrete,[x,-.34,125],[x,D-.28,125],.7,12,meta=meta('site','support'))
    box('viaduct_lane',white,[x,x+8,D+.015,D+.035,126.9,127.1],'site','marking')
for z in [114.4,136.6]:rail('viaduct_guard'+str(z),[-43,D,z],[365,D,z],'site')
for x in [-43,365]:
    M.beam('viaduct_approach'+str(x),road,[x,0,205],[x,D-.2,137],15,.4,meta('site','floor',certainty='inferred'))
    for z in range(146,199,13):M.rod('approach_support'+str(x),concrete,[x,-.3,z],[x,D*(205-z)/68-.4,z],.65,10,meta=meta('site','support'))

# Main building floors. Arrival stair opening is excluded from the mezzanine slab.
slab('F1_main_slab',floor,-36,358,1,114,0,'1')
slab('F2_main_slab',floor,-36,358,1,114,D,'2')
slab('M_arrival_corridor',blue,20,30,-322,-7,A,'M')
slab('M_arrival_landing',blue,-2,30,-7,-4,A,'M')
slab('F2_concourse_slab',carpet,-22,26,-322,P['concourse_rise']['end_z'],D,'2')
slab('F2_connector_floor',carpet,*P['connector_x'],P['concourse_rise']['end_z'],P['concourse_rise']['start_z'],D,'2')
slab('F1_concourse_service_slab',concrete,-22,30,-322,1,0,'1')
# Separate lower arrival route with its own enclosed walls and stair to baggage hall.
box('M_arrival_end',white,[20,30,A,A+3.7,-322,-321.8],'M','wall')
stairs('M_to_F1_arrival_escalator',4,-4,7,A,0,3,'M')
box('arrival_stair_guard_left',glass,[1.9,2.1,0,6.1,-4,7],'M','wall')
box('arrival_stair_guard_right',glass,[5.9,6.1,0,6.1,-4,7],'M','wall')
sign('arrival_mezz_sign',labels[7],25,A+2.65,-38,6,'M')
for x in [23,27]:M.rod('arrival_sign_hangers',steel,[x,A+3,-38],[x,D-.45,-38],.025,6,meta=meta('M','support'))
sign('arrival_transfer',labels[10],14,A+2.1,-8,7,'M',A)
slab('M_transfer_alcove',blue,10,20,-20,-7,A,'M')
box('transfer_counter',white,[12,18,A,A+1.05,-10,-8],'M','fixture')
box('transfer_alcove_end',white,[9.9,10.1,A,A+3.7,-20,-7],'M','wall')
for zz in [-20]:box('transfer_alcove_side'+str(zz),white,[10,20,A,A+3.7,zz-.1,zz+.1],'M','wall')
for z in range(-314,-4,22):
    for x in [20,29]:M.rod('arrival_deck_columns',white,[x,0,z],[x,A-.28,z],.26,10,meta=meta('structure','support'))

# Facades with real doorway gaps; upper facade follows the roof.
arrival_doors=[(-24,13),(20,11),(76,9),(134,7),(146,5),(244,3),(328,1)]
departure_doors=[(-23,18),(-10,16),(42,14),(90,12),(106,10),(162,8),(200,6),(258,4),(322,2)]
def frontage(y0,y1,doors,layer):
    cursor=-36
    for x,num in doors:
        if x-2.2>cursor:box(f'{layer}_front_panel_{num}',glass,[cursor,x-2.2,y0,y1,113.85,114],layer,'wall')
        if y1>y0+3.1:box(f'{layer}_door_header_{num}',glass,[x-2.2,x+2.2,y0+3.1,y1,113.85,114],layer,'wall')
        for dx in [-2.3,2.3]:box(f'{layer}_door_jamb_{num}_{dx}',steel,[x+dx-.065,x+dx+.065,y0,y0+3.2,113.65,114.15],layer,'support')
        cursor=x+2.2
    box(layer+'_front_end',glass,[cursor,358,y0,y1,113.85,114],layer,'wall')
frontage(0,D-.28,arrival_doors,'1');frontage(D,15,departure_doors,'2')
for x in np.linspace(-36,358,80):
    y=roof_y(x,114)-.5
    M.rod('front_mullions',steel,[x,0,114],[x,y,119],.105,8,meta=meta('facade','support'))
for i,(x0,x1) in enumerate(zip(np.linspace(-36,358,80)[:-1],np.linspace(-36,358,80)[1:])):
    v=[[x0,15,114],[x1,15,114],[x1,roof_y(x1,114)-.5,119],[x0,roof_y(x0,114)-.5,119]]
    M.mesh('front_upper_glass',glass,v,[[0,1,2],[0,2,3]],meta('facade','wall'))
for x in [-36,358]:
    for za,zb in zip(np.linspace(1,114,25)[:-1],np.linspace(1,114,25)[1:]):
        M.mesh('end_glass'+str(x),glass,[[x,0,za],[x,0,zb],[x,roof_y(x,zb)-.5,zb],[x,roof_y(x,za)-.5,za]],[[0,1,2],[0,2,3]],meta('facade','wall'))
        M.rod('end_frames'+str(x),steel,[x,0,za],[x,roof_y(x,za)-.5,za],.1,8,meta=meta('facade','support'))
for xa,xb in [(-36,-22),(30,358)]:
    for x0,x1 in zip(np.linspace(xa,xb,max(2,int((xb-xa)/5)))[:-1],np.linspace(xa,xb,max(2,int((xb-xa)/5)))[1:]):
        M.mesh('airside_main_glass',glass,[[x0,0,1],[x1,0,1],[x1,roof_y(x1,1)-.5,1],[x0,roof_y(x0,1)-.5,1]],[[0,1,2],[0,2,3]],meta('facade','wall'))
        M.rod('airside_frames',steel,[x0,0,1],[x0,roof_y(x0,1)-.5,1],.1,8,meta=meta('facade','support'))

from main_roof_revision import build as build_main_roof
build_main_roof(globals())
for x in np.arange(-26,350,22):
    for z in [15,92]:
        top=roof_y(x,z)-1.2
        M.rod('hall_columns',white,[x,0,z],[x,top-1.4,z],.68,16,meta=meta('structure','support',evidence='N07/C22; spacing inferred'))
        M.rod('hall_column_heads',white,[x,top-1.4,z],[x,top,z],.68,16,r2=1.45,meta=meta('structure','support'))
    for za,zb in zip(np.linspace(1,114,20)[:-1],np.linspace(1,114,20)[1:]):M.beam('main_roof_ribs',steel,[x,roof_y(x,za)-.85,za],[x,roof_y(x,zb)-.85,zb],.35,.8,meta('roof','support'))
sign('terminal_name',labels[0],161,12.4,114.3,23,'facade',D)
# Thick eave fascia and repeated sheltered entrance canopies visible in C20/C21.
for z in [-7,130]:
    for x0,x1 in zip(np.linspace(-43,365,100)[:-1],np.linspace(-43,365,100)[1:]):
        M.mesh('main_eave_fascia_'+str(z),white,[[x0,roof_y(x0,z),z],[x1,roof_y(x1,z),z],[x1,roof_y(x1,z)-1.25,z],[x0,roof_y(x0,z)-1.25,z]],[[0,1,2],[0,2,3]],meta('roof','detail',evidence='C20/C21 deep metal eave'))
for x in np.arange(-29,355,15.5):
    vv=[[x-6,D+3.6,114],[x+6,D+3.6,114],[x+6,D+3.3,124],[x-6,D+3.3,124],[x,D+4.8,119]]
    M.mesh('entrance_saddle_canopies',white,vv,[[0,1,4],[1,2,4],[2,3,4],[3,0,4]],meta('facade','roof',evidence='C20 repeating small canopies'))
    M.rod('canopy_mast',steel,[x,D,123],[x,D+3.45,123],.10,8,meta=meta('facade','support'))
    M.rod('canopy_brace',steel,[x,D+3.45,123],[x,D+4.8,119],.06,8,meta=meta('facade','support'))

# Source-registered departure plan, replacing the r1 islands and full-height divider.
from departure_revision import build as build_departure
build_departure(globals())

# Five numbered claim belts; public/secure arrival boundary has controlled exit aperture.
for xa,xb in [(-36,64),(76,358)]:box('arrival_exit_partition'+str(xa),glass,[xa,xb,0,D-.3,79.9,80.1],'1','wall')
box('arrival_exit_header',white,[64,76,3,D-.3,79.9,80.1],'1','wall')
arrival_map=json.loads((ROOT/'source/arrival-finger-map.json').read_text(encoding='utf-8'))['arrival']
for belt in arrival_map['belts']:
    ident=belt['id'];cx,cz=belt['xz']
    box(f'belt_{ident}_base',silver,[cx-5,cx+5,0,.52,cz-11,cz+11],'1','fixture',evidence='P02 belts 21–25; dimensions inferred')
    box(f'belt_{ident}_surface',dark,[cx-4.7,cx+4.7,.52,.66,cz-10.7,cz+10.7],'1','fixture')
    box(f'belt_{ident}_island',silver,[cx-2.8,cx+2.8,.66,.85,cz-8,cz+8],'1','fixture')
    sign(f'belt_{ident}_label',f'{ident}  行李转盘',cx,2,cz+10.8,6,'1',.85)
    for z in [cz-6,cz,cz+6]:
        ring=[]
        for t in np.linspace(0,2*math.pi,41):ring.append([cx+3*math.cos(t),6.5,z+3*math.sin(t)])
        for a,b in zip(ring,ring[1:]):M.rod('arrival_ring_lights',light,a,b,.1,6,meta=meta('ceiling','fixture'))
        for dx in [-2,2]:M.rod('arrival_light_hangers',steel,[cx+dx,6.5,z],[cx+dx,D-.28,z],.035,6,meta=meta('ceiling','support'))
for x in range(65,300,5):box('arrival_feature_wall_'+str(x),orange if x%2 else blue,[x,x+5,0,6.4,15,15.2],'1','wall')
box('arrival_ceiling_panels',gold,[-36,358,D-.48,D-.38,1,114],'ceiling','ceiling')
for x in range(55,307,2):box('arrival_ceiling_slats',gold,[x,x+.09,D-.68,D-.48,15,77],'ceiling','ceiling')
box('arrival_mezz_ceiling',wood,[20,26,D-.47,D-.37,-322,-7],'ceiling','ceiling')
for z in np.arange(-321,-7,.38):box('arrival_mezz_ceiling_battens',wood,[20,26,D-.62,D-.47,z,z+.07],'ceiling','ceiling')
for z in range(-315,-10,8):box('arrival_mezz_lights',light,[20.8,24.8,D-.64,D-.61,z,z+.12],'ceiling','fixture')
sign('claim_sign',labels[6],48,3,35,15,'1',0)
sign('exit_sign',labels[-1],70,3.9,80.2,12,'1',3)

# West finger: departure above, independent arrival corridor below. Gate positions from G01.
# Facade tops follow the revised longitudinal roof, including the tall root bays.
def curtain_point(side,z,f):
    bottom=-22 if side<0 else 29.08
    top=-22 if side<0 else 33.22
    h=finger_y(top,z)-.12
    return [bottom+(top-bottom)*f,h*f,z]
for side,x in [(-1,-22),(1,30)]:
    gates=sorted([g for g in SITE['gates'] if (g['xz'][0]>0)==(side>0)],key=lambda g:g['xz'][1])
    cuts=[(-322,-322)]+[(g['xz'][1]-3,g['xz'][1]+3) for g in gates]+[(1,1)]
    for (a,b),(c,d) in zip(cuts,cuts[1:]):
        if c<=b:continue
        # Short segments retain the roof curvature instead of a horizontal 18 m cap.
        for za,zb in zip(np.linspace(b,c,max(2,int((c-b)/4)+1)),np.linspace(b,c,max(2,int((c-b)/4)+1))[1:]):
            M.mesh('finger_curtain_'+str(side),glass,[curtain_point(side,za,(A-.3)/curtain_point(side,za,1)[1]),curtain_point(side,zb,(A-.3)/curtain_point(side,zb,1)[1]),curtain_point(side,zb,1),curtain_point(side,za,1)],[[0,1,2],[0,2,3]],meta('facade','wall',evidence='R2 arrival photo and R3 aerial; heights inferred'))
    # The aerial shows an opaque service-storey plinth below the glazed public floors.
    # Split the actual wall into white panels and small glazed apertures, rather than cover it.
    for za in np.arange(-322,1,6):
        zb=min(1,za+6);wmid=(za+zb)/2;wl=max(za,wmid-.85);wr=min(zb,wmid+.85)
        def plinth_quad(name,mat,z0,z1,y0,y1):
            pts=[]
            for zz,yy in [(z0,y0),(z1,y0),(z1,y1),(z0,y1)]:pts.append(curtain_point(side,zz,yy/curtain_point(side,zz,1)[1]))
            M.mesh(name,mat,pts,[[0,1,2],[0,2,3]],meta('facade','wall',evidence='R4 white service plinth; aperture spacing inferred'))
        plinth_quad('finger_service_plinth',white,za,zb,0,1.25)
        plinth_quad('finger_service_plinth',white,za,zb,2.25,A-.3)
        plinth_quad('finger_service_plinth',white,za,wl,1.25,2.25)
        plinth_quad('finger_service_plinth',white,wr,zb,1.25,2.25)
        plinth_quad('finger_service_windows',glass,wl,wr,1.25,2.25)
    # Above the gate apertures the curtain remains continuous to the roof.
    for g in gates:
        za,zb=g['xz'][1]-3,g['xz'][1]+3
        ta,tb=curtain_point(side,za,1),curtain_point(side,zb,1)
        la=curtain_point(side,za,(departure_y(za)+3.2)/ta[1]);lb=curtain_point(side,zb,(departure_y(zb)+3.2)/tb[1])
        M.mesh('finger_gate_upper_glass',glass,[la,lb,tb,ta],[[0,1,2],[0,2,3]],meta('facade','wall'))
    for z in range(-320,1,8):
        pa,pb=curtain_point(side,z,0),curtain_point(side,z,1)
        M.beam('arrival_outer_I_web' if side>0 else 'finger_mullion',white,pa,pb,.24,.55,meta('facade','support'))
        if side>0:
            for dz in [-.25,.25]:M.beam('arrival_outer_I_flange',white,[pa[0],0,z+dz],[pb[0],pb[1],z+dz],.6,.09,meta('facade','support'))
    for fraction in np.linspace(.16,1,9):
        for za in range(-322,1,4):
            zb=min(1,za+4)
            M.beam('finger_curtain_transom',steel,curtain_point(side,za,fraction),curtain_point(side,zb,fraction),.10,.10,meta('facade','support'))
for xa,xb in zip(np.linspace(-22,33.22,20),np.linspace(-22,33.22,20)[1:]):
    M.mesh('finger_end_glass',glass,[[xa,A-.3,-322],[xb,A-.3,-322],[xb,finger_y(xb,-322)-.12,-322],[xa,finger_y(xa,-322)-.12,-322]],[[0,1,2],[0,2,3]],meta('facade','wall'))
box('finger_end_service_plinth',white,[-22,29.08,0,A-.3,-322,-321.85],'facade','wall')
from roof_revision import build as build_finger_roof
build_finger_roof(globals())
for z in range(-318,0,12):
    for x in [-13,21]:M.rod('finger_columns',white,[x,0,z],[x,finger_y(x,z)-.5,z],.32,10,meta=meta('structure','support'))
    M.beam('finger_roof_beams',steel,[-24,finger_y(-24,z)-.6,z],[32,finger_y(32,z)-.6,z],.22,.45,meta('roof','support'))
# P01: east-side waiting banks plus west-side service/shop clusters.
from finger_layout_revision import build as build_finger_layout
build_finger_layout(globals())

# R4 removes the short scissor tower: long separated branches extend towards the aircraft.
from bridges_revision import build as build_bridges
routes=build_bridges(globals())

# The arrival corridor's solid inner wall is cut at west-gate entries and transfer alcove.
spans=sorted([(g['xz'][1]-2,g['xz'][1]+2) for g in SITE['gates'] if g['xz'][0]<0]+[(-20,-7)])
cursor=-322
for za,zb in spans:
    if za>cursor:box('M_inner_wall_'+str(cursor),white,[19.85,20.05,A,D-.28,cursor,za],'M','wall',evidence='R2 photo: solid inner wall')
    cursor=zb
for g in SITE['gates']:
    if g['xz'][0]>0:continue
    gz=g['xz'][1]
    for zz in [gz-2,gz+2]:box(f'M_west_entry_wall_{g["ref"]}_{zz}',white,[-22,19.85,A,D-.28,zz-.08,zz+.08],'M','wall')
# Floor-edge fascia and guard are absent only at the real upper crossbridges.
cursor=-322
for za,zb in sorted([(g['xz'][1]-2,g['xz'][1]+2) for g in SITE['gates'] if g['xz'][0]>0])+[(P['concourse_rise']['end_z'],P['concourse_rise']['end_z'])]:
    if za>cursor:
        box('departure_edge_fascia_'+str(cursor),white,[25.85,26.05,D-.6,D,cursor,za],'2','wall')
        box('departure_void_guard_'+str(cursor),glass,[25.95,26.05,D,D+1.25,cursor,za],'2','rail')
        rail('departure_void_rail_'+str(cursor),[26,D,cursor],[26,D,za],'2')
    cursor=zb

from arrival_detail import build as build_arrival_details
build_arrival_details(globals())
from connector_revision import build as build_connector
build_connector(globals())
apply_concourse_profile(globals())
for part in M.parts.values():
    if part['mat']==glass and part['meta'].get('layer')=='facade':part['mat']=facadeglass
output=ROOT/'assets/xiamen-gaoqi-t4.glb';stats=M.export(output)
stats['sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
(ROOT/'assets/components.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'assets/routes.json').write_text(json.dumps({'routes':routes,'note':'Paths explain reconstruction; operational bridge selection is not simulated.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in stats.items() if k!='components'},indent=2))
