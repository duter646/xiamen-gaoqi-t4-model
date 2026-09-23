"""P01 asymmetric waiting layout; module dimensions are explicitly inferred."""
import json
def build(c):
    M,D,box,meta,sign=[c[k] for k in ['M','D','box','meta','sign']]
    data=json.loads((c['ROOT']/'source/arrival-finger-map.json').read_text(encoding='utf-8'))['finger']
    gates=[g['xz'][1] for g in c['SITE']['gates']]
    for group in data['groups']:
        x0,x1,z0,z1=group['xz_bounds']
        # Interrupt the footprint wherever a real west gate has to cross it.
        cuts=sorted([z0,z1]+[max(z0,min(z1,z+d)) for z in gates for d in [-6,6] if z0<z<z1])
        for a,b in zip(cuts,cuts[1:]):
            if b-a<1 or any(abs((a+b)/2-z)<6 for z in gates):continue
            name='finger_service_'+group['id']+'_'+str(a)
            box(name+'_back',c['white'],[x0,x0+.2,D,D+3.2,a,b],'2','wall',evidence='P01 west service clusters; boundaries inferred')
            for z in [a,b-.2]:box(name+'_side',c['white'],[x0,x1,D,D+3.2,z,z+.2],'2','wall')
            box(name+'_ceiling',c['white'],[x0,x1,D+3.2,D+3.4,a,b],'2','wall')
            box(name+'_counter',c['gold'],[x1-2,x1,D,D+1,a+1,b-1],'2','fixture')
    for z in range(-313,-26,5):
        if any(abs(z-g)<6 for g in gates):continue
        for x in [12,16,21]:
            for k in range(3):
                xx=x+k*.75
                box('seat_cushions',c['violet'],[xx-.32,xx+.32,D+.4,D+.52,z-.4,z+.4],'2','fixture')
                box('seat_backs',c['violet'],[xx-.32,xx+.32,D+.52,D+1.1,z+.28,z+.4],'2','fixture')
                box('seat_legs',c['steel'],[xx-.17,xx+.17,D,D+.4,z-.2,z+.2],'2','fixture')
        # Short west banks only in gaps between service groups.
        if any(g['xz_bounds'][2]-3<=z<=g['xz_bounds'][3]+3 for g in data['groups']):continue
        for k in range(4):
            x=-18+k*.75
            box('seat_cushions',c['violet'],[x-.32,x+.32,D+.4,D+.52,z-.4,z+.4],'2','fixture')
            box('seat_backs',c['violet'],[x-.32,x+.32,D+.52,D+1.1,z+.28,z+.4],'2','fixture')
            box('seat_legs',c['steel'],[x-.17,x+.17,D,D+.4,z-.2,z+.2],'2','fixture')
