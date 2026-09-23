const {chromium}=require('C:/Users/39015/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
 const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:1200,height:900}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8767/?revision=5');await p.waitForFunction(()=>window.modelReady&&window.routesReady,null,{timeout:120000});
 for(const key of ['bridge','mezzanine','gallery','front','hallplan','hallsection']){
  await p.selectOption('#view',key,{force:true});await p.evaluate(()=>{document.getElementById('panel').hidden=true;document.getElementById('toggle').textContent='展开面板'});await p.waitForTimeout(250);await p.screenshot({path:path.join(__dirname,key+'-clean.png')});
 }
 const cameras=await p.evaluate(()=>({position:viewer.camera.position.toArray(),target:viewer.controls.target.toArray(),routeVisibility:Object.values(viewer.routeGroups).some(x=>x.visible)}));
 if(cameras.routeVisibility||errors.length)throw Error('Photo capture regression');
 await b.close();fs.writeFileSync(path.join(__dirname,'photo-validation.json'),JSON.stringify({sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'../assets/xiamen-gaoqi-t4.glb'))).digest('hex'),appSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'../app.js'))).digest('hex'),errors,cameras},null,2));console.log('Photo views passed');
})().catch(e=>{console.error(e);process.exit(1)});
