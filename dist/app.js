const state={score:68,taskDone:false,loginType:'candidate'};
const jobs=[
 {title:'Junior Data Analyst',company:'BrightForge Tools',place:'Pune · Hybrid',score:()=>state.score,skills:['SQL','Power BI','Communication']},
 {title:'Operations Analyst',company:'NorthLoop Logistics',place:'Remote',score:()=>76,skills:['Excel','Dashboards','Problem solving']},
 {title:'Reporting Associate',company:'GreenCart Retail',place:'Mumbai · On-site',score:()=>71,skills:['Excel','SQL','Data quality']},
 {title:'Customer Insights Intern',company:'LoopLearn',place:'Bengaluru · Hybrid',score:()=>67,skills:['Research','Storytelling','Dashboards']}
];
const skills=[['SQL','Advanced','Verified'],['Excel','Advanced','Verified'],['Data storytelling','Strong','Verified'],['Problem solving','Strong','Verified'],['Power BI','Intermediate',()=>state.taskDone?'Verified':'Developing'],['Python','Developing','Candidate supplied'],['Communication','Strong','Verified']];
const factors=[['Essential skill coverage',state.taskDone?82:68,35],['Evidence strength',state.taskDone?78:55,25],['Relevant experience',80,15],['Transferable skills',90,10],['Evidence recency',85,5],['Preferences',100,10]];
const $=(s)=>document.querySelector(s), $$=(s)=>[...document.querySelectorAll(s)];
function showToast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
function go(id){$$('.screen').forEach(x=>x.classList.remove('active'));$('#'+id).classList.add('active');window.scrollTo({top:0,behavior:'smooth'})}
$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));
function openModal(id){$('#'+id).classList.add('open');$('#'+id).setAttribute('aria-hidden','false')}
function closeModal(id){$('#'+id).classList.remove('open');$('#'+id).setAttribute('aria-hidden','true')}
$$('[data-close]').forEach(b=>b.onclick=()=>closeModal(b.dataset.close));
$('#loginOpen').onclick=()=>openModal('loginModal');
$('#tryCandidate').onclick=()=>quickLogin('candidate'); $('#tryEmployer').onclick=()=>quickLogin('employer');
$('#seeWhy').onclick=()=>{renderMatch();openModal('matchModal')};
function quickLogin(type){state.loginType=type; setLoginFields(type); closeModal('loginModal');go(type==='candidate'?'candidate':'employer');showToast(type==='candidate'?'Logged in as Aisha Khan':'Logged in as BrightForge recruiter')}
function setLoginFields(type){$('#emailInput').value=type==='candidate'?'aisha@include.ai':'hr@brightforge.in';$('#passwordInput').value='include123';$$('[data-login-type]').forEach(b=>b.classList.toggle('active',b.dataset.loginType===type))}
$$('[data-login-type]').forEach(b=>b.onclick=()=>{state.loginType=b.dataset.loginType;setLoginFields(state.loginType)});
$('#loginSubmit').onclick=()=>{const e=$('#emailInput').value.trim(),p=$('#passwordInput').value;if(p!=='include123'||!['aisha@include.ai','hr@brightforge.in'].includes(e)){showToast('Use one of the accounts shown below');return}quickLogin(e.startsWith('aisha')?'candidate':'employer')};
function switchPanel(prefix,name){$$(`#${prefix} .panel`).forEach(p=>p.classList.remove('active'));$(`#${name}Panel`).classList.add('active')}
$$('[data-panel]').forEach(b=>b.onclick=()=>{$$('[data-panel]').forEach(x=>x.classList.remove('active'));b.classList.add('active');switchPanel('candidate',b.dataset.panel)});
$$('[data-open-panel]').forEach(b=>b.onclick=()=>{go('candidate');switchPanel('candidate',b.dataset.openPanel);$$('[data-panel]').forEach(x=>x.classList.toggle('active',x.dataset.panel===b.dataset.openPanel))});
$$('[data-epanel]').forEach(b=>b.onclick=()=>{$$('[data-epanel]').forEach(x=>x.classList.remove('active'));b.classList.add('active');switchPanel('employer',b.dataset.epanel)});
$$('[data-open-epanel]').forEach(b=>b.onclick=()=>{switchPanel('employer',b.dataset.openEpanel);$$('[data-epanel]').forEach(x=>x.classList.toggle('active',x.dataset.epanel===b.dataset.openEpanel))});
function renderJobs(){const root=$('#jobList');root.innerHTML=jobs.map((j,i)=>`<article class="job-card ${i===0?'featured':''}" style="margin-bottom:14px"><div class="company-logo ${i%2?'purple':''}">${j.company.split(/\s/).map(x=>x[0]).slice(0,2).join('')}</div><div><h4>${j.title}</h4><p>${j.company} · ${j.place}</p><div class="chips">${j.skills.map(s=>`<span>${s}</span>`).join('')}</div></div><div class="score-badge ${i?'amber':''}">${j.score()}%</div><button class="secondary compact ${i===0?'matchDetails':'toastAction'}">Why?</button></article>`).join('');bindActions()}
function renderSkills(){$('#skillTable').innerHTML=skills.map(s=>{const st=typeof s[2]==='function'?s[2]():s[2];return `<div class="skill-item"><b>${s[0]}</b><span>${s[1]}</span><span class="${st==='Verified'?'verified':st==='Developing'?'developing':''}">${st}</span></div>`}).join('')}
function renderMatch(){const fs=[['Essential skill coverage',state.taskDone?82:68,35],['Evidence strength',state.taskDone?78:55,25],['Relevant experience',80,15],['Transferable skills',90,10],['Evidence recency',85,5],['Preferences',100,10]];$('#modalScore').textContent=state.score+'%';$('#scoreFactors').innerHTML=fs.map(([n,v,w])=>`<div class="factor"><span>${n} <small>(${w}%)</small></span><div class="bar"><i style="width:${v}%"></i></div><b>${v}</b></div>`).join('')}
function bindActions(){$$('.matchDetails').forEach(b=>b.onclick=()=>{renderMatch();openModal('matchModal')});$$('.matchDetailsAlt').forEach(b=>b.onclick=()=>showToast('76% match: strong Excel and dashboard evidence'));$$('.toastAction').forEach(b=>b.onclick=()=>showToast('Action saved'))}
function refresh(){['#overviewScore','#cardScore','#heroScore'].forEach(s=>$(s).textContent=state.score+'%');renderJobs();renderSkills();$('#powerEvidence').textContent=state.taskDone?'Dashboard task · verified':'Not added yet';$('#powerEvidence').className=state.taskDone?'verified':'';$('#taskStatus').textContent=state.taskDone?'✓ Evidence verified. Match improved from 68% to 83%.':'';$('#completeTask').textContent=state.taskDone?'Task complete ✓':'Mark task complete'}
$('#completeTask').onclick=()=>{if(state.taskDone){showToast('The task is already complete');return}state.taskDone=true;state.score=83;refresh();showToast('New evidence verified. Match increased to 83%!')};
$('#resetDemo').onclick=()=>{state.taskDone=false;state.score=68;refresh();showToast('Candidate journey reset')};
$('#addEvidence').onclick=()=>showToast('Upload opened: resume, project link or certificate');
$$('.fixCriteria').forEach(b=>b.onclick=()=>{b.textContent='Suggestion accepted ✓';b.disabled=true;showToast('Job criteria updated and audit log saved')});
$('#downloadResume').onclick=()=>{const html=`<!doctype html><meta charset="utf-8"><title>Aisha Khan Resume</title><style>body{font:16px Arial;max-width:760px;margin:50px auto;line-height:1.5}h1{border-bottom:4px solid #111;padding-bottom:10px}h2{color:#d52e67;font-size:17px;margin-top:25px}</style><h1>Aisha Khan</h1><p>Early-career Data Analyst · Pune · aisha@include.ai</p><h2>PROFILE</h2><p>Data-focused problem solver with project experience in SQL, dashboards and retail analysis.</p><h2>SKILLS</h2><p>SQL · Excel · Power BI · Data storytelling · Python</p><h2>PROJECTS</h2><b>Retail Sales Analysis</b><p>Cleaned 12,000 sales records and identified category-level patterns.</p><b>Hackathon Workforce Pitch</b><p>Designed and presented an inclusive hiring concept.</p><h2>EDUCATION</h2><p>B.Com coursework, 2023–2024. Continued learning through projects and short courses.</p>`;const blob=new Blob([html],{type:'text/html'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Aisha_Khan_Resume.html';a.click();URL.revokeObjectURL(a.href);showToast('Resume downloaded')};
window.onclick=e=>{if(e.target.classList.contains('modal'))closeModal(e.target.id)};
renderJobs();renderSkills();bindActions();refresh();
