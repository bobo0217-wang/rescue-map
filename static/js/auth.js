const errMsg = document.getElementById("err-msg");
const okMsg  = document.getElementById("ok-msg");

function showErr(msg) {
  if (!errMsg) return;
  errMsg.textContent = msg;
  errMsg.style.display = "block";
  if (okMsg) okMsg.style.display = "none";
}
function showOk(msg) {
  if (!okMsg) return;
  okMsg.textContent = msg;
  okMsg.style.display = "block";
  if (errMsg) errMsg.style.display = "none";
}

// ── 登入 ──────────────────────────────────────────────────
const btnLogin = document.getElementById("btn-login");
if (btnLogin) {
  async function doLogin() {
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    if (!email || !password) return showErr("請填寫 Email 和密碼");

    btnLogin.disabled = true;
    btnLogin.textContent = "登入中...";

    try {
      const res  = await fetch("/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        // 跳轉前先確認 session 真的有了
        const check = await fetch("/auth/me", { credentials: "include" });
        const me    = await check.json();
        if (me.logged_in) {
          window.location.replace("/cases");
        } else {
          showErr("登入異常，請重試");
          btnLogin.disabled = false;
          btnLogin.textContent = "登入";
        }
      } else {
        showErr(data.error || "帳號或密碼錯誤");
        btnLogin.disabled = false;
        btnLogin.textContent = "登入";
      }
    } catch (e) {
      showErr("網路錯誤，請稍後再試");
      btnLogin.disabled = false;
      btnLogin.textContent = "登入";
    }
  }

  btnLogin.addEventListener("click", doLogin);
  document.getElementById("password")?.addEventListener("keydown", e => {
    if (e.key === "Enter") doLogin();
  });
}

// ── 註冊 ──────────────────────────────────────────────────
const btnRegister = document.getElementById("btn-register");
if (btnRegister) {
  btnRegister.addEventListener("click", async () => {
    const username = document.getElementById("username")?.value.trim();
    const email    = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;
    if (!username || !email || !password) return showErr("請填寫所有欄位");
    if (password.length < 6) return showErr("密碼至少 6 個字元");

    btnRegister.disabled = true;
    btnRegister.textContent = "註冊中...";

    try {
      const res  = await fetch("/auth/register", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        showOk("✅ 註冊成功！請使用剛才的帳號密碼登入");
        // 清空欄位
        document.getElementById("username").value = "";
        document.getElementById("email").value = "";
        document.getElementById("password").value = "";
        // 2 秒後跳轉到登入頁
        setTimeout(() => { window.location.replace("/login"); }, 2000);
      } else {
        showErr(data.error || "註冊失敗");
        btnRegister.disabled = false;
        btnRegister.textContent = "註冊";
      }
    } catch (e) {
      showErr("網路錯誤，請稍後再試");
      btnRegister.disabled = false;
      btnRegister.textContent = "註冊";
    }
  });
}
