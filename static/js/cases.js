let allCases = [];

const grid         = document.getElementById("cases-grid");
const overlay      = document.getElementById("modal-overlay");
const modalContent = document.getElementById("modal-content");

// ── 載入個案（預設排除 moa 收容所資料）────────────────────
async function loadCases() {
  const status = document.getElementById("filter-status").value;
  const animal = document.getElementById("filter-animal").value;
  const source = document.getElementById("filter-source").value;

  let url = "/api/cases?";
  if (status) url += `status=${status}&`;
  if (animal) url += `animal_type=${encodeURIComponent(animal)}&`;
  if (source) {
    url += `source=${source}&`;
  } else {
    // 沒有選來源時，同時撈 user 和 ptt（排除 moa）
    url += `source=user&`;
  }

  grid.innerHTML = '<div class="loading-spinner">載入中...</div>';
  let res   = await fetch(url, { credentials: "include" });
  let cases = await res.json();

  // 如果沒選來源，再撈一次 ptt 合併
  if (!source) {
    const url2  = url.replace("source=user&", "source=ptt&");
    const res2  = await fetch(url2, { credentials: "include" });
    const ptt   = await res2.json();
    cases = [...cases, ...ptt];
    // 依時間重新排序
    cases.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  allCases = cases;
  renderGrid(allCases);
}

function sourceLabel(s) {
  return { user: "使用者回報", ptt: "PTT" }[s] || s;
}
function sourceBadge(s) {
  const cls = { user: "badge-user", ptt: "badge-ptt" }[s] || "";
  return `<span class="badge ${cls}">${sourceLabel(s)}</span>`;
}
function statusBadge(s) {
  return s === "handled"
    ? '<span class="badge badge-handled">✅ 已處理</span>'
    : '<span class="badge badge-open">🔴 待處理</span>';
}
function animalEmoji(t) {
  return { "狗": "🐶", "貓": "🐱" }[t] || "🐾";
}

// ── 渲染卡片 ──────────────────────────────────────────────
function renderGrid(cases) {
  if (!cases.length) {
    grid.innerHTML = '<p class="empty-msg">目前沒有符合條件的個案</p>';
    return;
  }
  grid.innerHTML = cases.map(c => `
    <div class="case-card ${c.status === 'handled' ? 'card-handled' : ''}"
         data-id="${c.id}" onclick="openModal(${c.id})">
      ${c.image_url ? `<img class="case-img" src="${c.image_url}" alt="">` : ""}
      <div class="case-body">
        <div class="case-badges">
          ${statusBadge(c.status)}
          ${sourceBadge(c.source)}
          <span class="animal-tag">${animalEmoji(c.animal_type)} ${c.animal_type}</span>
        </div>
        <h3 class="case-title">${c.title}</h3>
        ${c.location ? `<p class="case-location">📍 ${c.location}</p>` : ""}
        <p class="case-time">${c.created_at}</p>
      </div>
    </div>
  `).join("");
}

// ── 開啟詳情 Modal ────────────────────────────────────────
async function openModal(id) {
  overlay.style.display = "flex";
  modalContent.innerHTML = '<div class="loading-spinner">載入中...</div>';

  const res  = await fetch(`/api/cases/${id}`, { credentials: "include" });
  const data = await res.json();
  const c    = data.case;
  const notes = data.notes;
  const user = window._currentUser;

  const handleBtn = user
    ? c.status === "open"
      ? `<button class="btn-handle" onclick="handleCase(${c.id})">✅ 標記已處理</button>`
      : `<button class="btn-reopen" onclick="reopenCase(${c.id})">🔄 重新開啟</button>`
    : "";

  const pttLink = c.source === "ptt" && c.source_url
    ? `<a href="${c.source_url}" target="_blank" class="btn-outline-sm">前往 PTT 原文</a>` : "";

  const notesHtml = notes.length
    ? notes.map(n => `
        <div class="note-item">
          <span class="note-user">${n.username || n.display_name || "匿名"}</span>
          <span class="note-time">${n.created_at}</span>
          <p class="note-text">${n.note}</p>
        </div>`).join("")
    : '<p class="empty-msg">尚無筆記</p>';

  const noteForm = user ? `
    <div class="note-form">
      <textarea id="note-input" placeholder="新增筆記..." rows="2"></textarea>
      <button class="btn-primary-sm" onclick="addNote(${c.id})">送出筆記</button>
    </div>` : "";

  modalContent.innerHTML = `
    <div class="modal-badges">
      ${statusBadge(c.status)} ${sourceBadge(c.source)}
      <span class="animal-tag">${animalEmoji(c.animal_type)} ${c.animal_type}</span>
    </div>
    <h2 class="modal-title">${c.title}</h2>
    ${c.image_url ? `<img class="modal-img" src="${c.image_url}" alt="">` : ""}
    ${c.location ? `<p class="modal-location">📍 ${c.location}</p>` : ""}
    ${c.description ? `<p class="modal-desc">${c.description.replace(/\n/g,'<br>')}</p>` : ""}
    <p class="modal-meta">回報時間：${c.created_at}　｜　回報者：${c.username || c.display_name || "匿名"}</p>
    ${c.status === "handled" ? `<p class="modal-meta handled-by">已處理於 ${c.handled_at}</p>` : ""}
    <div class="modal-actions">${handleBtn} ${pttLink}</div>
    <hr class="divider-line">
    <h3>處理筆記</h3>
    ${notesHtml}
    ${noteForm}
  `;
}

async function handleCase(id) {
  await fetch(`/api/cases/${id}/handle`, { method: "POST", credentials: "include" });
  openModal(id);
  loadCases();
}
async function reopenCase(id) {
  await fetch(`/api/cases/${id}/reopen`, { method: "POST", credentials: "include" });
  openModal(id);
  loadCases();
}
async function addNote(id) {
  const note = document.getElementById("note-input").value.trim();
  if (!note) return;
  await fetch(`/api/cases/${id}/notes`, {
    method: "POST", credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  openModal(id);
}

document.getElementById("modal-close").onclick = () => overlay.style.display = "none";
overlay.onclick = (e) => { if (e.target === overlay) overlay.style.display = "none"; };

["filter-status", "filter-animal", "filter-source"].forEach(id => {
  document.getElementById(id)?.addEventListener("change", loadCases);
});

loadCases();
