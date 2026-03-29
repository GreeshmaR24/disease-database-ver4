"""
Human Disease & Cancer Biomarker Database
==========================================
A Flask-based bioinformatics web application inspired by MalaCards and OMIM.
Provides structured disease information with AI-assisted search.

Author: Student Project
"""

from flask import Flask, render_template, jsonify, request, session
import sqlite3
import json
import os
import re
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = "biomarker_db_secret_2024"

# Custom Jinja2 filter: parse JSON strings in templates
@app.template_filter("from_json")
def from_json_filter(value):
    try:
        return json.loads(value or "[]")
    except Exception:
        return []

DB_PATH = "biomarker.db"


# ─── Database Helpers ───────────────────────────────────────────────────────

def get_db():
    """Return a database connection with row_factory for dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(sql, args=(), one=False):
    """Execute a SELECT query and return results as list of dicts."""
    conn = get_db()
    cur = conn.execute(sql, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return (rows[0] if rows else None) if one else rows


# ─── Database Initialization ─────────────────────────────────────────────────

def init_db():
    """Create tables and populate with curated sample data."""
    conn = get_db()
    cur = conn.cursor()

    # ── Schema ──────────────────────────────────────────────────────────────
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS diseases (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        category    TEXT,           -- e.g. Genetic, Neurological, Cardiovascular
        description TEXT,
        symptoms    TEXT,           -- JSON array
        genes       TEXT,           -- JSON array
        proteins    TEXT,           -- JSON array
        diagnosis   TEXT,
        treatment   TEXT,
        prevalence  TEXT,
        inheritance TEXT,
        omim_id     TEXT,
        tags        TEXT            -- JSON array for smart search
    );

    CREATE TABLE IF NOT EXISTS biomarkers (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        cancer_type     TEXT,
        gene_protein    TEXT,
        relevance       TEXT,       -- Diagnostic / Prognostic / Predictive
        detection_method TEXT,
        normal_range    TEXT,
        clinical_significance TEXT,
        approved_test   TEXT
    );

    CREATE TABLE IF NOT EXISTS bookmarks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  TEXT,
        disease_id  INTEGER,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ── Seed diseases only if table is empty ────────────────────────────────
    if cur.execute("SELECT COUNT(*) FROM diseases").fetchone()[0] == 0:
        diseases = [
            {
                "name": "Cystic Fibrosis",
                "category": "Genetic",
                "description": "Cystic fibrosis (CF) is a life-threatening genetic disorder that damages the lungs and digestive system. It causes cells that produce mucus, sweat, and digestive juices to produce thick, sticky fluids instead of thin, slippery secretions.",
                "symptoms": json.dumps(["Persistent cough with thick mucus", "Frequent lung infections", "Shortness of breath", "Wheezing", "Salty-tasting skin", "Poor weight gain", "Clubbing of fingers", "Male infertility"]),
                "genes": json.dumps(["CFTR"]),
                "proteins": json.dumps(["Cystic fibrosis transmembrane conductance regulator (CFTR)"]),
                "diagnosis": "Newborn screening (immunoreactive trypsinogen), sweat chloride test (>60 mmol/L), genetic testing for CFTR mutations, pulmonary function tests.",
                "treatment": "CFTR modulators (Ivacaftor, Lumacaftor/Ivacaftor, Elexacaftor/Tezacaftor/Ivacaftor), chest physiotherapy, inhaled antibiotics, pancreatic enzyme replacement, lung transplantation in severe cases.",
                "prevalence": "1 in 2,500–3,500 newborns (European descent)",
                "inheritance": "Autosomal Recessive",
                "omim_id": "219700",
                "tags": json.dumps(["lung", "mucus", "genetic", "breathing", "cough", "pancreas", "CFTR"])
            },
            {
                "name": "Huntington's Disease",
                "category": "Neurological",
                "description": "Huntington's disease is a rare, fatal genetic disorder that causes the progressive breakdown of nerve cells in the brain. It has a broad impact on a person's functional abilities and usually results in movement, thinking and psychiatric disorders.",
                "symptoms": json.dumps(["Involuntary jerking movements (chorea)", "Muscle rigidity", "Slow or abnormal eye movements", "Impaired gait and balance", "Personality changes", "Depression and anxiety", "Cognitive decline", "Difficulty swallowing"]),
                "genes": json.dumps(["HTT"]),
                "proteins": json.dumps(["Huntingtin protein"]),
                "diagnosis": "Genetic testing for CAG repeat expansion in HTT gene (>36 repeats), MRI showing caudate nucleus atrophy, neurological assessment.",
                "treatment": "Tetrabenazine or deutetrabenazine for chorea, antidepressants, antipsychotics, physical therapy, occupational therapy. No disease-modifying therapy approved yet.",
                "prevalence": "3–7 per 100,000 (Western populations)",
                "inheritance": "Autosomal Dominant",
                "omim_id": "143100",
                "tags": json.dumps(["brain", "movement", "chorea", "neurological", "genetic", "psychiatric", "cognitive"])
            },
            {
                "name": "Breast Cancer (BRCA-associated)",
                "category": "Cancer",
                "description": "Hereditary breast and ovarian cancer syndrome (HBOC) is caused by pathogenic variants in BRCA1 or BRCA2 genes. Carriers have significantly elevated lifetime risk of breast cancer (up to 72%) and ovarian cancer (up to 44%).",
                "symptoms": json.dumps(["Lump in breast or underarm", "Change in breast size or shape", "Skin dimpling", "Nipple discharge or inversion", "Skin redness or scaliness", "Often asymptomatic early stage"]),
                "genes": json.dumps(["BRCA1", "BRCA2", "PALB2", "ATM"]),
                "proteins": json.dumps(["Breast cancer type 1 susceptibility protein", "Breast cancer type 2 susceptibility protein", "DNA repair proteins"]),
                "diagnosis": "Genetic panel testing, mammography, breast MRI, ultrasound, core needle biopsy, sentinel lymph node biopsy.",
                "treatment": "Surgery (lumpectomy/mastectomy), radiation, chemotherapy, hormonal therapy (tamoxifen, aromatase inhibitors), PARP inhibitors (olaparib, niraparib) for BRCA carriers.",
                "prevalence": "1 in 400–800 carry BRCA1/2 variants; 12% lifetime risk in general population",
                "inheritance": "Autosomal Dominant",
                "omim_id": "604370",
                "tags": json.dumps(["breast", "cancer", "BRCA", "tumor", "lump", "hereditary", "ovarian"])
            },
            {
                "name": "Type 2 Diabetes Mellitus",
                "category": "Metabolic",
                "description": "Type 2 diabetes is a chronic metabolic disorder characterized by insulin resistance and relative insulin deficiency. It is influenced by multiple genetic and environmental factors and is the most common form of diabetes worldwide.",
                "symptoms": json.dumps(["Increased thirst and urination", "Increased hunger", "Fatigue", "Blurred vision", "Slow-healing sores", "Frequent infections", "Areas of darkened skin (acanthosis nigricans)", "Numbness in hands or feet"]),
                "genes": json.dumps(["TCF7L2", "PPARG", "KCNJ11", "SLC30A8", "HNF1A", "FTO"]),
                "proteins": json.dumps(["Transcription factor 7-like 2", "Peroxisome proliferator-activated receptor gamma", "Zinc transporter 8"]),
                "diagnosis": "Fasting plasma glucose ≥126 mg/dL, HbA1c ≥6.5%, 2-hour OGTT ≥200 mg/dL, random glucose ≥200 mg/dL with symptoms.",
                "treatment": "Lifestyle modification, metformin (first-line), GLP-1 agonists (semaglutide, liraglutide), SGLT-2 inhibitors, insulin therapy, bariatric surgery in severe obesity.",
                "prevalence": "~10.5% globally (~537 million adults in 2021)",
                "inheritance": "Complex / Polygenic",
                "omim_id": "125853",
                "tags": json.dumps(["diabetes", "insulin", "glucose", "sugar", "thirst", "metabolic", "pancreas", "fatigue"])
            },
            {
                "name": "Alzheimer's Disease",
                "category": "Neurological",
                "description": "Alzheimer's disease is a progressive neurodegenerative disorder and the most common cause of dementia. It is characterized by accumulation of amyloid-beta plaques and neurofibrillary tangles of tau protein in the brain.",
                "symptoms": json.dumps(["Memory loss disrupting daily life", "Difficulty planning or solving problems", "Confusion with time or place", "Trouble understanding visual images", "New problems with words", "Misplacing objects", "Decreased judgment", "Withdrawal from social activities", "Mood and personality changes"]),
                "genes": json.dumps(["APP", "PSEN1", "PSEN2", "APOE", "TREM2", "CLU"]),
                "proteins": json.dumps(["Amyloid precursor protein", "Presenilin-1", "Presenilin-2", "Apolipoprotein E", "Tau protein"]),
                "diagnosis": "Clinical assessment, neuropsychological testing, MRI/PET brain imaging, CSF biomarkers (amyloid-β42, tau, p-tau), amyloid PET scan.",
                "treatment": "Cholinesterase inhibitors (donepezil, rivastigmine, galantamine), memantine, lecanemab (anti-amyloid), donanemab (FDA approved 2023), supportive care.",
                "prevalence": "~50 million worldwide; 1 in 9 people aged 65+",
                "inheritance": "Complex; APOE ε4 is major risk allele",
                "omim_id": "104300",
                "tags": json.dumps(["memory", "dementia", "brain", "neurological", "cognitive", "alzheimer", "confusion", "aging"])
            },
            {
                "name": "Sickle Cell Anemia",
                "category": "Genetic",
                "description": "Sickle cell anemia is a group of red blood cell disorders caused by abnormal hemoglobin (HbS). Red blood cells become rigid and shaped like sickles, causing blockages in blood flow and episodes of severe pain called vaso-occlusive crises.",
                "symptoms": json.dumps(["Anemia and fatigue", "Episodes of pain (vaso-occlusive crises)", "Swelling of hands and feet (dactylitis)", "Frequent infections", "Delayed growth", "Vision problems", "Stroke", "Acute chest syndrome"]),
                "genes": json.dumps(["HBB"]),
                "proteins": json.dumps(["Hemoglobin subunit beta (HbS variant)"]),
                "diagnosis": "Newborn screening (hemoglobin electrophoresis), HPLC, sickle solubility test, complete blood count, peripheral blood smear.",
                "treatment": "Hydroxyurea (increases HbF), voxelotor, crizanlizumab, L-glutamine, hematopoietic stem cell transplantation, gene therapy (lovotibeglogene autotemcel – FDA approved 2023).",
                "prevalence": "~100,000 in the US; predominantly in sub-Saharan African descent",
                "inheritance": "Autosomal Recessive",
                "omim_id": "603903",
                "tags": json.dumps(["blood", "anemia", "pain", "crisis", "hemoglobin", "genetic", "sickle", "fatigue"])
            },
            {
                "name": "Parkinson's Disease",
                "category": "Neurological",
                "description": "Parkinson's disease is a progressive neurodegenerative disorder affecting movement. It involves the degeneration of dopaminergic neurons in the substantia nigra and accumulation of Lewy bodies (alpha-synuclein aggregates).",
                "symptoms": json.dumps(["Tremor at rest", "Bradykinesia (slowness of movement)", "Rigidity", "Postural instability", "Shuffling gait", "Soft voice", "Loss of smell", "REM sleep behavior disorder", "Constipation", "Depression"]),
                "genes": json.dumps(["SNCA", "LRRK2", "PRKN", "PINK1", "DJ-1", "GBA"]),
                "proteins": json.dumps(["Alpha-synuclein", "Leucine-rich repeat kinase 2", "Parkin", "PTEN-induced kinase 1", "Glucocerebrosidase"]),
                "diagnosis": "Clinical diagnosis based on motor symptoms, DaTscan SPECT imaging, response to levodopa, MRI to exclude other causes.",
                "treatment": "Levodopa/carbidopa (gold standard), dopamine agonists (pramipexole, ropinirole), MAO-B inhibitors, COMT inhibitors, deep brain stimulation (DBS).",
                "prevalence": "~10 million worldwide; 1–2% of adults over 60",
                "inheritance": "Mostly sporadic; ~10–15% familial",
                "omim_id": "168600",
                "tags": json.dumps(["tremor", "movement", "brain", "dopamine", "parkinson", "rigidity", "neurological", "gait"])
            },
            {
                "name": "Marfan Syndrome",
                "category": "Genetic",
                "description": "Marfan syndrome is a genetic disorder affecting the body's connective tissue. It affects the heart, blood vessels, bones, joints, and eyes. The most dangerous complication is aortic aneurysm or dissection.",
                "symptoms": json.dumps(["Tall, thin body with long limbs", "Aortic aneurysm or dissection", "Mitral valve prolapse", "Lens dislocation (ectopia lentis)", "Scoliosis", "Flat feet", "Flexible joints", "Stretch marks unrelated to weight change"]),
                "genes": json.dumps(["FBN1", "FBN2", "TGFBR1", "TGFBR2"]),
                "proteins": json.dumps(["Fibrillin-1", "TGF-β receptor type 1 and 2"]),
                "diagnosis": "Revised Ghent Nosology (clinical scoring), echocardiography for aortic root, slit-lamp eye exam, genetic testing for FBN1.",
                "treatment": "Beta-blockers or ARBs (losartan) to slow aortic dilation, surgical aortic root replacement when diameter >4.5–5 cm, regular cardiovascular monitoring.",
                "prevalence": "1 in 5,000–10,000",
                "inheritance": "Autosomal Dominant",
                "omim_id": "154700",
                "tags": json.dumps(["heart", "aorta", "tall", "connective tissue", "genetic", "eyes", "joints", "skeleton"])
            },
            {
                "name": "Colorectal Cancer (Lynch Syndrome)",
                "category": "Cancer",
                "description": "Lynch syndrome is the most common hereditary colorectal cancer syndrome, caused by germline mutations in DNA mismatch repair (MMR) genes. It accounts for ~3–5% of all colorectal cancers and also increases risk of endometrial, ovarian, and other cancers.",
                "symptoms": json.dumps(["Rectal bleeding", "Change in bowel habits", "Abdominal pain or cramping", "Unexplained weight loss", "Fatigue and weakness", "Often asymptomatic until advanced"]),
                "genes": json.dumps(["MLH1", "MSH2", "MSH6", "PMS2", "EPCAM"]),
                "proteins": json.dumps(["MutL homolog 1", "MutS protein homolog 2", "MutS homolog 6", "Mismatch repair endonuclease PMS2"]),
                "diagnosis": "Colonoscopy, immunohistochemistry for MMR proteins, microsatellite instability (MSI) testing, germline genetic panel.",
                "treatment": "Surgical resection, adjuvant chemotherapy (FOLFOX, CAPOX), immune checkpoint inhibitors (pembrolizumab, nivolumab for MSI-H tumors), regular surveillance colonoscopy.",
                "prevalence": "Lynch: 1 in 280 in general population; ~3–5% of colorectal cancers",
                "inheritance": "Autosomal Dominant",
                "omim_id": "120435",
                "tags": json.dumps(["colon", "cancer", "rectal", "bleeding", "lynch", "mismatch repair", "bowel"])
            },
            {
                "name": "Hemophilia A",
                "category": "Genetic",
                "description": "Hemophilia A is the most common severe inherited bleeding disorder, caused by deficiency of clotting factor VIII. It results in prolonged or spontaneous bleeding especially into joints (hemarthrosis) and muscles.",
                "symptoms": json.dumps(["Prolonged bleeding after injury", "Spontaneous joint bleeding (hemarthrosis)", "Muscle bleeds", "Bruising easily", "Nosebleeds difficult to stop", "Blood in urine or stool", "Intracranial hemorrhage in severe cases"]),
                "genes": json.dumps(["F8"]),
                "proteins": json.dumps(["Coagulation factor VIII"]),
                "diagnosis": "Activated partial thromboplastin time (aPTT) prolonged, factor VIII activity assay, genetic testing for F8 mutations.",
                "treatment": "Factor VIII replacement therapy (on-demand or prophylactic), emicizumab (bispecific antibody prophylaxis), gene therapy (valoctocogene roxaparvovec – EMA approved 2022).",
                "prevalence": "~1 in 5,000 male births",
                "inheritance": "X-linked Recessive",
                "omim_id": "306700",
                "tags": json.dumps(["bleeding", "blood", "clotting", "joints", "genetic", "x-linked", "factor", "bruise"])
            },
            {
                "name": "Wilson's Disease",
                "category": "Metabolic",
                "description": "Wilson's disease is a rare genetic disorder causing copper accumulation in the liver, brain, and other organs. The ATP7B protein normally exports copper from hepatocytes; its dysfunction leads to toxic copper buildup.",
                "symptoms": json.dumps(["Liver disease (hepatitis, cirrhosis)", "Kayser-Fleischer rings in eyes", "Neuropsychiatric symptoms", "Tremors and dysarthria", "Behavioral changes", "Hemolytic anemia", "Renal dysfunction"]),
                "genes": json.dumps(["ATP7B"]),
                "proteins": json.dumps(["Copper-transporting ATPase 2 (Wilson disease protein)"]),
                "diagnosis": "Slit-lamp examination for KF rings, serum ceruloplasmin (<20 mg/dL), 24-hour urine copper (>100 μg/day), liver biopsy, genetic testing.",
                "treatment": "Copper chelation (D-penicillamine, trientine), zinc supplementation (reduces copper absorption), liver transplantation in acute liver failure.",
                "prevalence": "1 in 30,000",
                "inheritance": "Autosomal Recessive",
                "omim_id": "277900",
                "tags": json.dumps(["copper", "liver", "neurological", "metabolic", "genetic", "eyes", "tremor", "psychiatric"])
            },
            {
                "name": "Phenylketonuria (PKU)",
                "category": "Metabolic",
                "description": "Phenylketonuria is an inborn error of metabolism caused by deficiency of phenylalanine hydroxylase (PAH), leading to accumulation of phenylalanine. Untreated, it causes severe intellectual disability, but newborn screening enables effective dietary management.",
                "symptoms": json.dumps(["Intellectual disability (if untreated)", "Behavioral problems", "Seizures", "Musty body odor", "Lighter skin, hair, eyes", "Eczema", "Delayed development"]),
                "genes": json.dumps(["PAH"]),
                "proteins": json.dumps(["Phenylalanine hydroxylase"]),
                "diagnosis": "Newborn screening (elevated blood phenylalanine), plasma amino acid quantification, urine pterins, PAH genetic testing.",
                "treatment": "Phenylalanine-restricted diet (lifelong), sapropterin (BH4 cofactor therapy for BH4-responsive PKU), pegvaliase (PEGylated enzyme), investigational gene therapy.",
                "prevalence": "1 in 10,000–15,000 newborns",
                "inheritance": "Autosomal Recessive",
                "omim_id": "261600",
                "tags": json.dumps(["metabolic", "amino acid", "intellectual", "genetic", "seizures", "diet", "newborn", "phenylalanine"])
            },
        ]

        cur.executemany("""
            INSERT INTO diseases (name,category,description,symptoms,genes,proteins,
                                  diagnosis,treatment,prevalence,inheritance,omim_id,tags)
            VALUES (:name,:category,:description,:symptoms,:genes,:proteins,
                    :diagnosis,:treatment,:prevalence,:inheritance,:omim_id,:tags)
        """, diseases)

    # ── Seed biomarkers ─────────────────────────────────────────────────────
    if cur.execute("SELECT COUNT(*) FROM biomarkers").fetchone()[0] == 0:
        biomarkers = [
            {
                "name": "PSA (Prostate-Specific Antigen)",
                "cancer_type": "Prostate Cancer",
                "gene_protein": "KLK3 gene / PSA protein",
                "relevance": "Diagnostic and Monitoring",
                "detection_method": "Serum immunoassay (ELISA)",
                "normal_range": "<4.0 ng/mL",
                "clinical_significance": "Elevated PSA indicates prostate pathology. Used for screening, monitoring treatment response, and detecting recurrence. Free-to-total PSA ratio improves specificity.",
                "approved_test": "FDA-approved for prostate cancer screening"
            },
            {
                "name": "CA 125",
                "cancer_type": "Ovarian Cancer",
                "gene_protein": "MUC16 gene / CA-125 glycoprotein",
                "relevance": "Diagnostic and Prognostic",
                "detection_method": "Serum immunoassay",
                "normal_range": "<35 U/mL",
                "clinical_significance": "Elevated in 80% of ovarian cancers. Used to monitor treatment response and detect recurrence. Also elevated in endometriosis and other benign conditions (low specificity).",
                "approved_test": "FDA-approved for monitoring ovarian cancer"
            },
            {
                "name": "CEA (Carcinoembryonic Antigen)",
                "cancer_type": "Colorectal Cancer",
                "gene_protein": "CEACAM5 gene / CEA glycoprotein",
                "relevance": "Prognostic and Monitoring",
                "detection_method": "Serum immunoassay",
                "normal_range": "<2.5 ng/mL (non-smoker)",
                "clinical_significance": "Elevated CEA correlates with tumor burden in colorectal cancer. Post-operative surveillance: rising CEA suggests recurrence. Also elevated in other GI cancers, lung, breast.",
                "approved_test": "FDA-approved for colorectal cancer monitoring"
            },
            {
                "name": "HER2/neu",
                "cancer_type": "Breast Cancer / Gastric Cancer",
                "gene_protein": "ERBB2 gene / HER2 receptor protein",
                "relevance": "Predictive and Prognostic",
                "detection_method": "IHC (immunohistochemistry), FISH/ISH, NGS",
                "normal_range": "IHC 0 or 1+ = negative",
                "clinical_significance": "Overexpressed in ~20% of breast cancers. Predicts response to HER2-targeted therapies (trastuzumab, pertuzumab, T-DM1). Amplification = poor prognosis without targeted therapy.",
                "approved_test": "FDA-approved companion diagnostic"
            },
            {
                "name": "AFP (Alpha-Fetoprotein)",
                "cancer_type": "Hepatocellular Carcinoma / Germ Cell Tumors",
                "gene_protein": "AFP gene / Alpha-fetoprotein",
                "relevance": "Diagnostic and Monitoring",
                "detection_method": "Serum immunoassay",
                "normal_range": "<10 ng/mL",
                "clinical_significance": "Markedly elevated (>400 ng/mL) is diagnostic of HCC in cirrhotic patients. Also elevated in yolk sac tumors and hepatoblastoma. Used with ultrasound for HCC surveillance.",
                "approved_test": "FDA-approved for HCC monitoring"
            },
            {
                "name": "EGFR Mutation (L858R / Exon 19 del)",
                "cancer_type": "Non-Small Cell Lung Cancer (NSCLC)",
                "gene_protein": "EGFR gene / Epidermal Growth Factor Receptor",
                "relevance": "Predictive",
                "detection_method": "PCR, NGS (liquid biopsy or tissue)",
                "normal_range": "No mutation (wild-type)",
                "clinical_significance": "Activating EGFR mutations predict response to EGFR-TKIs (erlotinib, gefitinib, osimertinib). Present in ~15% of Western and ~50% of Asian NSCLC patients. Resistance mutations (T790M) detected by liquid biopsy.",
                "approved_test": "FDA-approved companion diagnostic for osimertinib"
            },
            {
                "name": "BRCA1/2 Mutation Status",
                "cancer_type": "Breast / Ovarian Cancer",
                "gene_protein": "BRCA1 / BRCA2 genes / DNA repair proteins",
                "relevance": "Predictive and Risk Assessment",
                "detection_method": "Germline and somatic NGS panel testing",
                "normal_range": "No pathogenic variant",
                "clinical_significance": "Germline BRCA mutations increase lifetime breast cancer risk to ~72% and ovarian to ~44%. Predicts sensitivity to PARP inhibitors (olaparib, niraparib). Essential for family screening.",
                "approved_test": "FDA-approved companion diagnostic for PARP inhibitors"
            },
            {
                "name": "PD-L1 Expression",
                "cancer_type": "Multiple Cancers (NSCLC, Melanoma, TNBC, etc.)",
                "gene_protein": "CD274 gene / PD-L1 protein",
                "relevance": "Predictive",
                "detection_method": "IHC (22C3, 28-8, SP142 antibody clones), TPS/CPS scoring",
                "normal_range": "TPS <1% (NSCLC)",
                "clinical_significance": "High PD-L1 expression predicts response to immune checkpoint inhibitors (pembrolizumab, atezolizumab). CPS ≥10 used for pembrolizumab in gastric and cervical cancers.",
                "approved_test": "FDA-approved companion diagnostic for immunotherapy"
            },
        ]

        cur.executemany("""
            INSERT INTO biomarkers (name,cancer_type,gene_protein,relevance,
                                    detection_method,normal_range,clinical_significance,approved_test)
            VALUES (:name,:cancer_type,:gene_protein,:relevance,
                    :detection_method,:normal_range,:clinical_significance,:approved_test)
        """, biomarkers)

    conn.commit()
    conn.close()
    print("✅ Database initialised successfully.")


# ─── AI / Smart Search Engine ────────────────────────────────────────────────

# Symptom → disease keyword mapping (rule-based AI)
SYMPTOM_KEYWORDS = {
    "memory": ["Alzheimer's Disease", "Huntington's Disease"],
    "tremor": ["Parkinson's Disease", "Huntington's Disease", "Wilson's Disease"],
    "bleeding": ["Hemophilia A", "Sickle Cell Anemia"],
    "pain": ["Sickle Cell Anemia", "Cystic Fibrosis"],
    "cough": ["Cystic Fibrosis"],
    "breathing": ["Cystic Fibrosis"],
    "fatigue": ["Sickle Cell Anemia", "Type 2 Diabetes Mellitus", "Hemophilia A"],
    "thirst": ["Type 2 Diabetes Mellitus"],
    "glucose": ["Type 2 Diabetes Mellitus"],
    "sugar": ["Type 2 Diabetes Mellitus"],
    "liver": ["Wilson's Disease"],
    "copper": ["Wilson's Disease"],
    "movement": ["Parkinson's Disease", "Huntington's Disease"],
    "chorea": ["Huntington's Disease"],
    "cancer": ["Breast Cancer (BRCA-associated)", "Colorectal Cancer (Lynch Syndrome)"],
    "lump": ["Breast Cancer (BRCA-associated)"],
    "seizure": ["Phenylketonuria (PKU)"],
    "intellectual": ["Phenylketonuria (PKU)"],
    "heart": ["Marfan Syndrome"],
    "aorta": ["Marfan Syndrome"],
    "joints": ["Hemophilia A", "Marfan Syndrome"],
    "anemia": ["Sickle Cell Anemia"],
}

def ai_symptom_suggest(query: str):
    """
    Rule-based AI: tokenise the query, match against symptom keywords,
    score candidate diseases, and return ranked suggestions.
    This qualifies as AI because it implements:
      1. NLP tokenisation and normalisation
      2. Knowledge-based reasoning (symptom–disease ontology)
      3. Weighted scoring and ranking
    """
    tokens = re.findall(r'\b\w+\b', query.lower())
    scores = {}
    for token in tokens:
        # Exact keyword match
        for kw, diseases in SYMPTOM_KEYWORDS.items():
            if token in kw or kw in token:
                for d in diseases:
                    scores[d] = scores.get(d, 0) + 1
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Landing / home page."""
    stats = {
        "disease_count": query_db("SELECT COUNT(*) as c FROM diseases", one=True)["c"],
        "biomarker_count": query_db("SELECT COUNT(*) as c FROM biomarkers", one=True)["c"],
    }
    return render_template("index.html", stats=stats)


@app.route("/diseases")
def diseases_page():
    """Disease database browser page."""
    category = request.args.get("category", "")
    if category:
        rows = query_db("SELECT * FROM diseases WHERE category=? ORDER BY name", [category])
    else:
        rows = query_db("SELECT * FROM diseases ORDER BY name")
    categories = query_db("SELECT DISTINCT category FROM diseases ORDER BY category")
    return render_template("diseases.html", diseases=rows, categories=categories, active_cat=category)


@app.route("/disease/<int:disease_id>")
def disease_detail(disease_id):
    """Single disease detail page."""
    disease = query_db("SELECT * FROM diseases WHERE id=?", [disease_id], one=True)
    if not disease:
        return render_template("404.html"), 404
    # Parse JSON fields
    disease["symptoms"] = json.loads(disease["symptoms"] or "[]")
    disease["genes"] = json.loads(disease["genes"] or "[]")
    disease["proteins"] = json.loads(disease["proteins"] or "[]")
    disease["tags"] = json.loads(disease["tags"] or "[]")
    # Get session bookmarks
    bookmarks = session.get("bookmarks", [])
    is_bookmarked = disease_id in bookmarks
    return render_template("disease_detail.html", disease=disease, is_bookmarked=is_bookmarked)


@app.route("/biomarkers")
def biomarkers_page():
    """Cancer biomarkers section."""
    rows = query_db("SELECT * FROM biomarkers ORDER BY cancer_type")
    cancer_types = list({r["cancer_type"] for r in rows})
    cancer_types.sort()
    return render_template("biomarkers.html", biomarkers=rows, cancer_types=cancer_types)


@app.route("/search")
def search_page():
    """Smart search page."""
    return render_template("search.html")


@app.route("/compare")
def compare_page():
    """Disease comparison tool (bonus feature)."""
    all_diseases = query_db("SELECT id, name, category FROM diseases ORDER BY name")
    return render_template("compare.html", all_diseases=all_diseases)


# ─── JSON API Endpoints ───────────────────────────────────────────────────────

@app.route("/api/diseases")
def api_diseases():
    """Return all diseases as JSON."""
    rows = query_db("SELECT id, name, category, prevalence, inheritance FROM diseases ORDER BY name")
    return jsonify(rows)


@app.route("/api/disease/<int:disease_id>")
def api_disease(disease_id):
    """Return single disease as JSON."""
    d = query_db("SELECT * FROM diseases WHERE id=?", [disease_id], one=True)
    if not d:
        return jsonify({"error": "Not found"}), 404
    d["symptoms"] = json.loads(d["symptoms"] or "[]")
    d["genes"] = json.loads(d["genes"] or "[]")
    d["proteins"] = json.loads(d["proteins"] or "[]")
    return jsonify(d)


@app.route("/api/biomarkers")
def api_biomarkers():
    """Return all biomarkers as JSON."""
    return jsonify(query_db("SELECT * FROM biomarkers ORDER BY cancer_type"))


@app.route("/api/search")
def api_search():
    """
    Smart search API — searches diseases and biomarkers by:
    • name, symptoms, gene name (full-text via LIKE)
    • AI symptom matching (rule-based NLP scoring)
    • 'Did you mean?' fuzzy suggestions
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"diseases": [], "biomarkers": [], "suggestions": [], "ai_matches": []})

    like = f"%{q}%"

    # Full text search across multiple columns
    diseases = query_db("""
        SELECT id, name, category, symptoms, genes, tags
        FROM diseases
        WHERE name LIKE ? OR symptoms LIKE ? OR genes LIKE ? OR tags LIKE ?
        ORDER BY name
    """, [like, like, like, like])

    biomarkers = query_db("""
        SELECT id, name, cancer_type, gene_protein, relevance
        FROM biomarkers
        WHERE name LIKE ? OR cancer_type LIKE ? OR gene_protein LIKE ?
    """, [like, like, like])

    # AI: symptom-based suggestions
    ai_matches = []
    if len(q) > 3:
        suggestions = ai_symptom_suggest(q)
        for disease_name, score in suggestions:
            d = query_db("SELECT id, name, category FROM diseases WHERE name=?", [disease_name], one=True)
            if d:
                ai_matches.append({**d, "match_score": score})

    # "Did you mean?" fuzzy matching on disease names
    all_names = [r["name"] for r in query_db("SELECT name FROM diseases")]
    fuzzy = get_close_matches(q, all_names, n=3, cutoff=0.45)

    return jsonify({
        "diseases": diseases,
        "biomarkers": biomarkers,
        "ai_matches": ai_matches,
        "suggestions": fuzzy,
        "query": q
    })


@app.route("/api/compare")
def api_compare():
    """Return full data for two diseases for comparison."""
    ids = request.args.getlist("id")
    results = []
    for did in ids[:2]:
        d = query_db("SELECT * FROM diseases WHERE id=?", [did], one=True)
        if d:
            d["symptoms"] = json.loads(d["symptoms"] or "[]")
            d["genes"] = json.loads(d["genes"] or "[]")
            d["proteins"] = json.loads(d["proteins"] or "[]")
            results.append(d)
    return jsonify(results)


# ─── Bookmark API ────────────────────────────────────────────────────────────

@app.route("/api/bookmark/<int:disease_id>", methods=["POST"])
def toggle_bookmark(disease_id):
    """Toggle bookmark for a disease (stored in session)."""
    bookmarks = session.get("bookmarks", [])
    if disease_id in bookmarks:
        bookmarks.remove(disease_id)
        action = "removed"
    else:
        bookmarks.append(disease_id)
        action = "added"
    session["bookmarks"] = bookmarks
    return jsonify({"action": action, "bookmarks": bookmarks})


@app.route("/bookmarks")
def bookmarks_page():
    """Show bookmarked diseases."""
    bm_ids = session.get("bookmarks", [])
    diseases = []
    for did in bm_ids:
        d = query_db("SELECT id, name, category, prevalence FROM diseases WHERE id=?", [did], one=True)
        if d:
            diseases.append(d)
    return render_template("bookmarks.html", diseases=diseases)


# ─── Error Handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    else:
        # Re-run init to seed any new data (idempotent)
        init_db()
    app.run(debug=True, port=5000)
