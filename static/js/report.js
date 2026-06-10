// 檢查是否登入
(async () => {
  const res  = await fetch("/auth/me", { credentials: "include" });
  const data = await res.json();
  if (!data.logged_in) {
    window.location.href = "/login";
  }
})();

let selectedLat = null;
let selectedLng = null;
let pinMarker   = null;

// 初始化選點地圖
const reportMap = L.map("report-map").setView([23.6, 121.0], 8);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '© OpenStreetMap',
  maxZoom: 18,
}).addTo(reportMap);

reportMap.on("click", (e) => {
  selectedLat = e.latlng.lat;
  selectedLng = e.latlng.lng;
  document.getElementById("latlng-hint").textContent =
    `已標記：${selectedLat.toFixed(5)}, ${selectedLng.toFixed(5)}`;
  if (pinMarker) reportMap.removeLayer(pinMarker);
  pinMarker = L.marker([selectedLat, selectedLng]).addTo(reportMap);
});

// 送出回報
document.getElementById("btn-submit").addEventListener("click", async () => {
  const errMsg = document.getElementById("err-msg");
  const okMsg  = document.getElementById("ok-msg");
  errMsg.style.display = "none";
  okMsg.style.display  = "none";

  const title       = document.getElementById("title").value.trim();
  const description = document.getElementById("description").value.trim();
  const location    = document.getElementById("location-text").value.trim();
  const animal_type = document.getElementById("animal-type").value;
  const image_url   = document.getElementById("image-url").value.trim();

  if (!title) {
    errMsg.textContent = "請填寫標題";
    errMsg.style.display = "block";
    return;
  }

  const payload = {
    title, description, location, animal_type, image_url,
    lat: selectedLat,
    lng: selectedLng,
  };

  const res  = await fetch("/api/cases", {
    method: "POST", credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (res.ok) {
    okMsg.textContent = "✅ 回報成功！正在跳轉到個案清單...";
    okMsg.style.display = "block";
    setTimeout(() => window.location.href = "/cases", 1500);
  } else {
    errMsg.textContent = data.error || "送出失敗，請稍後再試";
    errMsg.style.display = "block";
  }
});
