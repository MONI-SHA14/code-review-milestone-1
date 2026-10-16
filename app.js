const input = document.querySelector('#codeInput');
const language = document.querySelector('#language');
const lineNumbers = document.querySelector('#lineNumbers');
const charCount = document.querySelector('#charCount');
const submit = document.querySelector('#submitCode');
const loadExample = document.querySelector('#loadExample');
const fileHint = document.querySelector('#fileHint');
const emptyState = document.querySelector('#emptyState');
const reviewResults = document.querySelector('#reviewResults');
const statusChip = document.querySelector('#statusChip');
const summaryIcon = document.querySelector('#summaryIcon');
const summaryTitle = document.querySelector('#summaryTitle');
const summaryCopy = document.querySelector('#summaryCopy');
const findings = document.querySelector('#findings');
const guidance = document.querySelector('#guidance');

const examples = {
  python: `import sqlite3\n\ndef find_user(user_id):\n    connection = sqlite3.connect("app.db")\n    query = "SELECT * FROM users WHERE id = " + user_id\n    return connection.execute(query).fetchall()`,
  java: `import java.sql.*;\n\npublic class UserLookup {\n    public static void main(String[] args) {\n        String userId = args[0];\n        String query = "SELECT * FROM users WHERE id = " + userId;\n        System.out.println(query);\n    }\n}`
};

function updateEditorMeta() {
  const lines = Math.max(1, input.value.split('\n').length);
  lineNumbers.textContent = Array.from({length: lines}, (_, i) => i + 1).join('\n');
  charCount.textContent = `${input.value.length.toLocaleString()} characters`;
}
function setLanguage() { fileHint.textContent = language.value === 'python' ? '.py accepted' : '.java accepted'; if (!input.value.trim()) input.placeholder = `Paste your ${language.value === 'python' ? 'Python' : 'Java'} code here...`; }
function balanced(source, pairs) { const stack=[]; let quote=null, escape=false; for(let i=0;i<source.length;i++){const c=source[i]; if(quote){ if(escape) escape=false; else if(c==='\\') escape=true; else if(c===quote) quote=null; continue; } if(c==='"'||c==="'"){quote=c;continue} if(pairs.open.includes(c)) stack.push(c); else if(pairs.close.includes(c)){const want=pairs.open[pairs.close.indexOf(c)]; if(stack.pop()!==want) return {ok:false,line:source.slice(0,i).split('\n').length,message:`Unexpected '${c}'`}; }} return stack.length?{ok:false,line:source.split('\n').length,message:`Unclosed '${stack[stack.length-1]}'`}:{ok:true}; }
function validatePython(source) { const issues=[]; const p=balanced(source,{open:['(','[','{'],close:[')',']','}']}); if(!p.ok) issues.push({line:p.line,kind:'error',title:'Python syntax error',text:p.message}); source.split('\n').forEach((line,i)=>{if(/^\s*(def|class|if|for|while|try|with)\b/.test(line)&&!line.trimEnd().endsWith(':')) issues.push({line:i+1,kind:'error',title:'Missing colon',text:'This Python statement should end with a colon.'});}); return issues; }
function validateJava(source) { const issues=[]; const p=balanced(source,{open:['(','[','{'],close:[')',']','}']}); if(!p.ok) issues.push({line:p.line,kind:'error',title:'Java structure error',text:p.message}); if(!/\b(class|interface|enum)\s+[A-Za-z_$][\w$]*/.test(source)) issues.push({line:1,kind:'error',title:'Type declaration missing',text:'Add a class, interface, or enum declaration.'}); return issues; }
function securitySignals(source) { const list=[]; const lines=source.split('\n'); lines.forEach((line,i)=>{ if(/SELECT|INSERT|UPDATE|DELETE/i.test(line)&&/["'`]\s*\+|f["']/.test(line)) list.push({line:i+1,kind:'warning',title:'Potential SQL injection',text:'Avoid concatenating untrusted input into SQL. Use a parameterized query or prepared statement.'}); if(/(password|api[_-]?key|secret|token)\s*=\s*["'][^"']+/i.test(line)) list.push({line:i+1,kind:'warning',title:'Possible hardcoded secret',text:'Move credentials to a secret manager or protected environment configuration.'}); if(/innerHTML|document\.write/i.test(line)) list.push({line:i+1,kind:'warning',title:'Potential XSS sink',text:'Prefer safe DOM APIs or context-aware output encoding.'}); }); return list; }
const guidanceData=[{match:/SELECT|INSERT|UPDATE|DELETE|sql|query/i,title:'Parameterized queries',text:'Bind untrusted values with prepared statements. Do not concatenate user input into SQL.'},{match:/password|secret|token|api[_-]?key/i,title:'Secret handling',text:'Load credentials from a managed secret store or protected environment and redact them from logs.'},{match:/innerHTML|html|script|xss/i,title:'Output encoding',text:'Use framework auto-escaping and encode output for its rendering context to reduce XSS risk.'},{match:/auth|role|permission|user/i,title:'Server-side authorization',text:'Authenticate identity separately from authorization. Deny by default and check every protected action on the server.'}];
function renderGuidance(source) { const selected=guidanceData.filter(x=>x.match.test(source)); const cards=(selected.length?selected:guidanceData.slice(0,2)); guidance.innerHTML=cards.map(x=>`<div class="guidance-card"><strong>${x.title}</strong><p>${x.text}</p></div>`).join(''); }
function renderFinding(item) { return `<div class="finding ${item.kind}"><div class="finding-line">LINE ${item.line}</div><div><div class="finding-title">${item.title}</div><div class="finding-text">${item.text}</div></div></div>`; }
async function runReview() {
  const source=input.value;
  submit.disabled=true;
  submit.textContent='Reviewing...';
  try {
    const response=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language:language.value,source})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error || 'Review failed');
    const result=data.submission;
    const issues=(result.issues||[]).map(x=>({line:x.line||1,kind:'error',title:x.code==='PYTHON_SYNTAX'?'Python syntax error':x.code==='JAVA_UNBALANCED'?'Java structure error':'Validation issue',text:x.message}));
    const signals=(data.security_signals||[]).map(x=>({line:x.line,kind:'warning',title:x.code==='SQL_INJECTION_SIGNAL'?'Potential SQL injection':x.code==='HARDCODED_SECRET_SIGNAL'?'Possible hardcoded secret':'Potential XSS sink',text:x.message}));
    const all=[...issues,...signals];
    emptyState.classList.add('hidden'); reviewResults.classList.remove('hidden');
    findings.innerHTML=all.length?all.map(renderFinding).join(''):`<div class="finding info"><div class="finding-line">CLEAR</div><div><div class="finding-title">No immediate issues found</div><div class="finding-text">The static checks passed. Continue with tests and a deeper security review before shipping.</div></div></div>`;
    const hits=data.knowledge||[];
    guidance.innerHTML=(hits.length?hits:guidanceData.slice(0,2).map(x=>({title:x.title,text:x.text}))).map(x=>`<div class="guidance-card"><strong>${x.title}</strong><p>${x.text}</p></div>`).join('');
    const hasError=issues.length>0, hasWarn=signals.length>0;
    statusChip.className=`status-chip ${hasError?'fail':hasWarn?'warn':'success'}`; statusChip.textContent=hasError?'ACTION NEEDED':hasWarn?'REVIEW SIGNALS':'VALIDATED';
    summaryIcon.className=`summary-icon ${hasError?'fail':hasWarn?'warn':''}`; summaryIcon.textContent=hasError?'!':hasWarn?'~':'✓';
    summaryTitle.textContent=hasError?'Validation needs attention':hasWarn?'Valid, with security signals':'Ready for the next stage';
    summaryCopy.textContent=hasError?`${issues.length} validation issue${issues.length>1?'s':''} found. Fix syntax before deeper analysis.`:hasWarn?`${signals.length} security signal${signals.length>1?'s':''} found. Review the guidance below.`:'Syntax and structural checks passed. Grounded guidance is ready below.';
  } catch(error) {
    emptyState.classList.add('hidden'); reviewResults.classList.remove('hidden'); statusChip.className='status-chip fail'; statusChip.textContent='API ERROR'; summaryIcon.className='summary-icon fail'; summaryIcon.textContent='!'; summaryTitle.textContent='Review service unavailable'; summaryCopy.textContent=error.message; findings.innerHTML=''; guidance.innerHTML='';
  } finally { submit.disabled=false; submit.textContent='Submit Code'; }
}
input.addEventListener('input',updateEditorMeta); language.addEventListener('change',setLanguage); submit.addEventListener('click',runReview); loadExample.addEventListener('click',()=>{input.value=examples[language.value];updateEditorMeta();runReview();}); input.addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();const start=input.selectionStart;input.value=input.value.slice(0,start)+'    '+input.value.slice(input.selectionEnd);input.selectionStart=input.selectionEnd=start+4;updateEditorMeta();}}); updateEditorMeta(); setLanguage();
