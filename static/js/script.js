/* ══════════════════════════════════════════════════════
   CampusEdge — Global JavaScript
   ══════════════════════════════════════════════════════ */

// ── TABS ────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const group = btn.closest("[data-tabs]");
      const target = btn.dataset.tab;
      group.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      group.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      group.querySelector(`[data-panel="${target}"]`)?.classList.add("active");
    });
  });
}

// ── MODALS ──────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove("open");
  document.body.style.overflow = "";
}

document.addEventListener("click", e => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("open");
    document.body.style.overflow = "";
  }
  if (e.target.classList.contains("modal-close")) {
    const modal = e.target.closest(".modal-overlay");
    if (modal) { modal.classList.remove("open"); document.body.style.overflow = ""; }
  }
});

// ── APPLY TO DRIVE ───────────────────────────────────────
async function applyDrive(driveId, btn) {
  btn.disabled = true; btn.textContent = "Applying...";
  const res = await fetch("/student/apply", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `drive_id=${driveId}`
  });
  const data = await res.json();
  if (data.success) {
    btn.textContent = "Applied ✓";
    btn.classList.remove("btn-teal");
    btn.classList.add("btn-ghost");
    showToast("Application submitted!", "success");
  } else {
    btn.textContent = data.error || "Error";
    btn.disabled = false;
    showToast(data.error || "Something went wrong", "error");
  }
}

// ── UPDATE APPLICATION STATUS (TPO) ─────────────────────
async function updateStatus(appId, newStatus, selectEl) {
  const res = await fetch("/tpo/update_application", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `app_id=${appId}&status=${newStatus}`
  });
  const data = await res.json();
  if (data.success) showToast(`Status updated to ${newStatus}`, "success");
  else showToast("Update failed", "error");
}

// ── REFERRAL ACTIONS (TPO) ───────────────────────────────
async function handleReferral(refId, action, btn) {
  btn.disabled = true;
  const res = await fetch("/tpo/approve_referral", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `ref_id=${refId}&action=${action}`
  });
  const data = await res.json();
  if (data.success) {
    const row = btn.closest("tr");
    if (row) row.remove();
    showToast(action === "approved" ? "Referral approved!" : "Referral rejected", action === "approved" ? "success" : "error");
  }
}

// ── SUBMIT REFERRAL (ALUMNI) ─────────────────────────────
async function submitReferral(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const body = new URLSearchParams(formData).toString();
  const res = await fetch("/alumni/submit_referral", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
  const data = await res.json();
  if (data.success) {
    closeModal("modal-referral");
    form.reset();
    showToast("Referral submitted for TPO review!", "success");
  }
}

// ── CREATE MENTORSHIP SESSION (ALUMNI) ───────────────────
async function createMentorSession(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const body = new URLSearchParams(formData).toString();
  const res = await fetch("/alumni/create_session", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
  const data = await res.json();
  if (data.success) {
    closeModal("modal-session");
    form.reset();
    showToast("Mentorship session created!", "success");
    setTimeout(() => location.reload(), 800);
  }
}

// ── BOOK SESSION (STUDENT) ───────────────────────────────
async function bookSession(sessionId, btn) {
  btn.disabled = true; btn.textContent = "Booking...";
  const res = await fetch("/student/book_session", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `session_id=${sessionId}`
  });
  const data = await res.json();
  if (data.success) {
    btn.textContent = "Booked ✓";
    btn.classList.add("btn-ghost");
    showToast("Session booked!", "success");
  }
}

// ── AI RESUME ANALYZER ───────────────────────────────────
async function analyzeResume() {
  const btn = document.getElementById("analyze-btn");
  const result = document.getElementById("ai-result");
  btn.disabled = true; btn.textContent = "Analyzing...";
  result.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text2)">
    <div class="spinner"></div><p style="margin-top:1rem;font-size:0.85rem;">AI is analyzing your resume…</p>
  </div>`;
  try {
    const res = await fetch("/student/analyze_resume", { method: "POST" });
    const data = await res.json();
    renderAIResult(data);
  } catch {
    result.innerHTML = `<p style="color:#f87171;font-size:0.85rem;">Analysis failed. Please try again.</p>`;
  }
  btn.disabled = false; btn.textContent = "Analyze Resume";
}

function renderAIResult(data) {
  const result = document.getElementById("ai-result");
  const miss = data.missing_skills.map(s => `<span class="skill-tag skill-miss">${s}</span>`).join("");
  const ok = data.existing_skills.map(s => `<span class="skill-tag skill-ok">${s} ✓</span>`).join("");
  const sugs = data.suggestions.map(s => `<li><span class="sug-icon">→</span>${s}</li>`).join("");
  result.innerHTML = `
    <div class="score-circle-wrap">
      <div class="score-circle" style="--pct:${data.score}">
        <span class="score-num">${data.score}</span>
      </div>
      <div class="score-bars">
        <div class="sbar-row">
          <div class="sbar-label"><span>Technical Skills</span><span>${data.technical_skills}/100</span></div>
          <div class="sbar-bg"><div class="sbar-fill" style="width:${data.technical_skills}%;background:linear-gradient(90deg,#7c3aed,#a78bfa)"></div></div>
        </div>
        <div class="sbar-row">
          <div class="sbar-label"><span>Project Relevance</span><span>${data.project_relevance}/100</span></div>
          <div class="sbar-bg"><div class="sbar-fill" style="width:${data.project_relevance}%;background:linear-gradient(90deg,#0f766e,#0d9488)"></div></div>
        </div>
        <div class="sbar-row">
          <div class="sbar-label"><span>Communication</span><span>${data.communication}/100</span></div>
          <div class="sbar-bg"><div class="sbar-fill" style="width:${data.communication}%;background:linear-gradient(90deg,#b45309,#d97706)"></div></div>
        </div>
      </div>
    </div>
    <div style="margin-bottom:1rem">
      <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:6px">Missing Skills</div>
      <div class="missing-skills">${miss}</div>
    </div>
    <div style="margin-bottom:1.25rem">
      <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:6px">Strengths</div>
      <div class="ok-skills">${ok}</div>
    </div>
    <div>
      <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:8px">Suggestions</div>
      <ul class="suggestion-list">${sugs}</ul>
    </div>`;
}

// ── TOAST ─────────────────────────────────────────────────
function showToast(msg, type = "success") {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const t = document.createElement("div");
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  t.style.cssText = `
    position:fixed;bottom:2rem;right:2rem;z-index:9999;
    padding:.7rem 1.2rem;border-radius:12px;font-size:.85rem;font-weight:500;
    background:${type === "success" ? "rgba(5,150,105,0.9)" : "rgba(220,38,38,0.9)"};
    color:#fff;backdrop-filter:blur(12px);
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
    animation:slideIn .3s ease;
  `;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

const style = document.createElement("style");
style.textContent = `
@keyframes slideIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.spinner { width:28px;height:28px;border:2px solid rgba(124,58,237,.2);border-top-color:#7c3aed;border-radius:50%;animation:spin 0.7s linear infinite;margin:0 auto; }
@keyframes spin { to { transform:rotate(360deg); } }
`;
document.head.appendChild(style);

// ── INIT ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  document.querySelectorAll("[data-open-modal]").forEach(el => {
    el.addEventListener("click", () => openModal(el.dataset.openModal));
  });
  // auto-dismiss flash after 4s
  document.querySelectorAll(".flash-msg").forEach(el => {
    setTimeout(() => el.style.opacity = "0", 4000);
    setTimeout(() => el.remove(), 4500);
  });
});
