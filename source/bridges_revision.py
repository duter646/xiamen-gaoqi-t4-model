"""Long paired bridge branches reconstructed from the user's annotated aerial R4.
The observed exterior drives the envelope; branch widths, slopes and switching remain inferred.
"""
import json
import numpy as np

def build(c):
    M,ROOT,A,D,SITE=[c[k] for k in ['M','ROOT','A','D','SITE']]
    box,slab,meta,rail,sign=[c[k] for k in ['box','slab','meta','rail','sign']]
    white,steel,glass,floor,dark,blue=[c[k] for k in ['white','steel','glass','floor','dark','blue']]
    bridge_glass=M.material('Fixed bridge dark glazing',[.06,.15,.19],.2,.32,.70)
    routes=[];specs=[];original_parts=set(M.parts);baseD=D
    def wedge(name,mat,x0,x1,z0,z1,lo0,lo1,hi0,hi1,kind):
        v=[[x0,lo0,z0],[x1,lo1,z0],[x1,lo1,z1],[x0,lo0,z1],[x0,hi0,z0],[x1,hi1,z0],[x1,hi1,z1],[x0,hi0,z1]]
        f=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
        M.mesh(name,mat,v,f,meta('bridges',kind,evidence='R4 annotated aerial: long branches from departure and arrival mezzanine; dimensions inferred'))
    for gate in SITE['gates']:
        ref=gate['ref'];gx,gz=gate['xz'];s=1 if gx>0 else -1;x=30 if s>0 else -22
        pref='bridge_'+ref;D=c['departure_y'](gz)
        if s<0:slab('gate_'+ref+'_arrival_link',blue,x,20,gz-2,gz+2,A,'M')
        if s>0:
            slab('gate_'+ref+'_departure_crossbridge',floor,26,30,gz-2,gz+2,D,'2')
            for zz in [gz-2,gz+2]:
                box('gate_'+ref+'_crossbridge_glass'+str(zz),glass,[26,30,D,D+1.2,zz-.05,zz+.05],'2','rail')
                rail('gate_'+ref+'_crossbridge_rail'+str(zz),[26,D,zz],[30,D,zz],'2')
        start=x+s*3;end=x+s*37;tip=x+s*41;common=5.4
        # Short two-level threshold; most of the connection is the visible long branch.
        for label,y in [('departure',D),('arrival',A)]:
            slab(pref+'_'+label+'_threshold',floor,min(x,start),max(x,start),gz-3,gz+3,y,'bridges')
        for label,y,offset in [('departure',D,-1.55),('arrival',A,1.55)]:
            zc=gz+offset;za,zb=zc-1.35,zc+1.35
            wedge(pref+'_'+label+'_ramp',floor,start,end,za,zb,y-.24,common-.24,y,common,'floor')
            wedge(pref+'_'+label+'_roof',white,start,end,za-.12,zb+.12,y+2.82,common+2.82,y+3.0,common+3.0,'roof')
            for zz in [za,zb]:
                wedge(pref+'_'+label+'_glass_'+str(zz),bridge_glass,start,end,zz-.055,zz+.055,y+.18,common+.18,y+2.82,common+2.82,'wall')
                for lift in [.1,1.1,2.82]:M.beam(pref+'_'+label+'_long_rail',steel,[start,y+lift,zz],[end,common+lift,zz],.1,.12,meta('bridges','support'))
                for t in np.linspace(0,1,13):
                    xx=start+(end-start)*t;yy=y+(common-y)*t
                    M.beam(pref+'_'+label+'_mullion',white,[xx,yy+.18,zz],[xx,yy+2.82,zz],.09,.1,meta('bridges','support'))
            # A header encloses each threshold without putting a box around a stair tower.
            wedge(pref+'_'+label+'_threshold_roof',white,x,start,za-.12,zb+.12,y+2.82,y+2.82,y+3,y+3,'roof')
            for zz in [za,zb]:wedge(pref+'_'+label+'_threshold_glass',bridge_glass,x,start,zz-.05,zz+.05,y+.15,y+.15,y+2.82,y+2.82,'wall')
            specs.append({'gate':ref,'branch':label,'start':[start,y,zc],'end':[end,common,zc],'width':2.7})
        slab(pref+'_shared_head_floor',floor,min(end,tip),max(end,tip),gz-3,gz+3,common,'bridges')
        box(pref+'_shared_head_roof',white,[min(end,tip),max(end,tip),common+2.82,common+3,gz-3.1,gz+3.1],'bridges','roof')
        for zz in [gz-3,gz+3]:box(pref+'_shared_head_glass_'+str(zz),glass,[min(end,tip),max(end,tip),common,common+2.82,zz-.05,zz+.05],'bridges','wall')
        # The aircraft access is a short articulated glazed tube after the fixed twin branches.
        tube_end=x+s*56;z_end=gz+4.5
        M.beam(pref+'_tube_floor',steel,[tip,common-.15,gz],[tube_end,common-.15,z_end],3,.3,meta('bridges','floor'))
        M.beam(pref+'_tube_roof',white,[tip,common+2.75,gz],[tube_end,common+2.75,z_end],3.15,.2,meta('bridges','roof'))
        for dz in [-1.5,1.5]:
            M.beam(pref+'_tube_glass',glass,[tip,common+1.35,gz+dz],[tube_end,common+1.35,z_end+dz],.10,2.6,meta('bridges','wall'))
            for t in np.linspace(0,1,7):
                xx=tip+(tube_end-tip)*t;zz=gz+(z_end-gz)*t+dz
                M.beam(pref+'_tube_frames',white,[xx,common,zz],[xx,common+2.7,zz],.11,.11,meta('bridges','support'))
        # Fixed bridge piers and crossheads; outer mobile support has a paired wheel assembly.
        for distance in [16,35]:
            xx=x+s*distance;t=(distance-3)/34;support_y=min(D+(common-D)*t,A+(common-A)*t)-.25
            for dz in [-2.1,2.1]:M.rod(pref+'_fixed_pier',steel,[xx,0,gz+dz],[xx,support_y,gz+dz],.22,10,meta=meta('bridges','support'))
            M.beam(pref+'_pier_crosshead',steel,[xx,support_y-.1,gz-2.5],[xx,support_y-.1,gz+2.5],.45,.2,meta('bridges','support'))
            # Different-height branches have their own bearing posts from the common crosshead.
            for offset,y in [(-1.55,D),(1.55,A)]:
                yy=y+(common-y)*t-.24
                if yy>support_y+.02:M.rod(pref+'_branch_bearing',steel,[xx,support_y,gz+offset],[xx,yy,gz+offset],.16,8,meta=meta('bridges','support'))
        xx=tube_end-s*3;zz=z_end-.9
        for dz in [-1,1]:
            M.rod(pref+'_mobile_post',steel,[xx,.5,zz+dz],[xx,common-.3,zz+dz],.16,8,meta=meta('bridges','support'))
            M.rod(pref+'_wheel',dark,[xx-.22,.4,zz+dz],[xx+.22,.4,zz+dz],.4,12,meta=meta('bridges','fixture'))
        for i in range(7):
            ex=tube_end+s*i*.15
            for dz in [-1.55,1.55]:box(pref+'_bellows',dark,[ex-.05,ex+.05,common,common+2.9,z_end+dz-.06,z_end+dz+.06],'bridges','detail')
            box(pref+'_bellows_top',dark,[ex-.05,ex+.05,common+2.8,common+2.95,z_end-1.6,z_end+1.6],'bridges','detail')
        sign('gate_'+ref+'_sign',f'{ref}  登机口 GATE',x-s*5,D+2.5,gz+4,6,'2',D)
        routes.append({'id':'departure-'+ref,'type':'departure','gate':ref,'points':[[42,D+.1,124],[42,D+.1,100],[170,D+.1,100],[170,D+.1,56],[118,D+.1,56],[118,D+.1,24],[80,D+.1,19],[0,D+.1,19],[0,D+.1,6],[-4,baseD+.1,c['P']['concourse_rise']['start_z']],[.5,D+.1,c['P']['concourse_rise']['end_z']],[4,D+.1,c['P']['concourse_rise']['end_z']-2],[4,D+.1,gz],[x,D+.1,gz],[start,D+.1,gz-1.55],[end,common+.1,gz-1.55],[tip,common+.1,gz],[tube_end,common+.1,z_end]]})
        routes.append({'id':'arrival-'+ref,'type':'arrival','gate':ref,'points':[[tube_end,common+.1,z_end],[tip,common+.1,gz],[end,common+.1,gz+1.55],[start,A+.1,gz+1.55],[x,A+.1,gz],[25,A+.1,gz],[25,A+.1,-4.75],[4,A+.1,-4.75],[4,A+.1,-4],[4,.1,7],[4,.1,24],[48,.1,24],[48,.1,70],[70,.1,70],[70,.1,87],[76,.1,100],[76,.1,124]]})
    for name in set(M.parts)-original_parts:M.parts[name]['meta']['departure_profile_applied']=True
    for route in routes:
        if route['type']=='departure':
            for point in route['points']:
                if point[2]>=c['P']['concourse_rise']['start_z']:point[1]=baseD+.1
    (ROOT/'assets/bridge-branches.json').write_text(json.dumps(specs,indent=2))
    return routes
