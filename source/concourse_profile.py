"""Shared departure-floor profile and deformation at its exact break lines.
R5 confirms a gentle rise into the concourse; absolute dimensions are estimates.
"""
import numpy as np

def elevation(parameters,z):
    spec=parameters['concourse_rise'];t=np.clip((spec['start_z']-z)/(spec['start_z']-spec['end_z']),0,1)
    return parameters['departure_level']+spec['height']*t

def apply(c):
    M,P,A,D=[c[k] for k in ['M','P','A','D']];cuts=sorted([P['concourse_rise']['start_z'],P['concourse_rise']['end_z']])
    def clip(poly,z,keep_above):
        result=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            ina=(a[2]>=z-1e-8) if keep_above else (a[2]<=z+1e-8)
            inb=(b[2]>=z-1e-8) if keep_above else (b[2]<=z+1e-8)
            if ina:result.append(a)
            if ina!=inb:result.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
        return result
    def transform(part,mode):
        vertices=np.asarray(part['v'],float);uv=np.asarray(part['uv'],float)
        def lift(v):
            d=elevation(P,v[2])-D
            factor=1 if mode=='full' else (np.clip((v[1]-(A+3))/(D-.45-(A+3)),0,1) if mode=='hanger' else np.clip((v[1]-A)/(D-.7-A),0,1))
            out=v.copy();out[1]+=d*factor;return out
        if vertices[:,2].min()>=cuts[-1]:return
        if vertices[:,2].max()<=cuts[0]:part['v']=[lift(v).tolist() for v in vertices];return
        # A slab cannot use just its end vertices: split at both ramp ends before lifting.
        packed=np.column_stack([vertices,uv]);new_v=[];new_uv=[];new_f=[]
        for face in part['f']:
            for low,high in [(None,cuts[0]),(cuts[0],cuts[1]),(cuts[1],None)]:
                poly=[packed[i] for i in face]
                if low is not None:poly=clip(poly,low,True)
                if high is not None and poly:poly=clip(poly,high,False)
                for i in range(1,len(poly)-1):
                    tri=[poly[0],poly[i],poly[i+1]]
                    if np.linalg.norm(np.cross(tri[1][:3]-tri[0][:3],tri[2][:3]-tri[0][:3]))<1e-8:continue
                    base=len(new_v)
                    for v in tri:new_v.append(lift(v[:3]).tolist());new_uv.append(v[3:].tolist())
                    new_f.append([base,base+1,base+2])
        part.update(v=new_v,uv=new_uv,f=new_f)
    for name,part in M.parts.items():
        if part['meta'].get('departure_profile_applied'):continue
        if name.startswith('arrival_sign_hangers'):
            transform(part,'hanger')
        elif part['meta'].get('layer')=='2' or name.startswith(('arrival_mezz_ceiling','arrival_mezz_lights','connector_ceiling','connector_transition_wood')):
            transform(part,'full')
        elif name.startswith(('M_inner_wall_','M_west_entry_wall_','arrival_feature_back_')):
            transform(part,'wall_top')
    # Serialized independently, so QA can state the assumed profile alongside GLB measurements.
    import json
    (c['ROOT']/'assets/departure-profile.json').write_text(json.dumps({'base':D,**P['concourse_rise'],'gate_floor':float(elevation(P,cuts[0])),'note':'R5 confirms the rise; height and run are inferred.'},indent=2))
