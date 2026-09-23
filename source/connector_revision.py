"""Narrow uphill connector located by R6, with R5 photographed interior."""
import numpy as np
from PIL import Image,ImageDraw

def build(c):
    M,ROOT,D,P=[c[k] for k in ['M','ROOT','D','P']];box,meta,rail=[c[k] for k in ['box','meta','rail']]
    w,g,s,light=[c[k] for k in ['white','glass','steel','light']];a,b=P['concourse_rise']['start_z'],P['concourse_rise']['end_z'];xl,xr=P['connector_x']
    ceiling=M.material('Connector pale grey acoustic panels',[.63,.65,.64],0,.9)
    red=M.material('Connector flowers',[.53,.045,.06],0,.8)
    for x in [xl,xr]:
        box('connector_glass_side_'+str(x),g,[x-.055,x+.055,D,D+4.25,b,a],'2','wall',evidence='R5 glass-sided short passage; R6 location')
        for z in np.linspace(b,a,5):M.beam('connector_frame_posts',w,[x,D,z],[x,D+4.25,z],.18,.2,meta('2','support'))
        for za,zb in zip(np.linspace(b,a,5),np.linspace(b,a,5)[1:]):
            M.beam('connector_diagonal_braces',w,[x,D+.15,za],[x,D+4.1,zb],.25,.28,meta('2','support',evidence='R5 white diagonals'))
            M.beam('connector_diagonal_braces',w,[x,D+4.1,za],[x,D+.15,zb],.25,.28,meta('2','support'))
        inside=x+.5 if x==xl else x-.5
        rail('connector_handrail_'+str(x),[inside,D,b],[inside,D,a],'2')
        for lift in [1.5,3.0]:M.beam('connector_window_transoms',s,[x,D+lift,b],[x,D+lift,a],.07,.09,meta('2','support'))
    box('connector_ceiling_skin',w,[xl-.18,xr+.18,D+4.25,D+4.45,b,a],'ceiling','ceiling',evidence='R5 low white connector ceiling')
    box('connector_ceiling_central_panel',ceiling,[xl+2,xr-2,D+4.05,D+4.25,b,a],'ceiling','ceiling')
    for z in np.arange(b,a,.55):box('connector_ceiling_louvres',w,[xl+2,xr-2,D+3.96,D+4.05,z,min(a,z+.055)],'ceiling','detail')
    for z in np.arange(b+2,a,4):
        for x in [xl+1,xr-1]:M.rod('connector_ceiling_downlights',light,[x,D+4.20,z],[x,D+4.24,z],.12,12,meta=meta('ceiling','fixture'))
    for x in [xl+.75,xr-.75]:
        for z in [b+5,a-6]:
            box('connector_planter',w,[x-.25,x+.25,D,D+.6,z-1.7,z+1.7],'2','fixture')
            for zz in np.arange(z-1.4,z+1.5,.35):
                M.rod('connector_foliage',c['green'],[x,D+.6,zz],[x,D+.85,zz],.18,6,meta=meta('2','fixture'))
                M.rod('connector_flowers',red,[x,D+.85,zz],[x,D+.96,zz],.13,6,meta=meta('2','fixture'))
    # Guard the new platform edges flanking the narrow neck.
    for x0,x1 in [(-22,xl+4.5),(xr+4.5,26)]:rail('concourse_root_edge_guard'+str(x0),[x0,D,b],[x1,D,b],'2')
    # Warm inclined ceiling immediately after the low connector, as seen through the opening.
    for za in np.arange(b-16,b,1):
        zb=za+1;ya=D+4.5+(b-za)*.10;yb=D+4.5+(b-zb)*.10
        M.beam('connector_transition_wood',c['gold'],[-22,ya,za],[26,ya,za],.97,.12,meta('ceiling','ceiling',evidence='R5 warm inclined ceiling beyond passage'))
    for x in [-13,21]:
        for z in [b-2,b-14]:
            M.rod('connector_transition_hanger',s,[x,c['departure_y'](z)+4.5+(b-z)*.1,z],[x,c['finger_y'](x,z)-.5,z],.05,6,meta=meta('ceiling','support'))
    # Procedural textile, with small muted red strokes instead of a plain brown slab.
    rng=np.random.default_rng(67);arr=np.clip(np.array([74,73,73])+rng.integers(-5,6,(256,256,1)),0,255).astype('uint8');im=Image.fromarray(arr);d=ImageDraw.Draw(im)
    for i in range(65):
        x,y=rng.integers(0,256,2);d.line([(int(x),int(y)),(int(x+7),int(y-10)),(int(x+13),int(y-7))],fill=(110,55,51),width=1)
    p=ROOT/'assets/departure-carpet.png';im.save(p);M.textures.append(p);material=c['carpet'];M.materials[material]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture={'index':len(M.textures)-1})
    for part in M.parts.values():
        if part['mat']==material:part['uv']=[[v[0]/2,v[2]/2] for v in part['v']]

    # The map neck shifts laterally between the commercial street and the wider finger.
    for name,part in M.parts.items():
        if name=='F2_connector_floor' or (name.startswith('connector_') and not name.startswith('connector_transition')):
            for v in part['v']:v[0]+=P['connector_end_offset']*float(np.clip((a-v[2])/(a-b),0,1))
