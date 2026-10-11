const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(__dirname,'../deploy/analytics/chemgrid-analytics.js'),'utf8');
function boot(host){
 const calls=[],listeners={},response={ok:true};
 const window={location:{hostname:host,origin:'https://'+host,pathname:'/',href:'https://'+host+'/',search:''},dataLayer:[],history:{pushState(){},replaceState(){}},addEventListener(){},setTimeout(){},fetch:()=>Promise.resolve(response)};
 const document={title:'',head:{appendChild(){}},createElement:()=>({}),addEventListener:(name,fn)=>listeners[name]=fn,querySelector:()=>null};
 window.gtag=(...args)=>calls.push(args);
 vm.runInNewContext(source,{window,document,navigator:{userAgent:'Browser'},Set,URL,URLSearchParams,Date});
 return {window,listeners,calls,response};
}
(async()=>{
 for(const app of ['boxplotr','growthcurve','checkerboardr']){
  const s=boot(app+'.chemgrid.org');
  assert.equal(s.calls.filter(c=>c[0]==='config').length,2);
  for(const [id,fmt] of (app==='growthcurve'?[['wellPlotDownload','pdf'],['PlateParameterTableDownload','csv']]:[['downloadPlotPDF','pdf'],['downloadPlotSVG','svg'],['downloadMatrixCSV','csv']])){
   const link={id,classList:{contains:()=>false},getAttribute:n=>n==='href'?'/session/download':null};
   s.listeners.click({target:{closest:sel=>sel==='a.shiny-download-link'?link:null}});
   const e=s.calls.at(-1);assert.equal(e[1],'file_download');assert.equal(e[2].file_extension,fmt);assert.equal(e[2].app_name,app);assert.equal(e[2].interface,'web');assert(e[2].send_to.includes('G-LMCPLNFJPV'));assert.equal(e[2].send_to.length,2);
  }
  const before=s.calls.length;
  s.listeners.change({target:{id:'upload',files:[],matches:()=>true}});assert.equal(s.calls.length,before);
  s.listeners.change({target:{id:'upload',files:[{name:'PRIVATE_FILENAME'}],matches:()=>true}});assert.equal(s.calls.at(-1)[1],'file_upload');assert(!JSON.stringify(s.calls).includes('PRIVATE_FILENAME'));
 }
 const s=boot('chemgrid.org');
 const actual=await s.window.fetch('/api/v1/compounds/search?q=PRIVATE_QUERY&field=name');assert.strictEqual(actual,s.response);
 await Promise.resolve();assert.equal(s.calls.at(-1)[1],'search');assert.equal(s.calls.at(-1)[2].search_type,'compound');
 await s.window.fetch('/api/v1/structures/search',{body:JSON.stringify({query:'PRIVATE_SMILES',mode:'similarity'})});await Promise.resolve();assert.equal(s.calls.at(-1)[2].search_method,'similarity');
 const before=s.calls.length;s.response.ok=false;await s.window.fetch('/api/v1/genes/search?q=PRIVATE_QUERY');await Promise.resolve();assert.equal(s.calls.length,before);
 await s.window.fetch('https://example.com/api/v1/genes/search?q=PRIVATE_QUERY');await Promise.resolve();assert.equal(s.calls.length,before);
 assert(!JSON.stringify(s.calls).includes('PRIVATE_'));
 console.log('PASS: all three apps label exports and uploads; searches preserve responses, report categories, omit private data and exclude failed/external requests.');
})();
