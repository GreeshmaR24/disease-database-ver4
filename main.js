/* ============================================================
   BioBase — Main JavaScript
   Handles: search, charts, bookmarks, compare, UI helpers
   ============================================================ */

"use strict";

/* ── Utility ────────────────────────────────────────────────── */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function debounce(fn, ms = 300) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

function categoryIcon(cat = "") {
  const icons = {
    genetic: "🧬",
    neurological: "🧠",
    cancer: "🎗️",
    metabolic: "⚗️",
    cardiovascular: "❤️",
  };
  return icons[cat.toLowerCase()] || "🔬";
}

function categoryClass(cat = "") {
  return cat.toLowerCase().replace(/\s+/g, "") || "default";
}

function truncate(str, n = 120) {
  return str && str.length > n ? str.slice(0, n) + "…" : str;
}

/* ── Active Nav ─────────────────────────────────────────────── */
(function highlightNav() {
  const path = window.location.pathname;
  $$(".nav-link").forEach(a => {
    const href = a.getAttribute("href");
    if (href === path || (href !== "/" && path.startsWith(href))) {
      a.classList.add("active");
    }
  });
})();

/* ── Hero Search (redirects to /search) ──────────────────────── */
const heroForm = $(".hero-search");
if (heroForm) {
  heroForm.addEventListener("submit", e => {
    e.preventDefault();
    const q = heroForm.querySelector("input").value.trim();
    if (q) window.location.href = `/search?q=${encodeURIComponent(q)}`;
  });
}

/* ── Smart Search Page ──────────────────────────────────────── */
const searchInput = $("#search-input");
if (searchInput) {
  // Pre-fill from URL params
  const urlQ = new URLSearchParams(window.location.search).get("q");
  if (urlQ) {
    searchInput.value = urlQ;
    performSearch(urlQ);
  }

  searchInput.addEventListener("input", debounce(e => {
    const q = e.target.value.trim();
    if (q.length >= 2) performSearch(q);
    else clearResults();
  }, 350));

  searchInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      const q = e.target.value.trim();
      if (q) performSearch(q);
    }
  });
}

async function performSearch(query) {
  showSpinner();
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    renderSearchResults(data);
  } catch (err) {
    console.error("Search error:", err);
    showSearchError();
  }
}

function showSpinner() {
  const container = $("#results-container");
  if (container) container.innerHTML = '<div class="loading-spinner"></div>';
}

function clearResults() {
  const container = $("#results-container");
  if (container) container.innerHTML = "";
}

function showSearchError() {
  const container = $("#results-container");
  if (container) container.innerHTML = `
    <div class="empty-state">
      <div class="icon">⚠️</div>
      <p>Something went wrong. Please try again.</p>
    </div>`;
}

function renderSearchResults(data) {
  const container = $("#results-container");
  if (!container) return;

  let html = "";

  // "Did you mean?" suggestions
  if (data.suggestions && data.suggestions.length > 0) {
    const sug = data.suggestions.map(s =>
      `<strong onclick="document.getElementById('search-input').value='${s}';performSearch('${s}')">${s}</strong>`
    ).join(" &nbsp;·&nbsp; ");
    html += `<p class="did-you-mean">🔍 Did you mean: ${sug}</p>`;
  }

  // AI suggestions panel
  if (data.ai_matches && data.ai_matches.length > 0) {
    html += `
      <div class="ai-panel">
        <div class="ai-panel-title">🤖 AI Symptom Analysis — Possible Matches</div>
        ${data.ai_matches.map(m => `
          <div class="ai-match-item" onclick="window.location='/disease/${m.id}'">
            <div>
              <div class="ai-match-name">${m.name}</div>
              <div style="font-size:.8rem;color:var(--slate-500)">${m.category}</div>
            </div>
            <span class="ai-score">Relevance: ${m.match_score}</span>
          </div>
        `).join("")}
        <p style="font-size:.75rem;color:var(--blue-600);margin-top:.5rem">
          ℹ️ AI uses rule-based NLP: symptom tokenisation + knowledge-base scoring
        </p>
      </div>`;
  }

  // Disease results
  if (data.diseases && data.diseases.length > 0) {
    html += `<div class="results-section">
      <div class="results-heading">🧾 Diseases (${data.diseases.length})</div>
      ${data.diseases.map(d => {
        const genes = JSON.parse(d.genes || "[]").slice(0, 3).join(", ");
        return `
          <div class="result-item" onclick="window.location='/disease/${d.id}'">
            <div>
              <div class="result-name">${d.name}</div>
              <div class="result-meta">${d.category}${genes ? " · Genes: " + genes : ""}</div>
            </div>
            <span class="cat-badge ${categoryClass(d.category)}">${d.category}</span>
          </div>`;
      }).join("")}
    </div>`;
  }

  // Biomarker results
  if (data.biomarkers && data.biomarkers.length > 0) {
    html += `<div class="results-section">
      <div class="results-heading">🎗️ Biomarkers (${data.biomarkers.length})</div>
      ${data.biomarkers.map(b => `
        <div class="result-item" onclick="window.location='/biomarkers'">
          <div>
            <div class="result-name">${b.name}</div>
            <div class="result-meta">${b.cancer_type} · ${b.gene_protein}</div>
          </div>
          <span class="cat-badge cancer">${b.relevance}</span>
        </div>
      `).join("")}
    </div>`;
  }

  // No results
  if ((!data.diseases || data.diseases.length === 0) &&
      (!data.biomarkers || data.biomarkers.length === 0) &&
      (!data.ai_matches || data.ai_matches.length === 0)) {
    html = `
      <div class="empty-state">
        <div class="icon">🔬</div>
        <p>No results found for "<strong>${data.query}</strong>".<br>
        Try searching by symptom (e.g. "tremor"), gene (e.g. "BRCA1"), or disease name.</p>
      </div>`;
  }

  container.innerHTML = html;
}

/* ── Bookmark Toggle ─────────────────────────────────────────── */
window.toggleBookmark = async function(diseaseId) {
  const btn = $("#bookmark-btn");
  if (!btn) return;
  try {
    const res = await fetch(`/api/bookmark/${diseaseId}`, { method: "POST" });
    const data = await res.json();
    if (data.action === "added") {
      btn.classList.add("bookmarked");
      btn.innerHTML = "⭐ Bookmarked";
    } else {
      btn.classList.remove("bookmarked");
      btn.innerHTML = "☆ Bookmark";
    }
  } catch (err) {
    console.error("Bookmark error:", err);
  }
};

/* ── Disease Compare ─────────────────────────────────────────── */
const compareBtn = $("#compare-btn");
if (compareBtn) {
  compareBtn.addEventListener("click", async () => {
    const s1 = $("#sel1");
    const s2 = $("#sel2");
    if (!s1 || !s2) return;
    const id1 = s1.value, id2 = s2.value;
    if (!id1 || !id2) { alert("Please select two diseases to compare."); return; }
    if (id1 === id2) { alert("Please select two different diseases."); return; }

    compareBtn.textContent = "Loading…";
    try {
      const res = await fetch(`/api/compare?id=${id1}&id=${id2}`);
      const diseases = await res.json();
      renderCompareTable(diseases);
    } catch (err) {
      console.error(err);
    } finally {
      compareBtn.textContent = "Compare";
    }
  });
}

function renderCompareTable(diseases) {
  const wrap = $("#compare-result");
  if (!wrap || diseases.length < 2) return;

  const [a, b] = diseases;
  const rows = [
    ["Category", a.category, b.category],
    ["Inheritance", a.inheritance, b.inheritance],
    ["Prevalence", a.prevalence, b.prevalence],
    ["Genes Involved", JSON.parse(a.genes||"[]").join(", "), JSON.parse(b.genes||"[]").join(", ")],
    ["Proteins", JSON.parse(a.proteins||"[]").slice(0,2).join("; "), JSON.parse(b.proteins||"[]").slice(0,2).join("; ")],
    ["Symptoms", JSON.parse(a.symptoms||"[]").slice(0,3).join("; "), JSON.parse(b.symptoms||"[]").slice(0,3).join("; ")],
    ["Diagnosis", truncate(a.diagnosis, 140), truncate(b.diagnosis, 140)],
    ["Treatment", truncate(a.treatment, 140), truncate(b.treatment, 140)],
    ["OMIM ID", a.omim_id, b.omim_id],
  ];

  wrap.innerHTML = `
    <div class="compare-table-wrap">
      <table class="compare-table">
        <thead>
          <tr>
            <th>Attribute</th>
            <th>${a.name}</th>
            <th>${b.name}</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(([label, va, vb]) => `
            <tr>
              <td>${label}</td>
              <td>${va || "—"}</td>
              <td>${vb || "—"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>`;
}

/* ── Category Filter (Diseases page) ─────────────────────────── */
$$(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const cat = btn.dataset.cat || "";
    window.location.href = cat ? `/diseases?category=${encodeURIComponent(cat)}` : "/diseases";
  });
});

/* ── Charts (Home Page) ──────────────────────────────────────── */
async function initCharts() {
  const catCtx = $("#cat-chart");
  const bmCtx  = $("#bm-chart");
  if (!catCtx && !bmCtx) return;

  // Load Chart.js dynamically
  if (typeof Chart === "undefined") {
    await loadScript("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
  }

  // Disease category distribution
  if (catCtx) {
    const diseases = await fetch("/api/diseases").then(r => r.json());
    const catCounts = {};
    diseases.forEach(d => { catCounts[d.category] = (catCounts[d.category] || 0) + 1; });
    new Chart(catCtx, {
      type: "doughnut",
      data: {
        labels: Object.keys(catCounts),
        datasets: [{
          data: Object.values(catCounts),
          backgroundColor: ["#2563eb","#8b5cf6","#ef4444","#10b981","#f59e0b","#06b6d4"],
          borderWidth: 2,
          borderColor: "#fff",
        }]
      },
      options: {
        plugins: {
          legend: { position: "bottom", labels: { font: { family: "'DM Sans'" }, padding: 12 } }
        },
        cutout: "62%"
      }
    });
  }

  // Biomarker relevance distribution
  if (bmCtx) {
    const bms = await fetch("/api/biomarkers").then(r => r.json());
    const relCounts = {};
    bms.forEach(b => {
      b.relevance.split(" and ").forEach(r => {
        r = r.trim();
        relCounts[r] = (relCounts[r] || 0) + 1;
      });
    });
    new Chart(bmCtx, {
      type: "bar",
      data: {
        labels: Object.keys(relCounts),
        datasets: [{
          label: "Count",
          data: Object.values(relCounts),
          backgroundColor: "#3b82f6",
          borderRadius: 6,
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: "#f1f5f9" } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

initCharts();

/* ── Smooth card entrance (IntersectionObserver) ─────────────── */
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  $$(".disease-card, .bm-card, .detail-card").forEach(el => {
    observer.observe(el);
  });
}
