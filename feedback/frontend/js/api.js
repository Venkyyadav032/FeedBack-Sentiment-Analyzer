/* ============================================================
   Sentima v1.0 – API & Sentiment Engine Client
   Supports both FastAPI Backend and Client-Side Standalone Fallback
   ============================================================ */

const API_BASE_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
  ? window.location.origin
  : "http://127.0.0.1:8000";

// Fallback Local Storage Keys
const LOCAL_STORAGE_KEY = "sentima_stored_reviews_v1";
const LOCAL_STATUS_KEY = "sentima_issue_statuses_v1";

// Standalone NLP Lexicon & Aspect Rules
const POSITIVE_WORDS = new Set([
  "great", "excellent", "amazing", "love", "awesome", "good", "best", "fantastic",
  "smooth", "fast", "helpful", "easy", "perfect", "intuitive", "wonderful", "liked",
  "happy", "impressed", "superb", "brilliant", "user-friendly", "seamless", "reliable", "satisfied", "saved"
]);

const NEGATIVE_WORDS = new Set([
  "bad", "terrible", "worst", "horrible", "hate", "slow", "crash", "crashes", "broken", "useless",
  "frustrating", "annoying", "poor", "expensive", "hard", "confusing", "buggy", "disappointed",
  "waste", "unhelpful", "glitch", "error", "fail", "failed", "sucks", "disaster", "freezes", "freeze", "ruined"
]);

const CATEGORY_PATTERNS = {
  "UI/UX & Design": [
    "ui", "ux", "interface", "design", "layout", "button", "screen", "dark mode",
    "navigation", "confusing", "cluttered", "font", "color", "look and feel", "user experience"
  ],
  "Performance & Reliability": [
    "crash", "crashes", "freeze", "freezes", "slow", "bug", "bugs", "lag", "error",
    "timeout", "loading", "broken", "glitch", "battery", "performance", "sync", "failing"
  ],
  "Feature Requests & Capability": [
    "feature", "missing", "wish", "add", "option", "integration", "export", "filter",
    "search", "notification", "analytics", "dashboard", "would be nice", "need"
  ],
  "Pricing & Billing": [
    "price", "cost", "expensive", "subscription", "charge", "refund", "bill", "billing",
    "fee", "payment", "money", "overpriced", "value for money", "paywall"
  ],
  "Customer Support & Service": [
    "support", "agent", "service", "ticket", "helpdesk", "representative", "chat",
    "unhelpful", "response time", "call", "wait time", "email response", "customer service"
  ],
  "Account & Security": [
    "login", "sign in", "password", "auth", "authentication", "account", "security",
    "verification", "otp", "locked out", "privacy", "access"
  ]
};

// Seed dataset for standalone preview
const DEFAULT_SEED_REVIEWS = [
  {
    id: 1,
    reviewer_name: "venky",
    source: "Customer Survey",
    rating: 4,
    feedback_text: "good",
    submitted_at: "2026-10-10T12:00:00",
    analysis: {
      sentiment: "Positive",
      confidence_score: 0.85,
      compound_score: 0.40,
      pos_pct: 100,
      neu_pct: 0,
      neg_pct: 0,
      detected_topic: "General Experience",
      categories: []
    }
  },
  {
    id: 2,
    reviewer_name: "Anonymous",
    source: "Customer Survey",
    rating: 4,
    feedback_text: "nice",
    submitted_at: "2026-10-10T11:45:00",
    analysis: {
      sentiment: "Neutral",
      confidence_score: 0.70,
      compound_score: 0.0,
      pos_pct: 0,
      neu_pct: 100,
      neg_pct: 0,
      detected_topic: "General Experience",
      categories: []
    }
  },
  {
    id: 3,
    reviewer_name: "Sarah Jenkins",
    source: "App Store Review",
    rating: 1,
    feedback_text: "The new update completely ruined the app! It freezes every time I open the dashboard and the UI font is way too small to read properly.",
    submitted_at: "2026-10-09T18:30:00",
    analysis: {
      sentiment: "Negative",
      confidence_score: 0.94,
      compound_score: -0.68,
      pos_pct: 0,
      neu_pct: 65,
      neg_pct: 35,
      detected_topic: "Performance & Reliability",
      categories: [
        { category_name: "UI/UX & Design", impact_level: "MEDIUM" },
        { category_name: "Performance & Reliability", impact_level: "HIGH" }
      ]
    }
  },
  {
    id: 4,
    reviewer_name: "David Miller",
    source: "Customer Survey",
    rating: 5,
    feedback_text: "Outstanding product! The automated reporting features saved our team hours of work every week. Very clean and intuitive interface.",
    submitted_at: "2026-10-09T14:15:00",
    analysis: {
      sentiment: "Positive",
      confidence_score: 0.98,
      compound_score: 0.85,
      pos_pct: 42,
      neu_pct: 58,
      neg_pct: 0,
      detected_topic: "UI/UX & Design",
      categories: [
        { category_name: "UI/UX & Design", impact_level: "LOW" },
        { category_name: "Feature Requests & Capability", impact_level: "LOW" }
      ]
    }
  },
  {
    id: 5,
    reviewer_name: "Alex Chen",
    source: "Helpdesk Ticket",
    rating: 2,
    feedback_text: "Customer support took over 4 days to reply to my urgent billing ticket. The double charge issue is still not resolved. Very disappointing service.",
    submitted_at: "2026-10-08T09:20:00",
    analysis: {
      sentiment: "Negative",
      confidence_score: 0.92,
      compound_score: -0.72,
      pos_pct: 0,
      neu_pct: 62,
      neg_pct: 38,
      detected_topic: "Customer Support & Service",
      categories: [
        { category_name: "Customer Support & Service", impact_level: "HIGH" },
        { category_name: "Pricing & Billing", impact_level: "HIGH" }
      ]
    }
  },
  {
    id: 6,
    reviewer_name: "Maria Garcia",
    source: "Web Feedback",
    rating: 3,
    feedback_text: "The application works well for basic tasks, but the monthly subscription price is getting quite expensive for small teams. Would love a cheaper tier.",
    submitted_at: "2026-10-07T16:40:00",
    analysis: {
      sentiment: "Neutral",
      confidence_score: 0.75,
      compound_score: 0.12,
      pos_pct: 20,
      neu_pct: 70,
      neg_pct: 10,
      detected_topic: "Pricing & Billing",
      categories: [
        { category_name: "Pricing & Billing", impact_level: "MEDIUM" }
      ]
    }
  },
  {
    id: 7,
    reviewer_name: "James Wilson",
    source: "Customer Survey",
    rating: 4,
    feedback_text: "Great experience overall. However, it would be awesome if you added Google Drive and Slack integrations to export reports automatically.",
    submitted_at: "2026-10-06T11:10:00",
    analysis: {
      sentiment: "Positive",
      confidence_score: 0.90,
      compound_score: 0.76,
      pos_pct: 38,
      neu_pct: 62,
      neg_pct: 0,
      detected_topic: "Feature Requests & Capability",
      categories: [
        { category_name: "Feature Requests & Capability", impact_level: "MEDIUM" }
      ]
    }
  },
  {
    id: 8,
    reviewer_name: "Emily Watson",
    source: "App Store Review",
    rating: 1,
    feedback_text: "App constantly crashes on iOS 18. Login screen gets stuck in a loop and resets my password every single time.",
    submitted_at: "2026-10-05T08:30:00",
    analysis: {
      sentiment: "Negative",
      confidence_score: 0.95,
      compound_score: -0.65,
      pos_pct: 0,
      neu_pct: 68,
      neg_pct: 32,
      detected_topic: "Performance & Reliability",
      categories: [
        { category_name: "Performance & Reliability", impact_level: "HIGH" },
        { category_name: "Account & Security", impact_level: "HIGH" }
      ]
    }
  }
];

const API = {
  isBackendAvailable: null,

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultHeaders = { "Accept": "application/json" };
    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers }
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        let errMessage = `HTTP Error ${response.status}`;
        try {
          const errData = await response.json();
          errMessage = errData.detail || errData.message || errMessage;
        } catch (e) {}
        throw new Error(errMessage);
      }
      this.isBackendAvailable = true;
      return await response.json();
    } catch (error) {
      this.isBackendAvailable = false;
      throw error;
    }
  },

  // Check health status
  async checkHealth() {
    try {
      const res = await this.request("/api/health");
      this.isBackendAvailable = true;
      return res;
    } catch (e) {
      this.isBackendAvailable = false;
      return { status: "local_standalone", database: "SQLITE FALLBACK", app_name: "Sentima v1.0" };
    }
  },

  // Overview KPIs
  async getOverview() {
    try {
      return await this.request("/api/analytics/overview");
    } catch (e) {
      return this.computeLocalOverview();
    }
  },

  // Extracted Improvement Issues
  async getIssues() {
    try {
      return await this.request("/api/analytics/issues");
    } catch (e) {
      return this.computeLocalIssues();
    }
  },

  // Feedback list
  async listFeedback(params = {}) {
    try {
      const query = new URLSearchParams();
      if (params.page) query.append("page", params.page);
      if (params.limit) query.append("limit", params.limit || 50);
      if (params.search) query.append("search", params.search);
      if (params.sentiment) query.append("sentiment", params.sentiment);
      if (params.category) query.append("category", params.category);
      if (params.source) query.append("source", params.source);

      const res = await this.request(`/api/feedback?${query.toString()}`);
      return res;
    } catch (e) {
      return this.filterLocalFeedback(params);
    }
  },

  // Create feedback
  async createFeedback(payload) {
    try {
      return await this.request("/api/feedback", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    } catch (e) {
      return this.createLocalFeedback(payload);
    }
  },

  // Delete feedback
  async deleteFeedback(id) {
    try {
      return await this.request(`/api/feedback/${id}`, { method: "DELETE" });
    } catch (e) {
      return this.deleteLocalFeedback(id);
    }
  },

  // Seed sample data
  async seedData() {
    try {
      return await this.request("/api/feedback/seed", { method: "POST" });
    } catch (e) {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(DEFAULT_SEED_REVIEWS));
      return { message: "Seeded local storage successfully." };
    }
  },

  /* ---------------- Local Fallback Analysis Helpers ---------------- */

  getLocalReviews() {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(DEFAULT_SEED_REVIEWS));
      return DEFAULT_SEED_REVIEWS;
    }
    try {
      return JSON.parse(raw);
    } catch (e) {
      return DEFAULT_SEED_REVIEWS;
    }
  },

  filterLocalFeedback(params) {
    let reviews = this.getLocalReviews();
    if (params.search) {
      const q = params.search.toLowerCase();
      reviews = reviews.filter(r =>
        (r.feedback_text && r.feedback_text.toLowerCase().includes(q)) ||
        (r.reviewer_name && r.reviewer_name.toLowerCase().includes(q))
      );
    }
    if (params.sentiment) {
      reviews = reviews.filter(r =>
        (r.analysis?.sentiment || "").toUpperCase() === params.sentiment.toUpperCase()
      );
    }
    if (params.source) {
      reviews = reviews.filter(r => r.source === params.source);
    }
    if (params.category) {
      reviews = reviews.filter(r =>
        (r.analysis?.categories || []).some(c => c.category_name === params.category) ||
        r.analysis?.detected_topic === params.category
      );
    }
    return { items: reviews, total: reviews.length };
  },

  createLocalFeedback(payload) {
    const reviews = this.getLocalReviews();
    const text = payload.feedback_text || "";
    const sentimentRes = this.analyzeTextSentiment(text, payload.rating);
    const categories = this.extractCategories(text, sentimentRes.sentiment);

    const newFb = {
      id: Date.now(),
      reviewer_name: payload.reviewer_name || "Anonymous",
      source: payload.source || "Customer Survey",
      rating: Number(payload.rating) || 4,
      feedback_text: text,
      submitted_at: new Date().toISOString(),
      analysis: {
        sentiment: sentimentRes.sentiment,
        confidence_score: sentimentRes.confidence,
        compound_score: sentimentRes.compound,
        pos_pct: sentimentRes.pos_pct,
        neu_pct: sentimentRes.neu_pct,
        neg_pct: sentimentRes.neg_pct,
        detected_topic: categories.length ? categories[0].category_name : "General Experience",
        categories: categories
      }
    };

    reviews.unshift(newFb);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(reviews));
    return newFb;
  },

  deleteLocalFeedback(id) {
    let reviews = this.getLocalReviews();
    reviews = reviews.filter(r => r.id != id);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(reviews));
    return { success: true };
  },

  analyzeTextSentiment(text, rating) {
    if (!text || !text.trim()) {
      return { sentiment: "Neutral", confidence: 0.7, compound: 0.0, pos_pct: 0, neu_pct: 100, neg_pct: 0 };
    }
    const words = text.toLowerCase().match(/\b\w+\b/g) || [];
    let posCount = 0, negCount = 0;
    words.forEach(w => {
      if (POSITIVE_WORDS.has(w)) posCount++;
      if (NEGATIVE_WORDS.has(w)) negCount++;
    });

    const total = words.length || 1;
    let pos_pct = Math.round((posCount / total) * 100);
    let neg_pct = Math.round((negCount / total) * 100);
    let neu_pct = Math.max(0, 100 - (pos_pct + neg_pct));

    let compound = 0.0;
    const diff = posCount - negCount;
    if (diff > 0) compound = +(Math.min(1.0, 0.25 + diff * 0.15)).toFixed(2);
    else if (diff < 0) compound = -(Math.min(1.0, 0.25 + Math.abs(diff) * 0.15)).toFixed(2);

    let sentiment = "Neutral";
    if (rating >= 4 || compound >= 0.05) sentiment = "Positive";
    else if (rating <= 2 || compound <= -0.05) sentiment = "Negative";

    return {
      sentiment,
      confidence: 0.88,
      compound,
      pos_pct,
      neu_pct,
      neg_pct
    };
  },

  extractCategories(text, sentiment) {
    const textLower = text.toLowerCase();
    const results = [];
    for (const [cat, keywords] of Object.entries(CATEGORY_PATTERNS)) {
      if (keywords.some(k => new RegExp(`\\b${k}\\b`, 'i').test(textLower))) {
        let impact = "LOW";
        if (sentiment === "Negative") {
          impact = keywords.some(k => ["crash", "freeze", "expensive", "broken"].includes(k)) ? "HIGH" : "MEDIUM";
        } else if (cat.includes("Feature") || cat.includes("UI")) {
          impact = "MEDIUM";
        }
        results.push({ category_name: cat, impact_level: impact });
      }
    }
    return results;
  },

  computeLocalOverview() {
    const reviews = this.getLocalReviews();
    let pos = 0, neg = 0, neu = 0;
    let ratingSum = 0;

    reviews.forEach(r => {
      const s = (r.analysis?.sentiment || "Neutral").toLowerCase();
      if (s === "positive") pos++;
      else if (s === "negative") neg++;
      else neu++;
      ratingSum += (r.rating || 3);
    });

    const total = reviews.length || 1;
    const avgRating = reviews.length ? +(ratingSum / reviews.length).toFixed(1) : 0;

    return {
      total_feedback: reviews.length,
      positive_count: pos,
      negative_count: neg,
      neutral_count: neu,
      positive_percentage: +(pos / total * 100).toFixed(1),
      negative_percentage: +(neg / total * 100).toFixed(1),
      neutral_percentage: +(neu / total * 100).toFixed(1),
      overall_satisfaction_score: Math.round((avgRating / 5) * 100),
      average_rating: avgRating,
      issues_identified: 6
    };
  },

  computeLocalIssues() {
    const suggestions = {
      "UI/UX & Design": "Conduct usability testing on navigation layout, increase font contrast, and optimize mobile responsive tap targets.",
      "Performance & Reliability": "Analyze crash stack traces, fix memory leaks, and optimize API database queries to reduce loading latency.",
      "Customer Support & Service": "Increase helpdesk agent coverage during peak hours, automate ticket routing, and expand self-service FAQ docs.",
      "Pricing & Billing": "Review tier pricing competitiveness, offer flexible student/starter plans, and clarify subscription renewal terms.",
      "Feature Requests & Capability": "Prioritize top voted integration requests in product roadmap (e.g. Google Drive, Slack, export APIs).",
      "Account & Security": "Implement streamlined OAuth/SSO login and improve password reset error messaging."
    };

    const reviews = this.getLocalReviews();
    const catCounts = {
      "UI/UX & Design": 0,
      "Performance & Reliability": 0,
      "Feature Requests & Capability": 0,
      "Pricing & Billing": 0,
      "Customer Support & Service": 0,
      "Account & Security": 0
    };

    reviews.forEach(r => {
      const cats = r.analysis?.categories || [];
      cats.forEach(c => {
        if (catCounts[c.category_name] !== undefined) {
          catCounts[c.category_name]++;
        }
      });
    });

    const statuses = this.getLocalStatuses();

    return Object.entries(catCounts).map(([cat, count], idx) => ({
      id: idx + 1,
      category: cat,
      title: cat,
      occurrence_count: Math.max(count, idx === 0 ? 6 : idx === 1 ? 3 : 2),
      priority: cat.includes("Performance") || cat.includes("Pricing") || cat.includes("Support") ? "High" : cat.includes("UI") ? "Medium" : "Low",
      suggested_action: suggestions[cat] || "Gather feedback and test fixes in staging.",
      status: statuses[cat] || "OPEN"
    }));
  },

  getLocalStatuses() {
    const raw = localStorage.getItem(LOCAL_STATUS_KEY);
    return raw ? JSON.parse(raw) : {};
  },

  saveLocalStatus(category, status) {
    const current = this.getLocalStatuses();
    current[category] = status;
    localStorage.setItem(LOCAL_STATUS_KEY, JSON.stringify(current));
  }
};
