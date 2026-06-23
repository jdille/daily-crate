const state = { data:null, archive:null, saves:{items:{}}, listens:{items:{}}, rows:[], queue:[], queueIndex:-1, current:null, autoNext:true, listenMarkUrl:null };
const $ = s => document.querySelector(s);
const esc = s => String(s || '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const norm = s => String(s || '').toLowerCase();
const date10 = s => (s || '').slice(0,10);
const STORE_KEY = 'daily-crate-state-v1';

function fmtDur(sec) { sec = Math.floor(Number(sec || 0)); if (!sec) return ''; const m = Math.floor(sec/60), r = String(sec % 60).padStart(2,'0'); return `${m}:${r}`; }
function fmtAddedDate(d) {
  const m = String(d || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return d || '';
  const dt = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  const weekday = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][dt.getUTCDay()];
  return `${weekday} ${Number(m[2])}/${Number(m[3])}`;
}
function label(r) { return [r.artist, r.title, r.release, r.source_subject, r.source_from, ...(r.reasons||[])].join(' ').toLowerCase(); }
function rowKey(r) { return r?.key || r?.url || ''; }
function isSaved(r) { return !!(state.saves.items || {})[rowKey(r)]; }
function isListened(r) { return !!(state.listens.items || {})[rowKey(r)]; }
function rowDate(r) { return date10(r.first_seen_at || r.pull_date || r.last_seen_at || r.source_date); }
function loadLocalState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE_KEY) || '{}');
    state.saves = saved.saves || {items:{}};
    state.listens = saved.listens || {items:{}};
  } catch { state.saves = {items:{}}; state.listens = {items:{}}; }
}
function saveLocalState() { localStorage.setItem(STORE_KEY, JSON.stringify({saves:state.saves, listens:state.listens, exported_at:new Date().toISOString()})); }
function allRows() {
  if ($('#mode').value === 'archive') return Object.values((state.archive || {}).items || {});
  if ($('#mode').value === 'saved') return Object.values((state.saves || {}).items || {});
  return (state.data && state.data.rows) || [];
}
function populateTags() {
  const sourceRows = Object.values((state.archive || {}).items || {}).concat((state.data?.rows || []));
  const tags = [...new Set(sourceRows.flatMap(r => r.reasons || []))].sort((a,b)=>a.localeCompare(b));
  $('#tag').innerHTML = '<option value="">all tags</option>' + tags.map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('');
}
function applyFilters() {
  let rows = allRows().slice();
  const q = norm($('#q').value), tag = $('#tag').value, d = $('#date').value, minScore = Number($('#minScore').value || 0);
  if (q) rows = rows.filter(r => label(r).includes(q));
  if (tag) rows = rows.filter(r => (r.reasons || []).includes(tag));
  if (d) rows = rows.filter(r => rowDate(r) === d || (r.pull_dates || []).includes(d));
  if (minScore) rows = rows.filter(r => Number(r.score || r.best_score || 0) >= minScore);
  const sort = $('#sort').value;
  if (sort === 'score') rows.sort((a,b)=>(Number(b.best_score || b.score || 0)-Number(a.best_score || a.score || 0)) || label(a).localeCompare(label(b)));
  if (sort === 'artist') rows.sort((a,b)=>String(a.artist||'').localeCompare(String(b.artist||'')) || String(a.title||'').localeCompare(String(b.title||'')));
  if (sort === 'duration') rows.sort((a,b)=>Number(b.duration||0)-Number(a.duration||0));
  if (sort === 'page' && $('#mode').value !== 'latest') rows.sort((a,b)=>String(b.first_seen_at || b.last_seen_at || '').localeCompare(String(a.first_seen_at || a.last_seen_at || '')) || Number(b.best_score||b.score||0)-Number(a.best_score||a.score||0));
  return rows;
}
function buildQueue(rows) { state.queue = rows.filter(r => r.stream_url || r.embed_url); if (state.queueIndex >= state.queue.length) state.queueIndex = -1; updateQueueStatus(); }
function updateQueueStatus() { $('#queueStatus').textContent = `queue: ${state.queueIndex >= 0 ? state.queueIndex + 1 : 0}/${state.queue.length}`; $('#autoNext').textContent = `auto-play next: ${state.autoNext ? 'on' : 'off'}`; $('#autoNext').classList.toggle('active', state.autoNext); }
function setPlayerArtwork(r) {
  const art = $('#playerArt');
  const artworkUrl = r?.artwork_url || '';
  if (!artworkUrl) {
    art.removeAttribute('src');
    art.alt = 'no album artwork available';
    art.hidden = true;
    return;
  }
  if (art.getAttribute('src') !== artworkUrl) art.src = artworkUrl;
  const title = r.title || r.release || 'track';
  const artist = r.artist || r.label_artist || '';
  art.alt = `album artwork for ${title}${artist ? ' by ' + artist : ''}`;
  art.hidden = false;
}
function updatePlayingHighlight() {
  document.querySelectorAll('#rows tr.playing').forEach(tr => tr.classList.remove('playing'));
  if (!state.current) return;
  const tr = document.querySelector(`#rows tr[data-key="${CSS.escape(rowKey(state.current))}"]`);
  if (tr) tr.classList.add('playing');
}
function render() {
  const rows = applyFilters(); state.rows = rows; buildQueue(rows); $('#empty').hidden = rows.length !== 0;
  $('#rows').innerHTML = rows.map((r, i) => {
    const score = r.best_score || r.score || 0, tags = (r.reasons || []).slice(0,5).map(t=>`<span class="pill">${esc(t)}</span>`).join('');
    const saved = isSaved(r), listened = isListened(r), d = rowDate(r);
    return `<tr data-key="${esc(rowKey(r))}" class="${state.current && rowKey(state.current) === rowKey(r) ? 'playing' : ''} ${listened ? 'listened' : ''}">
      <td class="score">${esc(score)}</td><td class="date" title="${esc(d)}">${esc(fmtAddedDate(d))}</td>
      <td class="artist" title="${esc(r.artist)}">${esc(r.artist || r.label_artist || '')}</td>
      <td><div class="title" title="${esc(r.title)}">${esc(r.title || r.release || 'untitled')} ${r.duration ? `<span class="source">${fmtDur(r.duration)}</span>` : ''}${listened ? '<span class="heard-pill">heard ✓</span>' : ''}</div><details><summary>details</summary><div class="detail">${esc(r.snippet || '')}<br><a href="${esc(r.url)}" target="_blank" rel="noopener">open Bandcamp</a></div></details></td>
      <td class="release hide-sm" title="${esc(r.release)}">${esc(r.release || '')}</td><td class="tags hide-sm">${tags}</td><td class="source hide-sm" title="${esc(r.source_subject)}">${esc(r.source_subject || '')}</td>
      <td><div class="row-actions"><button data-load="${i}">${r.stream_url ? 'load' : (r.embed_url ? 'iframe' : 'open')}</button><button class="heard ${listened ? 'heard-on' : ''}" data-heard="${i}">${listened ? 'heard ✓' : 'mark heard'}</button><button class="save ${saved ? 'saved' : ''}" data-save="${i}">${saved ? 'saved ✓' : 'save'}</button></div></td>
    </tr>`;
  }).join('');
  $('#summary').textContent = `${state.data?.summary || ''} Showing ${rows.length} rows. ${state.archive?.summary || ''}`;
}
function toggleSave(row) {
  const key = rowKey(row); if (!key) return;
  if (isSaved(row)) delete state.saves.items[key]; else state.saves.items[key] = {...row, saved_at:new Date().toISOString(), status:'saved'};
  saveLocalState(); render();
}
function toggleListened(row, force=false) {
  const key = rowKey(row); if (!key) return;
  if (!force && isListened(row)) delete state.listens.items[key]; else state.listens.items[key] = {...row, listened_at:state.listens.items[key]?.listened_at || new Date().toISOString(), status:'listened'};
  saveLocalState(); render();
}
function maybeAutoMarkListened() {
  const audio = $('#audio'), r = state.current;
  if (!r || !r.stream_url || isListened(r) || state.listenMarkUrl === rowKey(r)) return;
  const dur = Number(audio.duration || r.duration || 0);
  if (!dur || audio.currentTime < Math.min(45, dur * 0.55)) return;
  state.listenMarkUrl = rowKey(r); toggleListened(r, true);
}
function loadQueueAt(idx, auto=false) {
  if (!state.queue.length) return;
  if (idx >= state.queue.length) idx = 0; if (idx < 0) idx = state.queue.length - 1;
  const r = state.queue[idx]; state.queueIndex = idx; state.current = r; state.listenMarkUrl = null;
  setPlayerArtwork(r);
  $('#playerTitle').textContent = `${auto ? 'auto-playing' : 'loaded'}: ${r.title || r.release || 'track'}${r.artist ? ' — ' + r.artist : ''}`;
  $('#playerSub').textContent = `${r.release || ''} ${r.source_subject ? '· ' + r.source_subject : ''}`;
  updateQueueStatus();
  const audio = $('#audio'), iframe = $('#fallbackPlayer');
  if (r.stream_url) { iframe.style.display = 'none'; audio.style.display = ''; if (audio.src !== r.stream_url) audio.src = r.stream_url; audio.play().catch(() => { $('#playerSub').textContent = 'browser blocked autoplay — click play once in the audio control'; }); }
  else if (r.embed_url) { audio.pause(); audio.removeAttribute('src'); audio.load(); audio.style.display = 'none'; iframe.style.display = 'block'; iframe.src = r.embed_url; $('#playerSub').textContent = 'Bandcamp iframe fallback — press play inside the embedded player'; }
  updatePlayingHighlight(); $('#playerBox').scrollIntoView({block:'nearest', behavior:'smooth'});
}
function loadRowAt(rowIndex) {
  const row = state.rows[rowIndex]; if (!row) return;
  const idx = state.queue.findIndex(q => rowKey(q) === rowKey(row));
  if (idx >= 0) return loadQueueAt(idx);
  $('#playerTitle').textContent = `not playable here: ${row.title || row.release || 'track'}`;
  setPlayerArtwork(row);
  $('#playerSub').innerHTML = row.url ? `<a href="${esc(row.url)}" target="_blank" rel="noopener">open on Bandcamp</a>` : 'no stream or embed found for this row';
}
function exportState() {
  const blob = new Blob([JSON.stringify({saves:state.saves, listens:state.listens, exported_at:new Date().toISOString()}, null, 2)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'daily-crate-saves.json'; a.click(); URL.revokeObjectURL(a.href);
}
async function importState(file) {
  const imported = JSON.parse(await file.text());
  state.saves = imported.saves || state.saves; state.listens = imported.listens || state.listens; saveLocalState(); render();
}
async function init() {
  loadLocalState(); const ts = Date.now();
  const dataRes = await fetch('./data.json?ts=' + ts); state.data = await dataRes.json();
  if (state.data?.site?.title) { document.title = state.data.site.title; $('#siteTitle').textContent = state.data.site.title; }
  state.archive = {items:{}, snapshots:[], summary:'archive loading…'}; populateTags(); render();
  const archiveRes = await fetch('./archive.json?ts=' + ts).catch(()=>null); if (archiveRes && archiveRes.ok) state.archive = await archiveRes.json();
  populateTags(); render();
}
['q','mode','tag','sort','date','minScore'].forEach(id => $('#'+id).addEventListener('input', render));
$('#prevTrack').addEventListener('click', () => loadQueueAt(state.queueIndex < 0 ? 0 : state.queueIndex - 1));
$('#nextTrack').addEventListener('click', () => loadQueueAt(state.queueIndex < 0 ? 0 : state.queueIndex + 1));
$('#autoNext').addEventListener('click', () => { state.autoNext = !state.autoNext; updateQueueStatus(); });
$('#exportState').addEventListener('click', exportState);
$('#importState').addEventListener('change', e => { if (e.target.files[0]) importState(e.target.files[0]).catch(err => alert('import failed: ' + err.message)); });
$('#audio').addEventListener('timeupdate', maybeAutoMarkListened);
$('#audio').addEventListener('ended', () => { if (state.autoNext) loadQueueAt(state.queueIndex + 1, true); });
$('#rows').addEventListener('click', e => {
  const load = e.target.closest('[data-load]'); if (load) return loadRowAt(Number(load.dataset.load));
  const save = e.target.closest('[data-save]'); if (save) return toggleSave(state.rows[Number(save.dataset.save)]);
  const heard = e.target.closest('[data-heard]'); if (heard) return toggleListened(state.rows[Number(heard.dataset.heard)]);
});
document.addEventListener('keydown', e => {
  if (e.target.matches('input, textarea, select')) return;
  if (e.key === 'n' || e.key === 'ArrowRight') { e.preventDefault(); return loadQueueAt(state.queueIndex < 0 ? 0 : state.queueIndex + 1); }
  if (e.key === 'p' || e.key === 'ArrowLeft') { e.preventDefault(); return loadQueueAt(state.queueIndex < 0 ? 0 : state.queueIndex - 1); }
  if (e.key === 's' && state.current) { e.preventDefault(); return toggleSave(state.current); }
  if (e.key === 'h' && state.current) { e.preventDefault(); return toggleListened(state.current); }
  if (e.key === '0') { e.preventDefault(); $('#playerBox').scrollIntoView({block:'start', behavior:'smooth'}); $('#audio').focus(); }
});
init().catch(err => { $('#summary').textContent = 'failed to load crate: ' + err.message; });
