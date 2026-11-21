let reviewId = null;
const $ = (id) => document.getElementById(id);
const code = $('code');
$('fileInput').addEventListener('change', async (e) => { const file = e.target.files[0]; if (!file) return; $('filename').value = file.name; $('language').value = file.name.endsWith('.java') ? 'java' : 'python'; code.value = await file.text(); });
$('analyze').addEventListener('click', async () => {
  $('status').textContent = 'Running Code Analysis + Security agents in parallel…'; $('analyze').disabled = true;
  try {
    const res = await fetch('/api/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({language:$('language').value, filename:$('filename').value, code:code.value})});
    const data = await res.json(); if (!res.ok) throw new Error(data.detail?.errors?.join(' ') || data.detail || 'Analysis failed');
    reviewId = data.review.id; renderReview(data.review); $('status').textContent = `Review ${reviewId.slice(0,8)} complete.`;
    $('mdExport').href = `/api/reviews/${reviewId}/export?format=markdown`; $('pdfExport').href = `/api/reviews/${reviewId}/export?format=pdf`; $('reviewActions').classList.remove('hidden');
  } catch (err) { $('status').textContent = err.message; } finally { $('analyze').disabled = false; }
});
function renderReview(r) {
  $('empty').classList.add('hidden'); $('results').classList.remove('hidden');
  const s = r.summary; const counts = Object.entries(s.severity_breakdown).filter(([,v])=>v).map(([k,v])=>`<span class="count ${k}">${v} ${k}</span>`).join('');
  $('results').innerHTML = `<div class="score"><div class="score-number">${s.health_score}<small>/100</small></div><div><span class="kicker">CODE HEALTH</span><h3>${s.risk_level.toUpperCase()} RISK</h3><div class="counts">${counts || 'No findings'}</div></div></div><div class="summary-box"><strong>PR summary</strong><pre>${escapeHtml(r.pr_summary)}</pre></div><div class="finding-list">${r.findings.sort((a,b)=>b.score-a.score).map(f=>`<article class="finding"><div class="finding-top"><span class="sev ${f.severity}">${f.severity}</span><span class="finding-id">${f.id} · line ${f.line_start}</span></div><h3>${escapeHtml(f.title)}</h3><p>${escapeHtml(f.description)}</p><div class="fix"><strong>Remediation</strong><p>${escapeHtml(f.remediation)}</p><pre>${escapeHtml(f.corrected_code)}</pre></div><div class="refs">${f.owasp || 'Code quality'} · confidence ${Math.round(f.confidence*100)}%</div></article>`).join('')}</div>`;
}
$('ask').addEventListener('click', ask); $('question').addEventListener('keydown', e => {if(e.key==='Enter') ask();});
async function ask(){ const q=$('question').value.trim(); if(!q) return; $('answer').classList.remove('hidden'); $('answer').textContent='Retrieving grounded guidance…'; const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,review_id:reviewId})}); const data=await res.json(); $('answer').innerHTML=`<div>${escapeHtml(data.answer).replace(/\n/g,'<br>')}</div><small>Sources: ${data.sources.map(escapeHtml).join(' · ') || 'none'}</small>`; }
function escapeHtml(s){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
