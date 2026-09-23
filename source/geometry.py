"""Small deterministic metre / Y-up mesh builder and embedded GLB writer."""
import json, math, struct
from pathlib import Path
import numpy as np

class Model:
    def __init__(self):
        self.parts={}; self.materials=[]; self.textures=[]
    def material(self,name,color,metal=0,rough=.6,alpha=1):
        m={'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[*color,alpha],'metallicFactor':metal,'roughnessFactor':rough}}
        if alpha<1:m['alphaMode']='BLEND'
        self.materials.append(m); return len(self.materials)-1
    def mesh(self,name,mat,vertices,faces,meta=None,uv=None):
        if name not in self.parts:self.parts[name]={'mat':mat,'v':[],'f':[],'uv':[],'meta':meta or {}}
        a=self.parts[name]; n=len(a['v'])
        a['v'].extend(np.asarray(vertices).tolist());a['f'].extend((np.asarray(faces)+n).tolist())
        a['uv'].extend(uv if uv is not None else [[0,0]]*len(vertices))
    def box(self,name,mat,x0,x1,y0,y1,z0,z1,meta=None):
        assert x1>x0 and y1>y0 and z1>z0,name
        v=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]]
        f=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]]
        self.mesh(name,mat,v,f,meta)
    def rod(self,name,mat,a,b,r=.1,n=10,r2=None,meta=None):
        a=np.array(a,float);b=np.array(b,float);d=b-a;d/=np.linalg.norm(d)
        u=np.cross(d,[0,1,0] if abs(d[1])<.9 else [1,0,0]);u/=np.linalg.norm(u);w=np.cross(d,u)
        v=[p+rr*(math.cos(t)*u+math.sin(t)*w) for p,rr in [(a,r),(b,r if r2 is None else r2)] for t in np.linspace(0,2*math.pi,n,endpoint=False)]
        v.extend([a,b]);f=[]
        for i in range(n):
            j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i],[2*n,j,i],[2*n+1,n+i,n+j]])
        self.mesh(name,mat,v,f,meta)
    def beam(self,name,mat,a,b,width,thick,meta=None):
        a=np.array(a,float);b=np.array(b,float);d=b-a;d/=np.linalg.norm(d)
        u=np.cross(d,[0,1,0] if abs(d[1])<.95 else [0,0,1]);u/=np.linalg.norm(u);w=np.cross(u,d)
        v=[p+sx*width/2*u+sy*thick/2*w for p in [a,b] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        self.mesh(name,mat,v,[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]],meta)
    def export(self,path):
        doc={'asset':{'version':'2.0','generator':'Gaoqi T4 evidence-based reconstruction r4','extras':{'units':'metres','vertical':'Y','accuracy':'Interpretive; see EVIDENCE.md'}},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':self.materials,'buffers':[{}],'bufferViews':[],'accessors':[]}
        binary=bytearray()
        def view(data):
            binary.extend(b'\0'*(-len(binary)%4));i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary.extend(data);return i
        def accessor(a,typ):
            i=len(doc['accessors']);doc['accessors'].append({'bufferView':view(a.astype('<f4').tobytes()),'componentType':5126,'count':len(a),'type':typ,'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()});return i
        if self.textures:
            doc['images']=[];doc['textures']=[];doc['samplers']=[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071},{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]
            for p in self.textures:
                doc['textures'].append({'source':len(doc['images']),'sampler':0 if not doc['images'] else 1});doc['images'].append({'bufferView':view(Path(p).read_bytes()),'mimeType':'image/png'})
        register=[];triangles=0
        for name,a in self.parts.items():
            v=np.array(a['v'],np.float32);f=np.array(a['f']);p=v[f].reshape(-1,3)
            normal=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);length=np.linalg.norm(normal,axis=1)
            if np.any(length<1e-8):raise ValueError('Degenerate triangles: '+name)
            normal=np.repeat(normal/length[:,None],3,axis=0)
            attrs={'POSITION':accessor(p,'VEC3'),'NORMAL':accessor(normal,'VEC3')}
            if 'baseColorTexture' in self.materials[a['mat']]['pbrMetallicRoughness']:attrs['TEXCOORD_0']=accessor(np.array(a['uv'])[f].reshape(-1,2),'VEC2')
            i=len(doc['nodes']);doc['scenes'][0]['nodes'].append(i);doc['nodes'].append({'name':name,'mesh':i,'extras':a['meta']})
            doc['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'material':a['mat']}]})
            register.append({'id':name,'min':v.min(axis=0).tolist(),'max':v.max(axis=0).tolist(),'triangles':len(f),**a['meta']});triangles+=len(f)
        binary.extend(b'\0'*(-len(binary)%4));doc['buffers'][0]['byteLength']=len(binary)
        js=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
        out=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
        Path(path).write_bytes(out)
        return {'nodes':len(register),'triangles':triangles,'bytes':len(out),'components':register}
