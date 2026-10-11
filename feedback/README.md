# FeedbackSense AI – Sentiment Analysis and Feedback Intelligence System

**FeedbackSense AI** is a complete, modern, responsive web application for classifying customer feedback sentiment (Positive, Negative, Neutral), identifying recurring issues, tracking satisfaction trends, and generating actionable improvement recommendations.

---

## 🌟 Key Features

1. **Dashboard Analytics**: Live overview cards (Total Feedback, Positive/Negative/Neutral %, Satisfaction Score, Issues Identified) with interactive Chart.js visualizations (Doughnut, Line, Bar, and Category Stacked Bar charts).
2. **Sentiment Analysis Engine**: Modular Machine Learning pipeline using **TF-IDF + Logistic Regression** coupled with lexicon heuristics to extract confidence scores, keywords, and topics.
3. **Manual & Bulk Analysis**: Analyze single text entries or upload bulk **CSV and Excel (.xlsx)** files with header mapping.
4. **Improvement Areas Module**: Automatically groups negative feedback and recurring complaints into high/medium/low priority issues with AI-suggested recommendations and representative quotes.
5. **All Feedback Data Table**: Search, filter by sentiment/category/source/rating, sort, view detailed breakdowns, edit, and perform single or bulk deletions.
6. **Trends & Reports Module**: Track daily/weekly/monthly trends, top positive/negative themes, export CSV reports, and print executive PDF summaries.
7. **MySQL & Fallback Engine**: Fully configured for **MySQL database (`feedbacksense_db`)** with dynamic SQLite fallback support so the system runs smoothly in any environment out-of-the-box.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Modern SaaS Navy/Light Theme), Vanilla JavaScript (ES6+), Chart.js, Font Awesome 6.
- **Backend**: Python 3.11+, FastAPI REST API, Uvicorn ASGI Server, Pydantic v2, SQLAlchemy 2.0 ORM, Pandas, Scikit-learn ML.
- **Database**: MySQL Server (Database: `feedbacksense_db`).

---

## 📁 Project Directory Structure

```
feedback/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application Entry & Static Mount
│   │   ├── core/
│   │   │   └── config.py            # Environment Configuration & Pydantic Settings
│   │   ├── database/
│   │   │   └── connection.py        # MySQL Engine & Session Factory (with SQLite Fallback)
│   │   ├── models/
│   │   │   ├── user.py              # User ORM Model
│   │   │   ├── feedback.py          # Feedback ORM Model
│   │   │   ├── analysis.py          # Sentiment Analysis ORM Model
│   │   │   └── issue.py             # Improvement Issue ORM Model & Join Table
│   │   ├── schemas/
│   │   │   ├── feedback.py          # Request & Response Pydantic Schemas
│   │   │   └── analytics.py         # KPI & Analytics Pydantic Schemas
│   │   ├── services/
│   │   │   ├── sentiment_service.py # ML Sentiment Classifier Engine & Keyword Extractor
│   │   │   ├── issue_detection_service.py # Grouping & Priority Issue Service
│   │   │   └── report_service.py    # Analytics Computation & Trends Service
│   │   ├── routers/
│   │   │   ├── feedback.py          # CRUD & Upload REST Endpoints
│   │   │   ├── analytics.py         # Dashboard & KPI Endpoints
│   │   │   ├── reports.py           # Export Endpoints
│   │   │   └── settings.py          # System Settings Endpoints
│   │   └── utils/
│   │       └── text_processing.py   # Text Cleaning & Keyword Extraction Utilities
│   ├── .env                         # Active Environment Variables
│   ├── .env.example                 # Environment Template
│   ├── init_db.sql                  # MySQL Initialization & Table Creation Script
│   └── requirements.txt             # Python Package Dependencies
├── frontend/
│   ├── index.html                   # Dashboard Page
│   ├── analyze.html                 # Feedback Input & Bulk Upload Page
│   ├── feedback.html                # Searchable Feedback Table & Management
│   ├── improvements.html             # Discovered Improvement Areas & Recommendations
│   ├── reports.html                 # Trends, Comparison Charts & CSV Exports
│   ├── settings.html                # System Configuration & Status Page
│   ├── css/
│   │   ├── style.css                # Primary SaaS Design System
│   │   └── responsive.css           # Mobile & Tablet Styles
│   └── js/
│       ├── api.js                   # Centralized REST API Fetch Wrapper
│       ├── app.js                   # Navigation & Global Utilities
│       ├── dashboard.js             # Dashboard Charts & KPI Logic
│       ├── analyze.js               # Manual & Bulk Upload Handlers
│       ├── feedback.js              # Table Pagination, Filter & Modal Handlers
│       ├── improvements.js          # Issue Cards Renderer
│       └── reports.js               # Trend Charts & Export Handlers
├── sample_data/
│   └── sample_feedback.csv          # Sample Customer Review Dataset
└── README.md                        # Setup Instructions & Documentation
```

---

## 🚀 Step-by-Step Windows Installation & Execution Guide

### Step 1: Open Command Prompt or PowerShell
Navigate to the backend folder:
```cmd
cd C:\Users\myala\.gemini\antigravity\scratch\feedback\backend
```

### Step 2: Install Required Dependencies
Ensure Python 3.11+ is installed, then run:
```cmd
pip install -r requirements.txt
```

### Step 3: Database Setup (MySQL)

1. Start your MySQL Server (via MySQL Workbench, XAMPP, or Windows Service).
2. Log into MySQL and run the database creation script:
```sql
mysql -u root -p < init_db.sql
```
*(Or execute `init_db.sql` directly inside MySQL Workbench / phpMyAdmin).*

3. Configure your MySQL credentials in `backend/.env`:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=feedbacksense_db
```

> **Note**: If MySQL is not running on your machine, FeedbackSense AI will automatically use its built-in SQLite fallback (`feedbacksense.db`) so you can run and test the app immediately without configuration errors!

### Step 4: Run the FastAPI Server with Uvicorn

From the `backend/` directory, start the backend server:

**Using Python:**
```cmd
python app/main.py
```

**Or using Uvicorn directly:**
```cmd
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 Opening the Application

Once the server is running:

1. **Web Dashboard**: Open your browser and navigate to:
   `http://127.0.0.1:8000/` or open `frontend/index.html` directly.

2. **Interactive API Documentation (Swagger UI)**:
   Navigate to: `http://127.0.0.1:8000/docs`

---

## 🧪 Demonstration & Testing Checklist

1. **Automatic Data Seeding**: On initial launch, the system automatically populates sample feedback into the database. You can also click **"Seed Sample Data"** on the Settings or Feedback pages.
2. **Manual Analysis**: Go to **Analyze Feedback -> Method A**, enter text (e.g., *"The app crashes every time I open settings"*), set rating to `1`, and click **Analyze Feedback**.
3. **Bulk Upload**: Go to **Analyze Feedback -> Method B**, upload `sample_data/sample_feedback.csv`, map the columns, and click **Start Bulk Upload**.
4. **Inspect Dashboard**: View real-time KPI card updates and live Chart.js figures on the main Dashboard.
5. **Manage Data**: Search, filter, edit, or delete feedback entries in the **All Feedback** table.
6. **Export Reports**: Go to **Trends & Reports** and click **Export CSV Report** or **Print / Save PDF**.

---

## 🔧 Troubleshooting Guide

- **Database Connection Failure**: Verify `MYSQL_USER` and `MYSQL_PASSWORD` in `.env`. Ensure MySQL service is started.
- **Port Conflict (8000)**: If port `8000` is occupied, change `API_PORT=8080` in `.env` and start Uvicorn with `--port 8080`.
- **CORS Blocked**: Update `CORS_ORIGINS` in `backend/.env` to include your frontend server's origin.

---

## 📄 License
Created for FeedbackSense AI - Sentiment Analysis & Feedback Intelligence System.
