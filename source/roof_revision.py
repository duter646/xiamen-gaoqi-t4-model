"""Sweeping, tapered skylight between two roof fields, following annotated aerial R4."""
import numpy as np

def sky_edges(z):
    t=np.clip((z+324)/325,0,1)
    centre=-25.75+59.5*t-2*np.sin(np.pi*t)
    half=min(.12+8*np.sin(np.pi*t),centre+25.95,33.95-centre)
    return centre-half,centre+half

def build(c):
    M,meta,fy=[c[k] for k in ['M','meta','finger_y']]
    def skin(name,mat,field,thickness):
        zs=np.linspace(-324,1,131);count=9;vertices=[];faces=[]
        for drop in [0,-thickness]:
            for z in zs:
                left,right=sky_edges(z);xa,xb={'left':(-26,left),'glass':(left,right),'right':(right,34)}[field]
                for x in np.linspace(xa,xb,count):vertices.append([x,fy(x,z)+drop,z])
        size=count*len(zs)
        for k in range(2):
            for row in range(len(zs)-1):
                for col in range(count-1):
                    a=k*size+row*count+col;b=a+1;d=a+count;e=d+1
                    faces.extend([[a,e,b],[a,d,e]] if k==0 else [[a,b,e],[a,e,d]])
        boundary=list(range(count))+[r*count+count-1 for r in range(1,len(zs))]+list(range(size-2,size-count-1,-1))+[r*count for r in range(len(zs)-2,0,-1)]
        for a,b in zip(boundary,boundary[1:]+boundary[:1]):faces.extend([[a,b,b+size],[a,b+size,a+size]])
        M.mesh(name,mat,vertices,faces,meta('roof','roof',evidence='R4 annotated aerial: tapered diagonal skylight and triangular roof field; curvature inferred'))
    skin('finger_roof_left',c['silver'],'left',.30);skin('finger_roof_right',c['silver'],'right',.30);skin('finger_roof_swept_skylight',c['glass'],'glass',.1)
    for z in np.arange(-323,1,1.2):
        left,right=sky_edges(z)
        M.beam('finger_skylight_transverse_bars',c['white'],[left,fy(left,z)-.06,z],[right,fy(right,z)-.06,z],.1,.13,meta('roof','support'))
    for z in np.arange(-323,1,2):
        left,right=sky_edges(z)
        xs=np.linspace(right,34,10)
        for xa,xb in zip(xs,xs[1:]):M.rod('finger_broad_field_transverse_seams',c['white'],[xa,fy(xa,z)+.035,z],[xb,fy(xb,z)+.035,z],.035,5,meta=meta('roof','detail'))
    for side in [0,1]:
        for za in np.arange(-324,1,2.5):
            zb=min(1,za+2.5);xa=sky_edges(za)[side];xb=sky_edges(zb)[side]
            M.beam('finger_skylight_curved_border',c['white'],[xa,fy(xa,za)+.03,za],[xb,fy(xb,zb)+.03,zb],.22,.18,meta('roof','support'))
    # Eave depth and roof edge share the same source surface.
    for x in [-26,34]:
        for za in np.arange(-324,1,2.5):
            zb=min(1,za+2.5)
            M.mesh('finger_eave_fascia',c['white'],[[x,fy(x,za),za],[x,fy(x,zb),zb],[x,fy(x,zb)-.55,zb],[x,fy(x,za)-.55,za]],[[0,1,2],[0,2,3]],meta('roof','detail'))
