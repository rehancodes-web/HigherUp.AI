const state = {
  score: 68,
  taskDone: false,
  loginType: 'candidate',
  currentEmail: '',
  deckIndex: 0,
  decisions: [],
  authenticated: false,
  summaryFields: [
    'skills',
    'projects',
    'internships',
    'experience',
    'hackathons',
    'certifications',
    'location',
    'gaps'
  ]
};
const candidates=[
 {name:'Aisha Khan',initials:'AK',headline:'Project-trained Data Analyst',location:'Pune · Available in 2 weeks',score:83,confidence:'High evidence confidence',summary:'Turns messy business data into clear decisions through projects, freelance tasks and hackathons.',skills:['SQL','Excel','Power BI','Data storytelling'],proof:[['Retail sales analysis','Cleaned 12,000 records and surfaced category trends'],['Power BI dashboard','Built a decision-ready dashboard from a timed brief'],['Freelance data cleanup','Standardised inconsistent customer and sales data']],gap:'Python is developing; it is not essential for this role.',factors:[['Essential skills',86,35],['Evidence strength',82,25],['Relevant work',76,15],['Transferable skills',91,10],['Recency',88,5],['Preferences',100,10]]},
 {name:'Vikram Joshi',initials:'VJ',headline:'Operations & Reporting Analyst',location:'Pune · Available now',score:80,confidence:'High evidence confidence',summary:'Combines shop-floor operations knowledge with strong spreadsheet reporting and process improvement.',skills:['Advanced Excel','Dashboards','Process mapping','SQL'],proof:[['Inventory tracker','Reduced weekly reconciliation time by 30%'],['Operations role','Two years of hands-on reporting work'],['SQL assessment','Passed the role-aligned query challenge']],gap:'Power BI evidence is basic; adjacent dashboard skills are strong.',factors:[['Essential skills',79,35],['Evidence strength',88,25],['Relevant work',92,15],['Transferable skills',84,10],['Recency',82,5],['Preferences',70,10]]},
 {name:'Sana Ali',initials:'SA',headline:'Self-taught Business Data Explorer',location:'Remote · Open to hybrid',score:74,confidence:'Medium evidence confidence',summary:'A fast learner with strong analytical reasoning, customer research and clear presentation skills.',skills:['Excel','Research','Storytelling','Data cleaning'],proof:[['Customer survey study','Analysed 430 responses and presented segments'],['Excel assessment','Scored 87% on a practical task'],['Community project','Tracked outcomes and created monthly reports']],gap:'Needs stronger SQL proof. Request a short work sample instead of guessing.',factors:[['Essential skills',66,35],['Evidence strength',67,25],['Relevant work',70,15],['Transferable skills',94,10],['Recency',90,5],['Preferences',90,10]]},
 {name:'Arjun Das',initials:'AD',headline:'Commerce Learner turned Analyst',location:'Mumbai · Ready to relocate',score:78,confidence:'High evidence confidence',summary:'Applies commercial understanding to data analysis with strong Excel, reporting and communication.',skills:['Excel','SQL','Business metrics','Communication'],proof:[['Profitability analysis','Compared margins across 60 products'],['SQL project','Created sales, returns and cohort queries'],['Peer mentoring','Explained spreadsheets to 25 learners']],gap:'No formal analyst title yet; project evidence covers the core tasks.',factors:[['Essential skills',81,35],['Evidence strength',80,25],['Relevant work',68,15],['Transferable skills',92,10],['Recency',86,5],['Preferences',80,10]]}
];
const candidateDetails={
 'Aisha Khan':{projects:'Retail analysis: cleaned 12,000 records and found category trends.',internships:'Business data intern · 3 months · weekly reporting.',experience:'Freelance data cleanup for a local retailer.',hackathons:'Inclusive Workforce hackathon · analytics and pitch lead.',certifications:'SQL Fundamentals · Excel for Business.'},
 'Vikram Joshi':{projects:'Inventory tracker reduced reconciliation time by 30%.',internships:'Not provided.',experience:'2 years in operations reporting and process improvement.',hackathons:'Operations automation challenge participant.',certifications:'Advanced Excel · SQL assessment verified.'},
 'Sana Ali':{projects:'Analysed 430 customer survey responses and created segments.',internships:'Community research internship · 8 weeks.',experience:'Volunteer reporting for a local organisation.',hackathons:'Data for Good challenge · finalist.',certifications:'Excel Skills for Business.'},
 'Arjun Das':{projects:'Compared profitability across 60 products.',internships:'Finance operations intern · 2 months.',experience:'Peer mentor for 25 spreadsheet learners.',hackathons:'Commerce analytics sprint participant.',certifications:'SQL Basics · Business Metrics.'}
};
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
function go(id){if(['candidate','employer'].includes(id)&&!state.authenticated){state.loginType=id==='employer'?'employer':'candidate';setLoginFields(state.loginType);openModal('loginModal');showToast('Log in to view account data');return}$$('.screen').forEach(x=>x.classList.remove('active'));$('#'+id).classList.add('active');window.scrollTo({top:0,behavior:'smooth'})}
$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));
function openModal(id){$('#'+id).classList.add('open');$('#'+id).setAttribute('aria-hidden','false')}
function closeModal(id){$('#'+id).classList.remove('open');$('#'+id).setAttribute('aria-hidden','true')}
$$('[data-close]').forEach(b=>b.onclick=()=>closeModal(b.dataset.close));
$('#loginOpen').onclick=()=>{if(state.authenticated){state.authenticated=false;$('#loginOpen').textContent='Log in';go('home');showToast('Logged out securely')}else openModal('loginModal')};
function requestLogin(type){state.loginType=type;setLoginFields(type);openModal('loginModal')}
$('#tryCandidate').onclick=()=>requestLogin('candidate'); $('#tryEmployer').onclick=()=>requestLogin('employer');
$('#seeWhy').onclick=()=>{if(!state.authenticated){requestLogin('candidate');showToast('Log in to view match details');return}renderMatch();openModal('matchModal')};
function quickLogin(type) {
  state.loginType = type;

  state.currentEmail =
    type === 'candidate'
      ? 'aisha@higherup.ai'
      : 'hr@brightforge.in';

  state.authenticated = true;

  setLoginFields(type);
  closeModal('loginModal');

  $('#loginOpen').textContent = 'Log out';

  go(type === 'candidate' ? 'candidate' : 'employer');

  if (type === 'employer') {
    openEmployerPanel('talent');
    renderCandidate();
  }

  showToast(
    type === 'candidate'
      ? 'Logged in as Aisha Khan'
      : 'Talent deck ready for BrightForge'
  );
}
function setLoginFields(type){$('#emailInput').value=type==='candidate'?'aisha@higherup.ai':'hr@brightforge.in';$('#passwordInput').value='higherup123';$$('[data-login-type]').forEach(b=>b.classList.toggle('active',b.dataset.loginType===type))}
$$('[data-login-type]').forEach(b=>b.onclick=()=>{state.loginType=b.dataset.loginType;setLoginFields(state.loginType)});
$('#loginSubmit').onclick=()=>{const e=$('#emailInput').value.trim(),p=$('#passwordInput').value;if(p!=='higherup123'||!['aisha@higherup.ai','hr@brightforge.in'].includes(e)){showToast('Use one of the accounts shown below');return}quickLogin(e.startsWith('aisha')?'candidate':'employer')};
function switchPanel(prefix,name){$$(`#${prefix} .panel`).forEach(p=>p.classList.remove('active'));$(`#${name}Panel`).classList.add('active')}
$$('[data-panel]').forEach(b=>b.onclick=()=>{$$('[data-panel]').forEach(x=>x.classList.remove('active'));b.classList.add('active');switchPanel('candidate',b.dataset.panel)});
$$('[data-open-panel]').forEach(b=>b.onclick=()=>{if(!state.authenticated){requestLogin('candidate');return}go('candidate');switchPanel('candidate',b.dataset.openPanel);$$('[data-panel]').forEach(x=>x.classList.toggle('active',x.dataset.panel===b.dataset.openPanel))});
function openEmployerPanel(name){switchPanel('employer',name);$$('[data-epanel]').forEach(x=>x.classList.toggle('active',x.dataset.epanel===name));if(name==='decisions')renderDecisions()}
$$('[data-epanel]').forEach(b=>b.onclick=()=>openEmployerPanel(b.dataset.epanel));
$$('[data-open-epanel]').forEach(b=>b.onclick=()=>openEmployerPanel(b.dataset.openEpanel));
function renderCandidate(){const card=$('#talentCard'),c=candidates[state.deckIndex];if(!c){card.className='talent-card';card.innerHTML=`<div class="deck-complete"><span>✓</span><h2>You reviewed every candidate</h2><p>Your choices are saved. Review them, undo the last swipe, or restart the deck.</p><button class="primary" data-show-decisions>View my decisions</button></div>`;$('#deckCount').textContent='Complete';$('#deckFactors').innerHTML='';$('#deckConfidence').textContent='Review complete';card.querySelector('[data-show-decisions]').onclick=()=>openEmployerPanel('decisions');return}const d=candidateDetails[c.name],has=f=>state.summaryFields.includes(f);const requested=[['projects','Relevant project',d.projects],['internships','Internship',d.internships],['experience','Previous work',d.experience],['hackathons','Hackathon',d.hackathons],['certifications','Courses & certifications',d.certifications]].filter(x=>has(x[0]));$('#deckCount').textContent=`${state.deckIndex+1} of ${candidates.length}`;$('#deckConfidence').textContent=c.confidence;card.className='talent-card';card.style.transform='';card.innerHTML=`<div class="candidate-top"><div class="candidate-avatar">${c.initials}</div><div><p class="eyebrow">YOUR CUSTOM ONE-PAGE SUMMARY</p><h2>${c.name}</h2><p>${c.headline}${has('location')?' · '+c.location:''}</p></div><div class="hero-match"><strong>${c.score}%</strong><span>job match</span></div></div><p class="candidate-summary">${c.summary}</p>${has('skills')?`<div class="card-section"><b>Core skills</b><div class="profile-skills">${c.skills.map(s=>`<span>${s}</span>`).join('')}</div></div>`:''}${requested.length?`<div class="custom-summary-grid">${requested.map(([,label,value])=>`<div><b>${label}</b><p>${value}</p></div>`).join('')}</div>`:''}${has('gaps')?`<div class="gap-note"><b>What to check in the interview</b><p>${c.gap}</p></div>`:''}<div class="card-footer"><span>${state.summaryFields.length} recruiter-selected fields</span><span>${c.confidence.replace(' evidence confidence',' confidence')}</span><span>Human decision only</span></div><div class="swipe-stamp pass-stamp">PASS</div><div class="swipe-stamp yes-stamp">SHORTLIST</div>`;$('#deckFactors').innerHTML=c.factors.map(([n,v,w])=>`<div><span>${n}<small>${w}% weight</small></span><div class="mini-bar"><i style="width:${v}%"></i></div><b>${v}</b></div>`).join('');attachSwipe(card)}
function decide(direction){const c=candidates[state.deckIndex];if(!c)return;const card=$('#talentCard');card.classList.add(direction==='right'?'fly-right':'fly-left');state.decisions.push({candidate:c,decision:direction==='right'?'Shortlisted':'Passed for this role'});setTimeout(()=>{state.deckIndex++;card.className='talent-card';card.style.transform='';renderCandidate();updateDecisionTotals()},260)}
function attachSwipe(card){let startX=0,delta=0,dragging=false;card.onpointerdown=e=>{dragging=true;startX=e.clientX;card.setPointerCapture(e.pointerId);card.classList.add('dragging')};card.onpointermove=e=>{if(!dragging)return;delta=e.clientX-startX;card.style.transform=`translateX(${delta}px) rotate(${delta/24}deg)`;card.classList.toggle('lean-right',delta>35);card.classList.toggle('lean-left',delta<-35)};card.onpointerup=()=>{if(!dragging)return;dragging=false;card.classList.remove('dragging');if(Math.abs(delta)>110)decide(delta>0?'right':'left');else{card.style.transform='';card.classList.remove('lean-right','lean-left')}delta=0}}
function updateDecisionTotals(){$('#shortlistTotal').textContent=state.decisions.filter(x=>x.decision==='Shortlisted').length;$('#passTotal').textContent=state.decisions.filter(x=>x.decision!=='Shortlisted').length;$('#remainingTotal').textContent=candidates.length-state.decisions.length}
function undoDecision(){if(!state.decisions.length){showToast('No decision to undo');return}state.decisions.pop();state.deckIndex=Math.max(0,state.deckIndex-1);renderCandidate();updateDecisionTotals();showToast('Last swipe undone')}
function renderDecisions(){updateDecisionTotals();const root=$('#decisionList');root.innerHTML=state.decisions.length?state.decisions.map((x,i)=>`<article><div class="candidate-avatar small">${x.candidate.initials}</div><div><b>${x.candidate.name}</b><span>${x.candidate.headline}</span></div><strong class="decision-score">${x.candidate.score}%</strong><span class="decision-status ${x.decision==='Shortlisted'?'selected':''}">${x.decision}</span><button class="text-btn" data-undo-index="${i}">Undo</button></article>`).join(''):`<div class="empty-decisions"><b>No decisions yet</b><p>Open the Talent Deck and swipe through the candidate summaries.</p></div>`;$$('[data-undo-index]').forEach(b=>b.onclick=()=>{state.decisions.splice(Number(b.dataset.undoIndex),1);state.deckIndex=state.decisions.length;renderDecisions();renderCandidate();showToast('Decision removed')})}
$('#passCandidate').onclick=()=>decide('left');$('#shortlistCandidate').onclick=()=>decide('right');$('#undoDecision').onclick=undoDecision;$('#resetDeck').onclick=()=>{state.deckIndex=0;state.decisions=[];renderCandidate();renderDecisions();showToast('Talent deck restarted')};document.addEventListener('keydown',e=>{if(!$('#employer').classList.contains('active')||!$('#talentPanel').classList.contains('active'))return;if(e.key==='ArrowLeft')decide('left');if(e.key==='ArrowRight')decide('right')});
function renderJobs(){const root=$('#jobList');root.innerHTML=jobs.map((j,i)=>`<article class="job-card ${i===0?'featured':''}" style="margin-bottom:14px"><div class="company-logo ${i%2?'purple':''}">${j.company.split(/\s/).map(x=>x[0]).slice(0,2).join('')}</div><div><h4>${j.title}</h4><p>${j.company} · ${j.place}</p><div class="chips">${j.skills.map(s=>`<span>${s}</span>`).join('')}</div></div><div class="score-badge ${i?'amber':''}">${j.score()}%</div><button class="secondary compact ${i===0?'matchDetails':'toastAction'}">Why?</button></article>`).join('');bindActions()}
function renderSkills(){$('#skillTable').innerHTML=skills.map(s=>{const st=typeof s[2]==='function'?s[2]():s[2];return `<div class="skill-item"><b>${s[0]}</b><span>${s[1]}</span><span class="${st==='Verified'?'verified':st==='Developing'?'developing':''}">${st}</span></div>`}).join('')}
function renderMatch(){const fs=[['Essential skill coverage',state.taskDone?82:68,35],['Evidence strength',state.taskDone?78:55,25],['Relevant experience',80,15],['Transferable skills',90,10],['Evidence recency',85,5],['Preferences',100,10]];$('#modalScore').textContent=state.score+'%';$('#scoreFactors').innerHTML=fs.map(([n,v,w])=>`<div class="factor"><span>${n} <small>(${w}%)</small></span><div class="bar"><i style="width:${v}%"></i></div><b>${v}</b></div>`).join('')}
function bindActions(){$$('.matchDetails').forEach(b=>b.onclick=()=>{renderMatch();openModal('matchModal')});$$('.matchDetailsAlt').forEach(b=>b.onclick=()=>showToast('76% match: strong Excel and dashboard evidence'));$$('.toastAction').forEach(b=>b.onclick=()=>showToast('Action saved'))}
function refresh(){['#overviewScore','#cardScore','#heroScore'].forEach(s=>$(s).textContent=state.score+'%');renderJobs();renderSkills();$('#powerEvidence').textContent=state.taskDone?'Dashboard task · verified':'Not added yet';$('#powerEvidence').className=state.taskDone?'verified':'';$('#taskStatus').textContent=state.taskDone?'✓ Evidence verified. Match improved from 68% to 83%.':'';$('#completeTask').textContent=state.taskDone?'Task complete ✓':'Mark task complete'}
$('#completeTask').onclick=()=>{if(state.taskDone){showToast('The task is already complete');return}state.taskDone=true;state.score=83;refresh();showToast('New evidence verified. Match increased to 83%!')};
$('#resetDemo').onclick=()=>{state.taskDone=false;state.score=68;refresh();showToast('Candidate journey reset')};
$('#passportPanel').insertAdjacentHTML('afterbegin',`<div class="candidate-profile-head"><div><p class="eyebrow">MY PROFILE</p><h2>Aisha Khan</h2><p>Control the resume, evidence and preferences used for job matching.</p></div><div class="profile-completion"><b>78%</b><span>complete</span></div></div><div class="profile-setup-grid"><section class="profile-box"><div class="box-title"><div><p class="eyebrow">RESUME / CV</p><h3>Your source document</h3></div><span class="tag cyan" id="resumeState">Analysed</span></div><div class="uploaded-file"><div class="file-icon">PDF</div><div><b id="resumeFileName">Aisha_Khan_Resume.pdf</b><span>Uploaded today · 1.2 MB</span></div></div><p>The AI extracts skills, projects, internships, hackathons and certifications. You can correct every field below.</p><input type="file" id="resumeUpload" accept=".pdf,.doc,.docx" hidden><button class="primary compact" id="replaceResume">Upload or replace resume</button></section><section class="profile-box"><div class="box-title"><div><p class="eyebrow">JOB PREFERENCES</p><h3>What are you looking for?</h3></div></div><div class="preference-form"><label>Preferred roles<input id="prefRoles" value="Data Analyst, Operations Analyst"></label><label>Preferred cities<input id="prefCities" value="Pune, Mumbai, Remote"></label><label>Work mode<select id="prefMode"><option>Hybrid or Remote</option><option>Remote only</option><option>On-site</option><option>Any</option></select></label><label>Minimum salary<input id="prefSalary" value="₹4.5 LPA"></label><label>Company type<select id="prefCompany"><option>MSME or growth-stage</option><option>Any company</option><option>Startup</option><option>Large enterprise</option></select></label><label>Availability<select id="prefAvailability"><option>Within 2 weeks</option><option>Immediately</option><option>Within 1 month</option></select></label><label class="check-line"><input type="checkbox" id="prefRelocate"> Open to relocation</label><label class="check-line"><input type="checkbox" id="prefAutoApply" checked> Let Apply Agent prepare high-fit applications</label></div><button class="primary compact" id="savePreferences">Save preferences</button></section></div>`);
$('#replaceResume').onclick=()=>$('#resumeUpload').click();
$('#resumeUpload').onchange=e=>{const file=e.target.files[0];if(!file)return;$('#resumeFileName').textContent=file.name;$('#resumeState').textContent='Analysing…';setTimeout(()=>{$('#resumeState').textContent='Analysed';showToast('Resume analysed and profile updated')},700)};
$('#savePreferences').onclick=()=>{const roles=$('#prefRoles').value||'Any suitable role',cities=$('#prefCities').value||'Any location',mode=$('#prefMode').value,salary=$('#prefSalary').value||'Not specified';const cards=$$('.preference-grid article b');if(cards.length>=4){cards[0].textContent=roles;cards[1].textContent=cities;cards[2].textContent=mode;cards[3].textContent=salary}$('#agentToggle').checked=$('#prefAutoApply').checked;$('#agentStatus').textContent=$('#prefAutoApply').checked?'Active':'Paused';showToast('Profile and job preferences saved')};
$('#addEvidence').onclick=()=>showToast('Upload opened: resume, project link or certificate');
$('#agentToggle').onchange=e=>{const on=e.target.checked;$('#agentStatus').textContent=on?'Active':'Paused';showToast(on?'Apply Agent is now finding high-fit roles':'Apply Agent paused')};
$$('.approveApply').forEach(b=>b.onclick=()=>{b.textContent='Approved ✓';b.disabled=true;showToast('Application approved and added to your tracker')});
$$('.fixCriteria').forEach(b=>b.onclick=()=>{b.textContent='Suggestion accepted ✓';b.disabled=true;showToast('Job criteria updated and audit log saved')});
function readSummaryFields(){return $$('[data-summary-field]:checked').map(x=>x.dataset.summaryField)}
function updateFieldCount(){const n=readSummaryFields().length;$('#selectedFieldCount').textContent=`${n} field${n===1?'':'s'} selected`}
$$('[data-summary-field]').forEach(x=>x.onchange=updateFieldCount);
const API_BASE = 'http://127.0.0.1:8000';

async function saveCandidatePreferences() {
  const roles =
    $('#prefRoles').value.trim() || 'Any suitable role';

  const cities =
    $('#prefCities').value.trim() || 'Any location';

  const mode = $('#prefMode').value;

  const salary =
    $('#prefSalary').value.trim() || 'Not specified';

  // Update the preference cards in the interface.
  const cards = $$('.preference-grid article b');

  if (cards.length >= 4) {
    cards[0].textContent = roles;
    cards[1].textContent = cities;
    cards[2].textContent = mode;
    cards[3].textContent = salary;
  }

  $('#agentToggle').checked = $('#prefAutoApply').checked;

  $('#agentStatus').textContent =
    $('#prefAutoApply').checked ? 'Active' : 'Paused';

  // Require a candidate demo login.
  if (
    !state.authenticated ||
    state.loginType !== 'candidate' ||
    !state.currentEmail
  ) {
    showToast('Log in as a candidate before saving to the database');
    return;
  }

  const button = $('#savePreferences');

  button.disabled = true;
  button.textContent = 'Saving…';

  try {
    const response = await fetch(
      `${API_BASE}/candidates/by-email/${encodeURIComponent(
        state.currentEmail
      )}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          full_name: 'Aisha Khan',
          email: state.currentEmail,
          preferred_roles: roles,
          preferred_locations: cities,
          work_mode: mode
        })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || `Request failed (${response.status})`
      );
    }

    showToast(
      `Preferences saved to SAP HANA (${result.status})`
    );

  } catch (error) {
    console.error(
      'Could not save candidate preferences:',
      error
    );

    showToast(
      'Could not save to SAP HANA. Check whether FastAPI is running.'
    );

  } finally {
    button.disabled = false;
    button.textContent = 'Save preferences';
  }
}

$('#savePreferences').onclick = saveCandidatePreferences;
$('#previewSummary').onclick=()=>{const fields=readSummaryFields();if(!fields.length){showToast('Select at least one summary field');return}state.summaryFields=fields;renderCandidate();openEmployerPanel('talent');showToast('Candidate cards updated to your template')};
$('#downloadResume').onclick=()=>{const html=`<!doctype html><meta charset="utf-8"><title>Aisha Khan Resume</title><style>body{font:16px Arial;max-width:760px;margin:50px auto;line-height:1.5}h1{border-bottom:4px solid #111;padding-bottom:10px}h2{color:#d52e67;font-size:17px;margin-top:25px}</style><h1>Aisha Khan</h1><p>Early-career Data Analyst · Pune · aisha@higherup.ai</p><h2>PROFILE</h2><p>Data-focused problem solver with project experience in SQL, dashboards and retail analysis.</p><h2>SKILLS</h2><p>SQL · Excel · Power BI · Data storytelling · Python</p><h2>PROJECTS</h2><b>Retail Sales Analysis</b><p>Cleaned 12,000 sales records and identified category-level patterns.</p><b>Hackathon Workforce Pitch</b><p>Designed and presented an inclusive hiring concept.</p><h2>EDUCATION</h2><p>B.Com coursework, 2023–2024. Continued learning through projects and short courses.</p>`;const blob=new Blob([html],{type:'text/html'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Aisha_Khan_Resume.html';a.click();URL.revokeObjectURL(a.href);showToast('Resume downloaded')};
window.onclick=e=>{if(e.target.classList.contains('modal'))closeModal(e.target.id)};
renderJobs();renderSkills();bindActions();refresh();renderCandidate();updateDecisionTotals();
