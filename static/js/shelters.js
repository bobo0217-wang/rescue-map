const grid        = document.getElementById("shelters-grid");
const countEl     = document.getElementById("shelter-count");
const searchInput = document.getElementById("search-input");

let allShelters = [];

// ── 載入收容所（source=moa）────────────────────────────
async function loadShelters() {
  grid.innerHTML = '<div class="loading-spinner">載入中...</div>';
  const res = await fetch("/api/cases?source=moa", { credentials: "include" });
  allShelters = await res.json();
  renderShelters(allShelters);
}

// ── 解析收容所資訊 ────────────────────────────────────
function parseShelter(c) {
  // title 格式：【收容所】名稱 — 狗X隻 貓Y隻
  const nameMatch = c.title.match(/【收容所】(.+?)—/);
  const dogMatch  = c.title.match(/狗(\d+)隻/);
  const catMatch  = c.title.match(/貓(\d+)隻/);
  const name = nameMatch ? nameMatch[1].trim() : c.title;
  const dogs = dogMatch  ? parseInt(dogMatch[1]) : 0;
  const cats = catMatch  ? parseInt(catMatch[1]) : 0;

  // description 格式：地址：xxx\n電話：xxx
  const addrMatch = (c.description || "").match(/地址：(.+)/);
  const telMatch  = (c.description || "").match(/電話：(.+)/);
  const address   = addrMatch ? addrMatch[1].trim() : "";
  const tel       = telMatch  ? telMatch[1].trim()  : "";

  return { name, dogs, cats, address, tel, location: c.location };
}

// ── 渲染卡片 ──────────────────────────────────────────
function renderShelters(cases) {
  if (!cases.length) {
    grid.innerHTML = '<p class="empty-msg">目前沒有收容所資料</p>';
    countEl.textContent = "";
    return;
  }

  countEl.textContent = `共 ${cases.length} 間收容所`;

  grid.innerHTML = cases.map(c => {
    const s = parseShelter(c);
    return `
      <div class="shelter-card">
        <div class="shelter-header">
          <span class="shelter-icon">🏠</span>
          <div>
            <h3 class="shelter-name">${s.name}</h3>
            <p class="shelter-county">${s.location || ""}</p>
          </div>
        </div>
        <div class="shelter-body">
          ${s.address ? `
            <div class="shelter-row">
              <span class="shelter-label">📍 地址</span>
              <span>${s.address}</span>
            </div>` : ""}
          ${s.tel ? `
            <div class="shelter-row">
              <span class="shelter-label">📞 電話</span>
              <a href="tel:${s.tel}" class="shelter-tel">${s.tel}</a>
            </div>` : ""}
        </div>
        <div class="shelter-footer">
          <span class="count-badge badge-dog">🐶 ${s.dogs} 隻</span>
          <span class="count-badge badge-cat">🐱 ${s.cats} 隻</span>
        </div>
      </div>
    `;
  }).join("");
}

// ── 搜尋 ──────────────────────────────────────────────
searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim().toLowerCase();
  if (!q) {
    renderShelters(allShelters);
    return;
  }
  const filtered = allShelters.filter(c => {
    const s = parseShelter(c);
    return s.name.includes(q) || s.address.includes(q) || (c.location || "").includes(q);
  });
  renderShelters(filtered);
  countEl.textContent = `顯示 ${filtered.length} / ${allShelters.length} 間`;
});

loadShelters();
