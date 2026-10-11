/* ============================================================
   Sentima v1.0 – Application Controller & Dynamic UI Renderer
   ============================================================ */

let currentTab = "dashboard";
let globalOverview = null;
let globalReviews = [];
let globalIssues = [];
let doughnutChartInstance = null;
let barChartInstance = null;
let selectedStarRating = 4;

document.addEventListener("DOMContentLoaded", async () => {
  initFromHash();
  await checkSystemHealth();
  await loadAllData();
});

// Handle direct link hash e.g. #reviews, #improvements
function initFromHash() {
  const hash = window.location.hash.replace("#", "");
  if (["dashboard", "reviews", "improvements"].includes(hash)) {
    switchTab(hash);
  }
}

// Check Backend Engine Health
async function checkSystemHealth() {
  const health = await API.checkHealth();
  const dbPill = document.getElementById("dbStatusPill");
  const modalTitle = document.getElementById("dbModalEngineTitle");
  if (dbPill) {
    dbPill.textContent = health.database ? `${health.database} Ready` : "MySQL / SQLite Ready";
  }
  if (modalTitle) {
    modalTitle.textContent = `Active Engine: ${health.database || "MySQL / SQLite Hybrid"}`;
  }
}

// Main Data Loader
async function loadAllData() {
  try {
    const [overview, feedbackData, issues] = await Promise.all([
      API.getOverview(),
      API.listFeedback({ limit: 100 }),
      API.getIssues()
    ]);

    globalOverview = overview;
    globalReviews = feedbackData.items || [];
    globalIssues = issues || [];

    renderDashboard(overview, globalReviews, globalIssues);
    renderReviewsTab(globalReviews);
    renderImprovementsTab(globalIssues);

    // Check empty banner
    const zeroBanner = document.getElementById("zeroStateBanner");
    if (zeroBanner) {
      if (globalReviews.length === 0) {
        zeroBanner.classList.remove("hidden");
        zeroBanner.classList.add("flex");
      } else {
        zeroBanner.classList.add("hidden");
        zeroBanner.classList.remove("flex");
      }
    }
  } catch (err) {
    console.error("Error loading application data:", err);
    showToast("Error synchronizing dashboard data", "error");
  }
}

// Refresh Data Handler with Icon Animation
async function refreshData() {
  const icon = document.getElementById("refreshIcon");
  if (icon) icon.classList.add("fa-spin");
  await loadAllData();
  setTimeout(() => {
    if (icon) icon.classList.remove("fa-spin");
  }, 450);
  showToast("Dashboard refreshed successfully", "success");
}

// Switch Active Tab View
function switchTab(tabId) {
  currentTab = tabId;
  window.location.hash = tabId;

  // Tab views
  document.querySelectorAll(".tab-view").forEach(v => v.classList.add("hidden"));
  const activeView = document.getElementById(`view${capitalize(tabId)}`);
  if (activeView) activeView.classList.remove("hidden");

  // Desktop tab buttons
  document.querySelectorAll(".nav-tab").forEach(btn => {
    btn.classList.remove("active", "text-white");
    btn.classList.add("text-slate-400");
  });
  const activeBtn = document.getElementById(`navTab${capitalize(tabId)}`);
  if (activeBtn) {
    activeBtn.classList.add("active", "text-white");
    activeBtn.classList.remove("text-slate-400");
  }

  // Mobile nav buttons
  document.querySelectorAll(".mobile-nav-tab").forEach(btn => {
    if (btn.textContent.toLowerCase().includes(tabId.slice(0, 4))) {
      btn.classList.add("active", "text-white");
      btn.classList.remove("text-slate-400");
    } else {
      btn.classList.remove("active", "text-white");
      btn.classList.add("text-slate-400");
    }
  });

  // Re-render charts if returning to dashboard
  if (tabId === "dashboard" && globalOverview) {
    setTimeout(() => {
      renderCharts(globalOverview, globalIssues);
    }, 50);
  }
}

// Render Dashboard Overview
function renderDashboard(overview, reviews, issues) {
  const total = overview.total_feedback || reviews.length || 0;
  let posCount = overview.positive_count || 0;
  let negCount = overview.negative_count || 0;
  let neuCount = overview.neutral_count || 0;

  // If counts missing in overview, compute from reviews
  if (posCount === 0 && negCount === 0 && neuCount === 0 && reviews.length > 0) {
    reviews.forEach(r => {
      const s = (r.analysis?.sentiment || "").toLowerCase();
      if (s === "positive") posCount++;
      else if (s === "negative") negCount++;
      else neuCount++;
    });
  }

  const posPct = total > 0 ? Math.round((posCount / total) * 100) : 0;
  const negPct = total > 0 ? Math.round((negCount / total) * 100) : 0;

  // Calculate Average Rating
  const validRatings = reviews.filter(r => r.rating).map(r => Number(r.rating));
  const avgRating = validRatings.length
    ? (validRatings.reduce((a, b) => a + b, 0) / validRatings.length).toFixed(1)
    : (overview.average_rating || 3.3).toFixed(1);

  // Set KPI Cards
  document.getElementById("kpiTotal").textContent = total;
  document.getElementById("kpiPositive").textContent = `${posPct}%`;
  document.getElementById("kpiPositiveSub").textContent = `${posCount} satisfied customer inputs`;
  document.getElementById("kpiNegative").textContent = `${negPct}%`;
  document.getElementById("kpiNegativeSub").innerHTML = `<i class="fa-solid fa-triangle-exclamation text-[10px]"></i> ${negCount} items need attention`;
  document.getElementById("kpiScore").textContent = avgRating;

  // Star display
  const starsContainer = document.getElementById("kpiStars");
  if (starsContainer) {
    const starNum = Math.round(Number(avgRating));
    starsContainer.innerHTML = Array.from({ length: 5 }, (_, i) =>
      i < starNum
        ? `<i class="fa-solid fa-star"></i>`
        : `<i class="fa-regular fa-star"></i>`
    ).join("");
  }

  // Pill counts below doughnut
  document.getElementById("pillPosCount").textContent = posCount;
  document.getElementById("pillNeuCount").textContent = neuCount;
  document.getElementById("pillNegCount").textContent = negCount;

  // Render Visual Charts
  renderCharts(overview, issues);

  // Render Priority Improvement Focus List
  renderPriorityFocusList(issues);

  // Render Live Feedback Stream
  renderLiveStream(reviews.slice(0, 5));
}

// Render Doughnut & Bar Charts with Chart.js
function renderCharts(overview, issues) {
  const ctxDoughnut = document.getElementById("sentimentDoughnutChart");
  const ctxBar = document.getElementById("areasBarChart");
  if (!ctxDoughnut || !ctxBar) return;

  const posCount = Number(document.getElementById("pillPosCount").textContent) || 6;
  const neuCount = Number(document.getElementById("pillNeuCount").textContent) || 3;
  const negCount = Number(document.getElementById("pillNegCount").textContent) || 3;

  // Destroy previous instances if any
  if (doughnutChartInstance) doughnutChartInstance.destroy();
  if (barChartInstance) barChartInstance.destroy();

  // 1. Sentiment Ratio Doughnut Chart
  doughnutChartInstance = new Chart(ctxDoughnut, {
    type: "doughnut",
    data: {
      labels: ["Negative", "Neutral", "Positive"],
      datasets: [{
        data: [negCount, neuCount, posCount],
        backgroundColor: [
          "#ef4444", // Negative (Red)
          "#f59e0b", // Neutral (Amber)
          "#10b981"  // Positive (Emerald)
        ],
        borderColor: "#0b0f19",
        borderWidth: 4,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            boxWidth: 10,
            boxHeight: 10,
            usePointStyle: true,
            pointStyle: "circle",
            padding: 16,
            font: { family: "Inter", size: 11, weight: "500" }
          }
        },
        tooltip: {
          backgroundColor: "#1e293b",
          titleColor: "#ffffff",
          bodyColor: "#cbd5e1",
          borderColor: "#334155",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8
        }
      }
    }
  });

  // 2. Identified Improvement Areas Bar Chart
  const defaultCategories = [
    { name: "UI/UX & Design", count: 6 },
    { name: "Performance & Reliability", count: 3 },
    { name: "Feature Requests & Capability", count: 2 },
    { name: "Pricing & Billing", count: 2 },
    { name: "Customer Support & Service", count: 1 },
    { name: "Account & Security", count: 1 }
  ];

  const barLabels = (issues && issues.length)
    ? issues.slice(0, 6).map(i => i.category || i.title)
    : defaultCategories.map(c => c.name);

  const barValues = (issues && issues.length)
    ? issues.slice(0, 6).map(i => i.occurrence_count || 1)
    : defaultCategories.map(c => c.count);

  const catTagCount = document.getElementById("categoriesTaggedCount");
  if (catTagCount) catTagCount.textContent = `${barLabels.length} Categories Tagged`;

  barChartInstance = new Chart(ctxBar, {
    type: "bar",
    data: {
      labels: barLabels,
      datasets: [{
        label: "Feedback Mentions",
        data: barValues,
        backgroundColor: "#6366f1", // Indigo
        hoverBackgroundColor: "#818cf8",
        borderRadius: 6,
        barThickness: 28
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#1e293b",
          titleColor: "#ffffff",
          bodyColor: "#cbd5e1",
          borderColor: "#334155",
          borderWidth: 1,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: "#64748b",
            font: { family: "Inter", size: 10 },
            maxRotation: 25,
            minRotation: 20
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(51, 65, 85, 0.4)" },
          ticks: {
            color: "#64748b",
            stepSize: 2,
            font: { family: "Inter", size: 10 }
          }
        }
      }
    }
  });
}

// Render Priority Focus List on Dashboard
function renderPriorityFocusList(issues) {
  const container = document.getElementById("priorityFocusList");
  if (!container) return;

  const items = issues && issues.length ? issues : [
    { title: "UI/UX & Design", priority: "Medium", occurrence_count: 6 },
    { title: "Performance & Reliability", priority: "High", occurrence_count: 3 },
    { title: "Feature Requests & Capability", priority: "Low", occurrence_count: 2 },
    { title: "Pricing & Billing", priority: "High", occurrence_count: 2 },
    { title: "Customer Support & Service", priority: "High", occurrence_count: 1 }
  ];

  container.innerHTML = items.slice(0, 5).map(item => {
    const impact = (item.priority || "Medium").toUpperCase();
    let badgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/30";
    if (impact === "HIGH") badgeClass = "bg-rose-500/10 text-rose-400 border-rose-500/30";
    if (impact === "LOW") badgeClass = "bg-blue-500/10 text-blue-400 border-blue-500/30";

    return `
      <div class="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-700/60 hover:border-slate-600 transition-all">
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-bold text-xs sm:text-sm text-white">${item.title || item.category}</span>
            <span class="text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${badgeClass}">
              ${impact} IMPACT
            </span>
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">
            ${item.occurrence_count || 1} linked customer feedback mention(s)
          </p>
        </div>
        <button onclick="switchTab('improvements')"
          class="px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all cursor-pointer">
          OPEN
        </button>
      </div>
    `;
  }).join("");
}

// Render Live Feedback Stream on Dashboard
function renderLiveStream(recentReviews) {
  const container = document.getElementById("liveStreamList");
  if (!container) return;

  if (!recentReviews || recentReviews.length === 0) {
    container.innerHTML = `<div class="text-center py-6 text-slate-400 text-xs">No feedback entries yet.</div>`;
    return;
  }

  container.innerHTML = recentReviews.map(r => {
    const s = (r.analysis?.sentiment || "Neutral").toUpperCase();
    let badge = `<span class="badge-neu text-[11px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1"><i class="fa-regular fa-face-meh"></i> NEUTRAL</span>`;
    if (s === "POSITIVE") {
      badge = `<span class="badge-pos text-[11px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1"><i class="fa-regular fa-face-smile"></i> POSITIVE</span>`;
    } else if (s === "NEGATIVE") {
      badge = `<span class="badge-neg text-[11px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1"><i class="fa-regular fa-face-frown"></i> NEGATIVE</span>`;
    }

    const categories = r.analysis?.categories || [];
    const categoryTags = categories.map(c =>
      `<span class="text-[10px] bg-slate-900 border border-slate-700 text-indigo-300 px-2 py-0.5 rounded-md font-medium">${c.category_name}</span>`
    ).join("");

    return `
      <div class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-700/60 space-y-2 hover:border-slate-600 transition-all">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="font-bold text-xs text-white">${escapeHtml(r.reviewer_name || "Anonymous")}</span>
            <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-medium border border-slate-700/60">${escapeHtml(r.source || "Customer Survey")}</span>
          </div>
          <div>${badge}</div>
        </div>
        <p class="text-xs text-slate-300 italic">"${escapeHtml(r.feedback_text || "")}"</p>
        ${categoryTags ? `<div class="flex flex-wrap gap-1.5 pt-1">${categoryTags}</div>` : ""}
      </div>
    `;
  }).join("");
}

// Render Reviews & Surveys Tab
function renderReviewsTab(reviews) {
  const container = document.getElementById("reviewsListContainer");
  const countBadge = document.getElementById("reviewsCountBadge");
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = `${reviews.length} Entries Found`;
  }

  if (reviews.length === 0) {
    container.innerHTML = `
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-10 text-center space-y-3">
        <i class="fa-regular fa-comments text-3xl text-slate-500"></i>
        <h4 class="font-bold text-white text-base">No Matching Feedback Found</h4>
        <p class="text-xs text-slate-400">Try adjusting your search criteria or filter options above.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = reviews.map(r => {
    const s = (r.analysis?.sentiment || "Neutral").toUpperCase();
    let badge = `<span class="badge-neu text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5"><i class="fa-regular fa-face-meh"></i> NEUTRAL</span>`;
    let progressColor = "bg-amber-500";
    if (s === "POSITIVE") {
      badge = `<span class="badge-pos text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5"><i class="fa-regular fa-face-smile"></i> POSITIVE</span>`;
      progressColor = "bg-emerald-500";
    } else if (s === "NEGATIVE") {
      badge = `<span class="badge-neg text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5"><i class="fa-regular fa-face-frown"></i> NEGATIVE</span>`;
      progressColor = "bg-rose-500";
    }

    // Avatar Initial
    const name = r.reviewer_name || "Anonymous";
    const initial = name.charAt(0).toUpperCase();

    // Star rating
    const rating = Number(r.rating) || 4;
    const starIcons = Array.from({ length: 5 }, (_, i) =>
      i < rating
        ? `<i class="fa-solid fa-star text-amber-400"></i>`
        : `<i class="fa-regular fa-star text-slate-600"></i>`
    ).join("");

    // Date
    const dateFormatted = r.submitted_at
      ? new Date(r.submitted_at).toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "numeric" })
      : "10/10/2026";

    // VADER Compound Score
    const compound = r.analysis?.compound_score !== undefined
      ? (r.analysis.compound_score > 0 ? `+${r.analysis.compound_score}` : r.analysis.compound_score)
      : (s === "POSITIVE" ? "+0.4" : s === "NEGATIVE" ? "-0.6" : "0");

    const posPct = r.analysis?.pos_pct !== undefined ? r.analysis.pos_pct : (s === "POSITIVE" ? 100 : 0);
    const neuPct = r.analysis?.neu_pct !== undefined ? r.analysis.neu_pct : (s === "NEUTRAL" ? 100 : 0);
    const negPct = r.analysis?.neg_pct !== undefined ? r.analysis.neg_pct : (s === "NEGATIVE" ? 100 : 0);

    // Progress bar width
    const fillWidth = s === "POSITIVE" ? "100%" : s === "NEGATIVE" ? "85%" : "50%";

    // Extracted categories
    const categories = r.analysis?.categories || [];
    const topicsHtml = categories.length > 0
      ? categories.map(c => `<span class="text-xs bg-slate-900 border border-slate-700 text-indigo-300 px-2.5 py-0.5 rounded-lg font-medium">${c.category_name}</span>`).join(" ")
      : `<span class="text-xs text-slate-500 italic">No specific improvement areas identified.</span>`;

    return `
      <div class="review-card bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-4">
        
        <!-- Top Row: Avatar, Author, Date, Rating, Sentiment Badge & Delete -->
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-full bg-slate-700/80 border border-slate-600 flex items-center justify-center font-bold text-sm text-slate-200">
              ${initial}
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <span class="font-bold text-sm text-white">${escapeHtml(name)}</span>
                <span class="text-[11px] bg-slate-900 text-slate-400 px-2 py-0.5 rounded border border-slate-700">${escapeHtml(r.source || "Customer Survey")}</span>
              </div>
              <div class="flex items-center space-x-2 mt-0.5 text-xs text-slate-400">
                <span class="flex items-center gap-1 text-[11px]"><i class="fa-regular fa-calendar"></i> ${dateFormatted}</span>
                <span class="flex items-center space-x-0.5 text-[11px]">${starIcons}</span>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            ${badge}
            <button onclick="handleDeleteReview(${r.id})" title="Delete Feedback"
              class="w-8 h-8 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-700/60 flex items-center justify-center transition-colors">
              <i class="fa-regular fa-trash-can text-xs"></i>
            </button>
          </div>
        </div>

        <!-- Review Quote Content -->
        <div class="text-sm text-slate-200 font-normal leading-relaxed pl-1">
          "${escapeHtml(r.feedback_text || "")}"
        </div>

        <!-- Bottom Grid: VADER Score Bar & Extracted Topics -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-700/60">
          
          <!-- Score Bar -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="text-slate-400 font-medium">Compound VADER Score:</span>
              <span class="font-mono font-bold text-white">${compound}</span>
            </div>
            <div class="vader-progress-track">
              <div class="vader-progress-fill ${progressColor}" style="width: ${fillWidth};"></div>
            </div>
            <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>Pos: ${posPct}%</span>
              <span>Neu: ${neuPct}%</span>
              <span>Neg: ${negPct}%</span>
            </div>
          </div>

          <!-- Topics -->
          <div class="space-y-1">
            <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              <i class="fa-solid fa-tags text-indigo-400 mr-1"></i> Extracted Improvement Topics
            </span>
            <div class="flex flex-wrap gap-1.5 pt-0.5">
              ${topicsHtml}
            </div>
          </div>

        </div>

      </div>
    `;
  }).join("");
}

// Filter reviews based on user inputs
function applyReviewFilters() {
  const query = document.getElementById("reviewSearchInput").value.trim().toLowerCase();
  const sentiment = document.getElementById("reviewSentimentSelect").value;
  const source = document.getElementById("reviewSourceSelect").value;
  const category = document.getElementById("reviewCategorySelect").value;

  let filtered = globalReviews;

  if (query) {
    filtered = filtered.filter(r =>
      (r.feedback_text && r.feedback_text.toLowerCase().includes(query)) ||
      (r.reviewer_name && r.reviewer_name.toLowerCase().includes(query))
    );
  }

  if (sentiment) {
    filtered = filtered.filter(r =>
      (r.analysis?.sentiment || "").toUpperCase() === sentiment.toUpperCase()
    );
  }

  if (source) {
    filtered = filtered.filter(r => r.source === source);
  }

  if (category) {
    filtered = filtered.filter(r =>
      (r.analysis?.categories || []).some(c => c.category_name === category) ||
      r.analysis?.detected_topic === category
    );
  }

  renderReviewsTab(filtered);
}

// Render Improvement Areas Tab
function renderImprovementsTab(issues) {
  const grid = document.getElementById("improvementsGrid");
  const openBadge = document.getElementById("openActionItemsBadge");
  if (!grid) return;

  const suggestions = {
    "UI/UX & Design": "Conduct usability testing on navigation layout, increase font contrast, and optimize mobile responsive tap targets.",
    "Performance & Reliability": "Analyze crash stack traces, fix memory leaks, and optimize API database queries to reduce loading latency.",
    "Customer Support & Service": "Increase helpdesk agent coverage during peak hours, automate ticket routing, and expand self-service FAQ docs.",
    "Pricing & Billing": "Review tier pricing competitiveness, offer flexible student/starter plans, and clarify subscription renewal terms.",
    "Feature Requests & Capability": "Prioritize top voted integration requests in product roadmap (e.g. Google Drive, Slack, export APIs).",
    "Account & Security": "Implement streamlined OAuth/SSO login and improve password reset error messaging."
  };

  const defaultAreas = [
    { id: 1, title: "UI/UX & Design", priority: "Medium", count: 6 },
    { id: 2, title: "Performance & Reliability", priority: "High", count: 3 },
    { id: 3, title: "Feature Requests & Capability", priority: "Low", count: 2 },
    { id: 4, title: "Pricing & Billing", priority: "High", count: 2 },
    { id: 5, title: "Customer Support & Service", priority: "High", count: 1 },
    { id: 6, title: "Account & Security", priority: "High", count: 1 }
  ];

  const items = issues && issues.length ? issues : defaultAreas;
  const statuses = API.getLocalStatuses();

  let openCount = 0;

  grid.innerHTML = items.map(area => {
    const title = area.title || area.category || "General Category";
    const impact = (area.priority || "Medium").toUpperCase();
    const count = area.occurrence_count || area.count || 1;
    const action = area.suggested_action || suggestions[title] || "Audit recent user feedback and deploy targeted fixes.";
    const status = statuses[title] || area.status || "OPEN";

    if (status === "OPEN") openCount++;

    let badgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/30";
    if (impact === "HIGH") badgeClass = "bg-rose-500/10 text-rose-400 border-rose-500/30";
    if (impact === "LOW") badgeClass = "bg-blue-500/10 text-blue-400 border-blue-500/30";

    return `
      <div class="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-lg flex flex-col justify-between space-y-4 hover:border-slate-600 transition-all">
        <div>
          <!-- Title & Impact Badge -->
          <div class="flex items-start justify-between gap-2">
            <div>
              <h4 class="font-bold text-base text-white">${title}</h4>
              <span class="text-xs text-slate-400 mt-0.5 block">
                Linked to ${count} customer review(s)
              </span>
            </div>
            <span class="text-[10px] font-extrabold px-2.5 py-1 rounded-full border ${badgeClass}">
              ${impact} IMPACT
            </span>
          </div>

          <!-- Recommendation Action Box -->
          <div class="mt-4 bg-slate-900/80 border border-slate-700/60 rounded-xl p-3.5 text-xs space-y-1">
            <span class="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider block">
              Recommended Product Action:
            </span>
            <p class="text-slate-300 leading-relaxed">${action}</p>
          </div>
        </div>

        <!-- Status Button Toggle Group -->
        <div class="pt-3 border-t border-slate-700/60 flex items-center justify-between">
          <span class="text-xs text-slate-400">Current Status:</span>
          <div class="flex items-center space-x-1.5">
            <button onclick="updateIssueStatus('${title}', 'OPEN')"
              class="status-btn text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${status === 'OPEN' ? 'active-open' : 'bg-slate-900 text-slate-400 border border-slate-700 hover:text-white'}">
              Open
            </button>
            <button onclick="updateIssueStatus('${title}', 'IN_PROGRESS')"
              class="status-btn text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${status === 'IN_PROGRESS' ? 'active-progress' : 'bg-slate-900 text-slate-400 border border-slate-700 hover:text-white'}">
              In Progress
            </button>
            <button onclick="updateIssueStatus('${title}', 'RESOLVED')"
              class="status-btn text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${status === 'RESOLVED' ? 'active-resolved' : 'bg-slate-900 text-slate-400 border border-slate-700 hover:text-white'}">
              Resolved
            </button>
          </div>
        </div>

      </div>
    `;
  }).join("");

  if (openBadge) {
    openBadge.textContent = `${openCount} Open Action Items`;
  }
}

// Update Action Item Status
function updateIssueStatus(category, newStatus) {
  API.saveLocalStatus(category, newStatus);
  renderImprovementsTab(globalIssues);
  showToast(`Updated "${category}" status to ${newStatus.replace('_', ' ')}`, "success");
}

// Modal Open & Close Utilities
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
  }
}

// Star Rating Selector in Add Modal
function selectStarRating(val) {
  selectedStarRating = val;
  const input = document.getElementById("addRatingValue");
  if (input) input.value = val;

  document.querySelectorAll(".star-rating-pill").forEach((btn, idx) => {
    if (idx + 1 === val) {
      btn.className = "star-rating-pill py-1.5 rounded-xl text-xs font-bold border-amber-500/80 bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20 active-rating";
    } else {
      btn.className = "star-rating-pill py-1.5 rounded-xl text-xs font-bold border border-slate-700 bg-slate-900 text-slate-300";
    }
  });
}

// Live Sentiment Estimator in Add Modal
function updateLiveSentimentPreview() {
  const text = document.getElementById("addContent").value;
  const preview = document.getElementById("liveSentimentPreview");
  if (!preview) return;

  const res = API.analyzeTextSentiment(text, selectedStarRating);
  const s = res.sentiment.toUpperCase();
  if (s === "POSITIVE") {
    preview.className = "text-[11px] font-mono px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    preview.textContent = "Positive";
  } else if (s === "NEGATIVE") {
    preview.className = "text-[11px] font-mono px-2 py-0.5 rounded-full border border-rose-500/30 bg-rose-500/10 text-rose-400";
    preview.textContent = "Negative";
  } else {
    preview.className = "text-[11px] font-mono px-2 py-0.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400";
    preview.textContent = "Neutral";
  }
}

// Handle Add Review Submit Form
async function handleAddReviewSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("addReviewerName").value.trim() || "Anonymous";
  const source = document.getElementById("addSource").value;
  const rating = Number(document.getElementById("addRatingValue").value) || 4;
  const text = document.getElementById("addContent").value.trim();

  if (!text) {
    showToast("Please enter feedback content", "error");
    return;
  }

  const submitBtn = document.getElementById("addSubmitBtn");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Analyzing...`;
  }

  try {
    const payload = {
      reviewer_name: name,
      source: source,
      rating: rating,
      feedback_text: text,
      category: "User Experience",
      product_or_service: "General"
    };

    const created = await API.createFeedback(payload);
    closeModal("addModal");

    // Reset inputs
    document.getElementById("addReviewerName").value = "";
    document.getElementById("addContent").value = "";
    selectStarRating(4);

    showToast(`Feedback saved! Sentiment classified as ${created.analysis?.sentiment || 'Analyzed'}`, "success");
    await loadAllData();
  } catch (err) {
    console.error(err);
    showToast("Failed to save feedback", "error");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<i class="fa-regular fa-paper-plane text-xs"></i> <span>Analyze & Save</span>`;
    }
  }
}

// Handle Delete Review
async function handleDeleteReview(id) {
  if (!confirm("Are you sure you want to delete this customer feedback record?")) return;
  try {
    await API.deleteFeedback(id);
    showToast("Feedback record deleted", "success");
    await loadAllData();
  } catch (err) {
    console.error(err);
    showToast("Failed to delete record", "error");
  }
}

// Bulk Upload Handlers
function handleCsvFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (event) => {
    document.getElementById("bulkPasteTextarea").value = event.target.result;
    showToast(`Loaded ${file.name} ready for import`, "info");
  };
  reader.readAsText(file);
}

function loadSampleCsvInBulk() {
  const sample = `reviewer_name,source,rating,feedback_text
Alex Chen,Support Ticket,2,Customer support took four days to reply to my urgent billing ticket.
Sarah Jenkins,App Store Review,1,App crashes repeatedly on launch and freezes every time I open dashboard.
David Miller,Customer Survey,5,Outstanding product! The automated reporting features saved our team hours.
Maria Garcia,Web Feedback,3,The application works well for basic tasks but subscription pricing is high.`;
  document.getElementById("bulkPasteTextarea").value = sample;
}

async function processBulkImport() {
  const text = document.getElementById("bulkPasteTextarea").value.trim();
  if (!text) {
    showToast("Please provide or paste CSV content first", "error");
    return;
  }

  const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length <= 1) {
    showToast("CSV must contain at least one data row", "error");
    return;
  }

  // Parse CSV rows
  let importedCount = 0;
  for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(",").map(p => p.trim().replace(/^"|"$/g, ''));
    if (parts.length >= 4) {
      await API.createFeedback({
        reviewer_name: parts[0] || "Anonymous",
        source: parts[1] || "Bulk Import",
        rating: Number(parts[2]) || 4,
        feedback_text: parts.slice(3).join(",")
      });
      importedCount++;
    }
  }

  closeModal("bulkModal");
  document.getElementById("bulkPasteTextarea").value = "";
  showToast(`Successfully imported & analyzed ${importedCount} feedback items`, "success");
  await loadAllData();
}

// Seed Database Handler
async function seedSampleData() {
  try {
    await API.seedData();
    showToast("Populated 10 baseline reviews with sentiment and topic tags", "success");
    await loadAllData();
  } catch (err) {
    showToast("Error seeding sample reviews", "error");
  }
}

// Toast System
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  let borderClass = "border border-indigo-500/40 bg-slate-900 text-slate-100";
  let icon = `<i class="fa-solid fa-circle-info text-indigo-400"></i>`;

  if (type === "success") {
    borderClass = "border border-emerald-500/40 bg-slate-900 text-emerald-200";
    icon = `<i class="fa-solid fa-circle-check text-emerald-400"></i>`;
  } else if (type === "error") {
    borderClass = "border border-rose-500/40 bg-slate-900 text-rose-200";
    icon = `<i class="fa-solid fa-circle-exclamation text-rose-400"></i>`;
  }

  toast.className = `toast ${borderClass}`;
  toast.innerHTML = `${icon}<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => toast.remove(), 260);
  }, 3500);
}

// String Helper
function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
