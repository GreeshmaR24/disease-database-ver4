from flask import Flask, render_template, jsonify, request, session
import sqlite3
import json
import os
import re
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = "biomarker_db_secret_2024"

# ✅ FIX: Proper DB path for Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "biomarker.db")

# Custom Jinja2 filter
@app.template_filter("from_json")
def from_json_filter(value):
    try:
        return json.loads(value or "[]")
    except Exception:
        return []


# ─── Database Helpers ─────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(sql, args=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return (rows[0] if rows else None) if one else rows


# ─── Database Initialization ──────────────────────────────

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        symptoms TEXT,
        genes TEXT,
        proteins TEXT,
        diagnosis TEXT,
        treatment TEXT,
        prevalence TEXT,
        inheritance TEXT,
        omim_id TEXT,
        tags TEXT
    );

    CREATE TABLE IF NOT EXISTS biomarkers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cancer_type TEXT,
        gene_protein TEXT,
        relevance TEXT,
        detection_method TEXT,
        normal_range TEXT,
        clinical_significance TEXT,
        approved_test TEXT
    );
    """)

    # Only insert if empty
    if cur.execute("SELECT COUNT(*) FROM diseases").fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO diseases (name, category, description, symptoms, genes, proteins, diagnosis, treatment, prevalence, inheritance, omim_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Cystic Fibrosis",
            "Genetic",
            "A genetic disorder affecting lungs and digestive system.",
            json.dumps(["Cough", "Breathing difficulty"]),
            json.dumps(["CFTR"]),
            json.dumps(["CFTR Protein"]),
            "Sweat test",
            "Medications + therapy",
            "1 in 3000",
            "Autosomal Recessive",
            "219700",
            json.dumps(["lung", "genetic"])
        ))

    if cur.execute("SELECT COUNT(*) FROM biomarkers").fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO biomarkers (name, cancer_type, gene_protein, relevance, detection_method, normal_range, clinical_significance, approved_test)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "PSA",
            "Prostate Cancer",
            "KLK3",
            "Diagnostic",
            "Blood test",
            "<4 ng/mL",
            "Elevated in prostate cancer",
            "FDA approved"
        ))

    conn.commit()
    conn.close()


# ✅ FIX: Initialize DB for Render (VERY IMPORTANT)
init_db()


# ─── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    stats = {
        "disease_count": query_db("SELECT COUNT(*) as c FROM diseases", one=True)["c"],
        "biomarker_count": query_db("SELECT COUNT(*) as c FROM biomarkers", one=True)["c"],
    }
    return render_template("index.html", stats=stats)


@app.route("/diseases")
def diseases_page():
    rows = query_db("SELECT * FROM diseases")
    return render_template("diseases.html", diseases=rows)


@app.route("/biomarkers")
def biomarkers_page():
    rows = query_db("SELECT * FROM biomarkers")
    return render_template("biomarkers.html", biomarkers=rows)


# ─── Error Handler ───────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404


# ─── Entry ───────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
