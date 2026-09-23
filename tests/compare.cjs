const {chromium}=require('C:/Users/39015/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
 const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const p=await b.newPage({viewport:{width:1500,height:980}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8767/compare.html');
 async function loaded(){await p.waitForFunction(()=>[...document.images].every(x=>x.complete&&x.naturalWidth>0));}
 await loaded();await p.screenshot({path:path.join(__dirname,'compare-page.png'),fullPage:true});
 for(const frame of ['guide','top'])for(const rev of ['before','after']){await p.selectOption('#frame',frame);await p.selectOption('#revision',rev);await loaded();}
 await p.locator('#opacity').fill('0');if(await p.locator('[data-layer="security"]').evaluate(x=>x.style.opacity)!=='0')throw Error('Opacity failed');
 await p.locator('#opacity').fill('85');await p.locator('[data-category="security"]').uncheck();if(await p.locator('[data-layer="security"]').evaluate(x=>x.style.opacity)!=='0')throw Error('Category failed');
 await p.locator('[data-category="security"]').check();await p.locator('#blink').dispatchEvent('keydown',{code:'Space'});if(await p.locator('[data-layer="security"]').evaluate(x=>x.style.opacity)!=='0')throw Error('Blink failed');await p.locator('#blink').dispatchEvent('keyup',{code:'Space'});
 await p.setViewportSize({width:390,height:844});await loaded();if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');await p.screenshot({path:path.join(__dirname,'compare-mobile.png'),fullPage:true});
 const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'../assets/plan-compare/manifest.json')));const sha=crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'../assets/xiamen-gaoqi-t4.glb'))).digest('hex');if(manifest.revisions.after.sha256!==sha)throw Error('Stale overlay');
 await p.setViewportSize({width:1400,height:1000});await p.goto('http://127.0.0.1:8767/arrival-finger-compare.html');await loaded();
 for(const area of ['arrival','finger'])for(const rev of ['before','after']){await p.selectOption('#area',area);await p.selectOption('#revision',rev);await loaded();}
 await p.screenshot({path:path.join(__dirname,'finger-compare-page.png'),fullPage:true});await p.selectOption('#area','arrival');await loaded();await p.screenshot({path:path.join(__dirname,'arrival-compare-page.png'),fullPage:true});
 await p.locator('#opacity').fill('0');if(await p.locator('#model').evaluate(x=>x.style.opacity)!=='0')throw Error('Arrival opacity failed');
 const extra=JSON.parse(fs.readFileSync(path.join(__dirname,'../assets/arrival-finger-compare/report.json')));for(const area of ['arrival','finger'])if(extra[area].versions.after.sha256!==sha)throw Error('Stale arrival/finger projection');
 await p.setViewportSize({width:390,height:844});if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Arrival mobile overflow');
 await b.close();if(errors.length)throw Error(errors.join('\n'));fs.writeFileSync(path.join(__dirname,'compare-validation.json'),JSON.stringify({sha256:sha,errors,frames:2,revisions:2,opacity:true,category:true,blink:true,mobile:true},null,2));console.log('Comparison checks passed');
})().catch(e=>{console.error(e);process.exit(1)});
