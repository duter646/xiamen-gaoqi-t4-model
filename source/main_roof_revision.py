"""Asymmetric paired roof shells constrained by C01/C20 front and C07/C21 side photographs."""
import numpy as np

def spine(z):
    t=np.clip((z+7)/137,0,1)
    return 205+17*t,11-4*t

def height(x,z):
    v=float(np.clip((z+7)/137,0,1));centre,_=spine(z)
    t=min(1.1,abs(x-centre)/((centre+43) if x<centre else (365-centre)))
    front=18.8+14*t*t;back=25+8*t*t+9*max(0,1-t)**3
    return float(front*v+back*(1-v)-1.2*np.sin(np.pi*v)*(1-min(t,1)))

def build(c):
    M,meta=c['M'],c['meta']
    def shell(name,material,field,drop,thick,layer):
        nx=32;nz=36;vertices=[];faces=[]
        for d in [drop,drop-thick]:
            for z in np.linspace(-7,130,nz):
                mid,width=spine(z);lo,hi={'left':(-43,mid-width/2),'glass':(mid-width/2,mid+width/2),'right':(mid+width/2,365)}[field]
                for x in np.linspace(lo,hi,nx):vertices.append([x,height(x,z)+d,z])
        size=nx*nz
        for side in [0,1]:
            for r in range(nz-1):
                for k in range(nx-1):
                    a=side*size+r*nx+k;b=a+1;d=a+nx;e=d+1
                    faces.extend([[a,e,b],[a,d,e]] if side==0 else [[a,b,e],[a,e,d]])
        boundary=list(range(nx))+[r*nx+nx-1 for r in range(1,nz)]+list(range(size-2,size-nx-1,-1))+[r*nx for r in range(nz-2,0,-1)]
        for a,b in zip(boundary,boundary[1:]+boundary[:1]):faces.extend([[a,b,b+size],[a,b+size,a+size]])
        M.mesh(name,material,vertices,faces,meta(layer,'roof' if layer=='roof' else 'ceiling',evidence='C01/C07/C20/C21; paired off-centre upswept shells; dimensions inferred'))
    for field in ['left','right']:
        shell('main_roof_'+field,c['silver'],field,0,.38,'roof')
        shell('hall_inner_ceiling_'+field,c['white'],field,-1.45,.08,'ceiling')
    shell('central_roof_skylight',c['glass'],'glass',-.16,.12,'roof')
    for field,count in [('left',70),('right',43)]:
        for fraction in np.linspace(0,1,count):
            points=[]
            for z in np.linspace(-7,130,37):
                mid,width=spine(z);lo,hi=(-43,mid-width/2) if field=='left' else (mid+width/2,365)
                x=lo+(hi-lo)*fraction;points.append([x,height(x,z)+.07,z])
            for a,b in zip(points,points[1:]):M.rod('roof_seams',c['white'],a,b,.065,5,meta=meta('roof','detail'))
    for side in [-1,1]:
        points=[]
        for z in np.linspace(-7,130,60):
            mid,width=spine(z);x=mid+side*width/2;points.append([x,height(x,z)+.18,z])
        for a,b in zip(points,points[1:]):M.beam('main_skylight_raised_border',c['white'],a,b,.4,.45,meta('roof','support'))
    for z in np.arange(-7,130,2.5):
        mid,width=spine(z);M.beam('main_skylight_bars',c['steel'],[mid-width/2,height(mid-width/2,z)-.05,z],[mid+width/2,height(mid+width/2,z)-.05,z],.12,.15,meta('roof','support'))
