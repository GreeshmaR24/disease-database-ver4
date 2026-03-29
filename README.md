# 🧬 BioBase — Human Disease & Cancer Biomarker Database

> A professional, AI-assisted bioinformatics web application built with Flask, SQLite, and vanilla JS.  
> Inspired by MalaCards and OMIM. Built for academic purposes.

---

## 📁 Project Structure

```
biomarker_db/
├── app.py                  # Flask backend — all routes, DB init, AI search
├── requirements.txt        # Python dependencies (Flask only)
├── biomarker.db            # SQLite database (auto-created on first run)
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Shared layout (navbar + footer)
│   ├── index.html          # Home page with hero + charts
│   ├── diseases.html       # Disease browser with category filters
│   ├── disease_detail.html # Full disease page with all clinical data
│   ├── biomarkers.html     # Cancer biomarker cards + chart
│   ├── search.html         # AI-powered search page
│   ├── compare.html        # Disease comparison tool
│   ├── bookmarks.html      # Saved/bookmarked diseases
│   └── 404.html            # Custom 404 page
│
└── static/
    ├── css/
    │   └── style.css       # Full custom stylesheet (no Bootstrap)
    └── js/
        └── main.js         # Search, charts, bookmarks, compare logic
```

---

## 🚀 How to Run

### 1. Prerequisites
- Python 3.8+ installed
- pip available

### 2. Install Dependencies
```bash
cd biomarker_db
pip install -r requirements.txt
```

### 3. Run the App
```bash
python app.py
```

The server starts at **http://127.0.0.1:5000**

> The SQLite database (`biomarker.db`) is created automatically with all sample data on first run.

---

## 🗄️ Database Design

### Tables

#### `diseases`
| Column       | Type    | Description                          |
|--------------|---------|--------------------------------------|
| id           | INTEGER | Primary key                          |
| name         | TEXT    | Disease name                         |
| category     | TEXT    | Genetic / Neurological / Cancer / Metabolic |
| description  | TEXT    | Clinical overview                    |
| symptoms     | TEXT    | JSON array of symptoms               |
| genes        | TEXT    | JSON array of associated gene symbols |
| proteins     | TEXT    | JSON array of associated proteins    |
| diagnosis    | TEXT    | Diagnostic methods                   |
| treatment    | TEXT    | Treatment overview                   |
| prevalence   | TEXT    | Epidemiology data                    |
| inheritance  | TEXT    | Autosomal Dominant/Recessive/X-linked |
| omim_id      | TEXT    | OMIM reference number                |
| tags         | TEXT    | JSON array for smart search          |

#### `biomarkers`
| Column               | Type    | Description                        |
|----------------------|---------|------------------------------------|
| id                   | INTEGER | Primary key                        |
| name                 | TEXT    | Biomarker name                     |
| cancer_type          | TEXT    | Associated cancer                  |
| gene_protein         | TEXT    | Gene / protein involved            |
| relevance            | TEXT    | Diagnostic / Prognostic / Predictive |
| detection_method     | TEXT    | Lab assay method                   |
| normal_range         | TEXT    | Reference range                    |
| clinical_significance| TEXT    | Clinical use description           |
| approved_test        | TEXT    | FDA/EMA approval status            |

#### `bookmarks`
| Column     | Type     | Description               |
|------------|----------|---------------------------|
| id         | INTEGER  | Primary key               |
| session_id | TEXT     | Flask session identifier  |
| disease_id | INTEGER  | FK → diseases.id          |
| created_at | DATETIME | Timestamp                 |

---

## 🤖 AI Integration — How It Works

The AI feature is a **rule-based NLP system** that qualifies as AI because it:

1. **Tokenises** the user's query using regex (`re.findall`) — core NLP technique
2. **Matches** tokens against a curated **symptom–disease ontology** (knowledge base)
3. **Scores** each candidate disease by number of matching evidence tokens
4. **Ranks** results by relevance score (highest first)
5. **Fuzzy matching** via Python's `difflib.get_close_matches` for "Did you mean?"

### Example
User types: *"tremor, difficulty walking"*

→ Tokeniser produces: `["tremor", "difficulty", "walking"]`  
→ "tremor" matches: Parkinson's Disease (score+1), Huntington's Disease (score+1)  
→ "walking" does not match any keyword  
→ Result: Parkinson's and Huntington's ranked with score 1 each  

This is the same principle used in early expert systems and clinical decision support tools.

---

## 🌟 Features Summary

| Feature                   | Description                                           |
|---------------------------|-------------------------------------------------------|
| Disease Database          | 12 diseases with full clinical detail                 |
| Cancer Biomarkers         | 8 validated biomarkers with FDA status                |
| AI Symptom Search         | Rule-based NLP scoring + knowledge base               |
| Fuzzy "Did You Mean?"     | difflib sequence matching                             |
| Disease Comparison Tool   | Side-by-side comparison of any 2 diseases             |
| Bookmark / Save           | Session-based disease bookmarking                     |
| Dynamic Charts            | Doughnut + bar charts via Chart.js                    |
| Category Filtering        | Filter diseases by category                           |
| REST API                  | JSON endpoints for all data                           |
| Responsive Design         | Mobile-friendly, custom CSS                           |

---

## 🔌 API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | `/api/diseases`       | All diseases (summary)                   |
| GET    | `/api/disease/<id>`   | Single disease full detail               |
| GET    | `/api/biomarkers`     | All biomarkers                           |
| GET    | `/api/search?q=...`   | AI-powered search (diseases+biomarkers)  |
| GET    | `/api/compare?id=&id=`| Compare two diseases                     |
| POST   | `/api/bookmark/<id>`  | Toggle bookmark (session-based)          |

---

## 📊 Sample Diseases Included

1. Cystic Fibrosis (Genetic)
2. Huntington's Disease (Neurological)
3. Breast Cancer / HBOC (Cancer)
4. Type 2 Diabetes Mellitus (Metabolic)
5. Alzheimer's Disease (Neurological)
6. Sickle Cell Anemia (Genetic)
7. Parkinson's Disease (Neurological)
8. Marfan Syndrome (Genetic)
9. Colorectal Cancer / Lynch Syndrome (Cancer)
10. Hemophilia A (Genetic)
11. Wilson's Disease (Metabolic)
12. Phenylketonuria / PKU (Metabolic)

## 🎗️ Sample Biomarkers Included

1. PSA — Prostate Cancer
2. CA 125 — Ovarian Cancer
3. CEA — Colorectal Cancer
4. HER2/neu — Breast/Gastric Cancer
5. AFP — Hepatocellular Carcinoma
6. EGFR Mutation — NSCLC
7. BRCA1/2 — Breast/Ovarian Cancer
8. PD-L1 — Multiple Cancers

---

## 📝 Data Sources

Data is **manually curated** and inspired by:
- OMIM (Online Mendelian Inheritance in Man)
- MalaCards — Human Disease Database
- ClinGen
- FDA biomarker qualification database
- Published clinical guidelines (NCCN, ASCO, EMA)

> ⚠️ **Not scraped or copied.** All entries are original summaries written for educational purposes.

---

*Built with ❤️ using Flask · SQLite · Chart.js · Google Fonts (DM Serif Display + DM Sans)*
