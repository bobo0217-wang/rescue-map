const map = L.map("map-view").setView([23.6, 121.0], 8);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 18,
}).addTo(map);

let markers = [];
const caseList = document.getElementById("map-case-list");

function makeIcon(status, type) {
  const emoji  = { "狗": "🐶", "貓": "🐱" }[type] || "🐾";
  const border = status === "handled" ? "#aaa" : "#e63946";
  return L.divIcon({
    html: `<div style="width:32px;height:32px;border-radius:50%;background:#fff;
           border:2px solid ${border};box-shadow:0 2px 6px rgba(0,0,0,.25);
           display:flex;align-items:center;justify-content:center;font-size:16px;">${emoji}</div>`,
    iconSize: [32, 32], iconAnchor: [16, 16], popupAnchor: [0, -18], className: "",
  });
}

async function loadMapCases() {
  const status = document.getElementById("map-filter-status").value;
  const animal = document.getElementById("map-filter-animal").value;
  let url = "/api/cases?";
  if (status) url += `status=${status}&`;
  if (animal) url += `animal_type=${encodeURIComponent(animal)}&`;

  const res   = await fetch(url, { credentials: "include" });
  const cases = await res.json();

  markers.forEach(m => map.removeLayer(m));
  markers = [];
  caseList.innerHTML = "";

  const withCoord = cases.filter(c => c.lat && c.lng);

  withCoord.forEach(c => {
    const marker = L.marker([c.lat, c.lng], { icon: makeIcon(c.status, c.animal_type) });
    marker.bindPopup(`
      <div style="min-width:160px;">
        <strong>${c.title}</strong><br>
        <span style="font-size:12px;color:#666;">${c.location || ""}</span><br>
        <a href="#" onclick="event.preventDefault();showCaseSidebar(${c.id})"
           style="color:#1a6b4a;font-size:13px;">查看詳情</a>
      </div>`);
    marker.addTo(map);
    markers.push(marker);

    // 側邊欄清單
    const item = document.createElement("div");
    item.className = `map-case-item ${c.status === "handled" ? "item-handled" : ""}`;
    item.innerHTML = `
      <span class="item-emoji">${{ "狗": "🐶", "貓": "🐱" }[c.animal_type] || "🐾"}</span>
      <div class="item-info">
        <p class="item-title">${c.title}</p>
        <p class="item-loc">${c.location || "未知地點"}</p>
      </div>`;
    item.onclick = () => {
      map.setView([c.lat, c.lng], 14);
      marker.openPopup();
    };
    caseList.appendChild(item);
  });

  if (!withCoord.length) {
    caseList.innerHTML = '<p style="color:#999;padding:1rem;font-size:13px;">目前沒有有地點的個案</p>';
  }
}

["map-filter-status", "map-filter-animal"].forEach(id => {
  document.getElementById(id)?.addEventListener("change", loadMapCases);
});

loadMapCases();
