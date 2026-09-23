const {chromium}=require('C:/Users/39015/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1500,height:980}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8767/');await page.waitForFunction(()=>window.modelReady&&window.routesReady,null,{timeout:120000});
 for(const key of ['overall','front','airside','bridge','west','east','cutaway','hall','hallplan','hallsection','security','gallery','mezzanine','claim','section']){
   await page.selectOption('#view',key);await page.waitForTimeout(250);await page.screenshot({path:path.join(__dirname,key+'.png')});
 }
 for(const floor of ['1','M','2','U']){await page.selectOption('#view','plan');await page.selectOption('#floor',floor);await page.uncheck('#facade');await page.uncheck('#site');await page.waitForTimeout(100);await page.screenshot({path:path.join(__dirname,'plan-'+floor+'.png')})}
 await page.click('#flow');await page.waitForTimeout(200);await page.screenshot({path:path.join(__dirname,'flows.png')});
 const enabled=await page.evaluate(()=>Object.values(viewer.routeGroups).filter(g=>g.visible).length);if(enabled!==2)throw Error('Expected both routes');
 await page.selectOption('#gate','73');const visible=await page.evaluate(()=>Object.entries(viewer.routeGroups).filter(([id,g])=>g.visible).map(([id])=>id));if(!visible.every(id=>id.endsWith('-73')))throw Error('Gate selector failed');
 const res=await page.request.get('http://127.0.0.1:8767/assets/xiamen-gaoqi-t4.glb');const served=await res.body();if(!res.ok()||served.subarray(0,4).toString()!=='glTF'||!served.equals(fs.readFileSync(path.join(__dirname,'../assets/xiamen-gaoqi-t4.glb'))))throw Error('Download mismatch');const sha256=crypto.createHash('sha256').update(served).digest('hex');
 await page.selectOption('#view','overall');await page.click('#toggle');await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(__dirname,'mobile.png')});if(!await page.locator('#panel').isHidden())throw Error('Panel toggle failed');if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
 await page.evaluate(()=>{for(const id of ['departure','arrival']){const input=document.getElementById(id);input.checked=false;input.dispatchEvent(new Event('change',{bubbles:true}));}});await page.setViewportSize({width:1200,height:900});await page.selectOption('#view','bridge',{force:true});await page.waitForTimeout(250);await page.screenshot({path:path.join(__dirname,'bridge-clean.png')});await page.selectOption('#view','mezzanine',{force:true});await page.waitForTimeout(250);await page.screenshot({path:path.join(__dirname,'mezzanine-clean.png')});
 await browser.close();if(errors.length)throw Error(errors.join('\n'));
 fs.writeFileSync(path.join(__dirname,'viewer-validation.json'),JSON.stringify({sha256,errors,views:15,floorPlans:4,routeCount:24,gateSwitch:true,download:true,mobile:true},null,2));console.log('Viewer checks passed');
})().catch(e=>{console.error(e);process.exit(1)});
