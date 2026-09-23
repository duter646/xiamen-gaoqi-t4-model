import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {GLTFLoader} from './vendor/GLTFLoader.js';

const scene=new THREE.Scene();scene.background=new THREE.Color('#e5e9e7');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));renderer.localClippingEnabled=true;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;document.body.appendChild(renderer.domElement);
let camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,.08,3000);let controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxDistance=1500;controls.target.set(100,5,-60);
scene.add(new THREE.HemisphereLight(0xeefaff,0x8e917d,1.4));const sun=new THREE.DirectionalLight(0xfff4db,2.0);sun.position.set(-180,300,160);scene.add(sun);const fill=new THREE.DirectionalLight(0xc5dded,1.2);fill.position.set(200,100,-300);scene.add(fill);scene.add(new THREE.AmbientLight(0xffffff,.65));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-420,right:420,top:450,bottom:-450,near:1,far:1100});sun.shadow.bias=-.00005;sun.shadow.normalBias=.14;sun.position.set(-180,400,170);sun.target.position.set(100,0,-65);scene.add(sun.target);
const ui=id=>document.getElementById(id);let model,routeData;const routeGroups={};
const views={overall:[[600,350,450],[110,4,-75]],front:[[165,38,680],[160,16,60]],airside:[[410,250,-490],[80,6,-95]],bridge:[[-175,110,-470],[0,13,-190]],west:[[-450,120,-110],[30,8,-85]],east:[[740,130,-70],[110,8,-70]],cutaway:[[510,350,360],[110,0,-65]],hall:[[282,10,84],[175,11,48]],security:[[110,10.5,62],[110,10.8,20]],gallery:[[-3.1,9.8,-4],[1,10.4,-34]],mezzanine:[[27.1,5.7,-67],[25.7,8.4,-36]],claim:[[48,2.1,72],[160,2.1,48]],section:[[110,13,-160],[4,8,-160]],hallplan:[[161,600,57],[161,8,57]],hallsection:[[210,95,350],[155,9,35]],plan:[[150,600,-70],[150,0,-70]]};
function setView(key){
  const [pos,target]=views[key];
  if(['plan','hallplan'].includes(key)){
    const half=key==='hallplan'?150:300,aspect=innerWidth/innerHeight;camera=new THREE.OrthographicCamera(-half*aspect,half*aspect,half,-half,.1,2000);camera.up.set(0,0,-1);
  }else camera=new THREE.PerspectiveCamera(key==='mezzanine'?64:40,innerWidth/innerHeight,.08,3000);
  controls.dispose();controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;camera.position.fromArray(pos);controls.target.fromArray(target);camera.lookAt(controls.target);
  if(['cutaway','section','plan','hallplan','hallsection'].includes(key))ui('roof').checked=false;
  if(key==='hallplan'){ui('floor').value='2';ui('facade').checked=false;ui('site').checked=false;}
  if(key==='hallsection'){ui('floor').value='all';ui('facade').checked=false;ui('site').checked=false;}
  if(key==='section'){ui('facade').checked=false;ui('site').checked=false;}
  if(['hall','security','gallery'].includes(key)){ui('floor').value='all';ui('roof').checked=true;ui('facade').checked=true;}
  if(key==='mezzanine'){ui('floor').value='all';ui('roof').checked=true;}
  if(key==='claim'){ui('floor').value='all';ui('roof').checked=true;}
  if(['overall','front','airside','bridge','west','east'].includes(key)){ui('floor').value='all';ui('roof').checked=true;ui('facade').checked=true;ui('site').checked=true;}
  updateVisibility();window.viewer.camera=camera;window.viewer.controls=controls;
}
const plane=new THREE.Plane(new THREE.Vector3(0,0,-1),-145);
function updateVisibility(){
 if(!model)return;const floor=ui('floor').value;const section=['section','hallsection'].includes(ui('view').value);plane.constant=ui('view').value==='hallsection'?60:-145;
 model.traverse(o=>{if(!o.isMesh)return;const d=o.userData,layer=d.layer;
   o.visible=(floor==='all'||!['1','2','M','U'].includes(layer)||layer===floor);
   if(layer==='roof'||layer==='ceiling')o.visible&&=ui('roof').checked&&floor==='all';
   if(layer==='facade')o.visible&&=ui('facade').checked;
   if(layer==='site')o.visible&&=ui('site').checked;
   if(['fixture','sign'].includes(d.kind))o.visible&&=ui('interior').checked;
   if(layer==='structure'&&floor!=='all')o.visible=false;
   if(layer==='bridges'&&floor!=='all')o.visible=false;
   o.material.clippingPlanes=section?[plane]:[];
 });updateRoutes();
}
function makeLine(points,color){const group=new THREE.Group();const m=new THREE.MeshBasicMaterial({color,depthTest:false,transparent:true,opacity:.9});
 for(let i=1;i<points.length;i++){const a=new THREE.Vector3(...points[i-1]),b=new THREE.Vector3(...points[i]),delta=b.clone().sub(a);const mesh=new THREE.Mesh(new THREE.CylinderGeometry(.28,.28,delta.length(),8),m);mesh.position.copy(a.clone().add(b).multiplyScalar(.5));mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());mesh.renderOrder=10;group.add(mesh);
 if(delta.lengthSq()>.1){const arrow=new THREE.ArrowHelper(delta,a.clone().lerp(b,.65),3,color,2,1);arrow.traverse(o=>{if(o.material){o.material.depthTest=false;o.renderOrder=11}});group.add(arrow);}}
 return group;
}
function updateRoutes(){for(const [id,g] of Object.entries(routeGroups))g.visible=id===`${id.startsWith('departure')?'departure':'arrival'}-${ui('gate').value}`&&ui(id.startsWith('departure')?'departure':'arrival').checked;}
window.viewer={scene,renderer,camera,controls,routeGroups,setView,updateVisibility};
try{
 const [gltf,routes]=await Promise.all([new GLTFLoader().loadAsync('./assets/xiamen-gaoqi-t4.glb?r=7'),fetch('./assets/routes.json?r=7').then(r=>{if(!r.ok)throw Error('动线加载失败');return r.json()})]);model=gltf.scene;model.traverse(o=>{if(o.isMesh){o.castShadow=!o.material.transparent;o.receiveShadow=o.userData.layer!=='roof';}});scene.add(model);routeData=routes;window.viewer.model=model;
 for(const gate of [...new Set(routes.routes.map(r=>r.gate))].sort((a,b)=>a-b)){const option=document.createElement('option');option.value=gate;option.textContent=`${gate} 号登机口`;ui('gate').appendChild(option)}
 for(const r of routes.routes){const group=makeLine(r.points,r.type==='departure'?0xd09b2d:0x098daf);routeGroups[r.id]=group;scene.add(group)}
 setView('overall');ui('loading').hidden=true;window.modelReady=true;window.routesReady=true;
}catch(error){ui('loading').textContent='模型加载失败：'+error.message;console.error(error);}
ui('view').addEventListener('change',()=>setView(ui('view').value));for(const id of ['floor','roof','facade','site','interior'])ui(id).addEventListener('change',updateVisibility);for(const id of ['departure','arrival','gate'])ui(id).addEventListener('change',updateRoutes);
ui('flow').onclick=()=>{ui('view').value='cutaway';ui('floor').value='all';ui('roof').checked=false;ui('facade').checked=false;ui('site').checked=false;ui('departure').checked=true;ui('arrival').checked=true;setView('cutaway');};
ui('toggle').onclick=()=>{const hidden=!ui('panel').hidden;ui('panel').hidden=hidden;ui('toggle').textContent=hidden?'展开面板':'收起面板';ui('toggle').setAttribute('aria-expanded',String(!hidden));};
addEventListener('resize',()=>{if(camera.isPerspectiveCamera)camera.aspect=innerWidth/innerHeight;else{camera.left=-300*innerWidth/innerHeight;camera.right=300*innerWidth/innerHeight}camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
const keys=new Set();addEventListener('keydown',e=>{if(!['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName))keys.add(e.code)});addEventListener('keyup',e=>keys.delete(e.code));addEventListener('blur',()=>keys.clear());
let last=performance.now();function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;const speed=(keys.has('ShiftLeft')?75:25)*dt;let f=camera.getWorldDirection(new THREE.Vector3());f.y=0;f.normalize();const right=new THREE.Vector3().crossVectors(f,new THREE.Vector3(0,1,0));const move=new THREE.Vector3();if(keys.has('KeyW'))move.add(f);if(keys.has('KeyS'))move.sub(f);if(keys.has('KeyD'))move.add(right);if(keys.has('KeyA'))move.sub(right);if(keys.has('KeyE'))move.y++;if(keys.has('KeyQ'))move.y--;move.multiplyScalar(speed);camera.position.add(move);controls.target.add(move);controls.update();renderer.render(scene,camera);requestAnimationFrame(frame)}requestAnimationFrame(frame);
