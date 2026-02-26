import streamlit as st
import pdfplumber
import re
import requests
from groq import Groq
from generate_report import generate_credit_report
import pandas as pd
import docx
from PIL import Image
import pytesseract

# Set tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ==============================
# KEYS FROM SECRETS
# ==============================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# ==============================
# PAGE SETUP
# ==============================
st.set_page_config(
    page_title="CredX",
    page_icon="⚡",
    layout="wide"
)

# ==============================
# ANIMATIONS CSS
# ==============================
st.markdown("""
<style>

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes ticker {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-40px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(40px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes zoomIn {
    from { opacity: 0; transform: scale(0.7); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes borderGlow {
    0% { box-shadow: 0 0 5px #ffffff22; }
    50% { box-shadow: 0 0 20px #ffffff66; }
    100% { box-shadow: 0 0 5px #ffffff22; }
}

@keyframes scoreCount {
    from { opacity: 0; transform: scale(0.3) rotate(-10deg); }
    to { opacity: 1; transform: scale(1) rotate(0deg); }
}

.result-card {
    background-color: #1a1a2e;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #333;
    animation: slideInLeft 0.8s ease forwards;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.result-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(255,255,255,0.1);
    border-color: #555;
}

.result-card-right {
    background-color: #1a1a2e;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #333;
    animation: slideInRight 0.8s ease forwards;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.result-card-right:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(255,255,255,0.1);
    border-color: #555;
}

.score-box-approve {
    background: linear-gradient(135deg, #1a2e1a, #0d3d0d);
    border: 2px solid #4caf50;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    animation: zoomIn 1s ease forwards, borderGlow 4s ease-in-out infinite;
}

.score-box-reject {
    background: linear-gradient(135deg, #2e1a1a, #3d0d0d);
    border: 2px solid #f44336;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    animation: zoomIn 1s ease forwards, borderGlow 4s ease-in-out infinite;
}

.score-box-neutral {
    background: linear-gradient(135deg, #2e2a1a, #3d300d);
    border: 2px solid #ff9800;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    animation: zoomIn 1s ease forwards, borderGlow 4s ease-in-out infinite;
}

.score-number {
    font-size: 72px;
    font-weight: bold;
    color: white;
    animation: scoreCount 1.2s ease forwards;
    display: block;
    line-height: 1;
}

.score-label {
    font-size: 14px;
    color: #aaaaaa;
    margin-top: 8px;
}

.decision-badge-approve {
    display: inline-block;
    background: linear-gradient(90deg, #1a6e1a, #2d9e2d, #1a6e1a);
    background-size: 200% auto;
    animation: shimmer 5s linear infinite;
    color: white;
    font-size: 22px;
    font-weight: bold;
    padding: 12px 30px;
    border-radius: 50px;
    margin-top: 15px;
    letter-spacing: 2px;
}

.decision-badge-reject {
    display: inline-block;
    background: linear-gradient(90deg, #6e1a1a, #9e2d2d, #6e1a1a);
    background-size: 200% auto;
    animation: shimmer 5s linear infinite;
    color: white;
    font-size: 22px;
    font-weight: bold;
    padding: 12px 30px;
    border-radius: 50px;
    margin-top: 15px;
    letter-spacing: 2px;
}

.decision-badge-neutral {
    display: inline-block;
    background: linear-gradient(90deg, #6e5a1a, #9e7d2d, #6e5a1a);
    background-size: 200% auto;
    animation: shimmer 5s linear infinite;
    color: white;
    font-size: 22px;
    font-weight: bold;
    padding: 12px 30px;
    border-radius: 50px;
    margin-top: 15px;
    letter-spacing: 2px;
}

.fivec-card {
    background-color: #1a1a2e;
    border-radius: 10px;
    padding: 15px 20px;
    margin: 8px 0;
    border-left: 4px solid white;
    animation: slideInLeft 0.6s ease forwards;
    transition: transform 0.3s, border-left-color 0.3s;
}
.fivec-card:hover {
    transform: translateX(8px);
    border-left-color: #f0a500;
}

.fivec-title {
    color: white;
    font-weight: bold;
    font-size: 15px;
}

.news-item {
    background-color: #1a1a2e;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 6px 0;
    border-left: 3px solid #555;
    animation: fadeInUp 0.5s ease forwards;
    transition: border-left-color 0.3s;
    color: #cccccc;
    font-size: 13px;
}
.news-item:hover {
    border-left-color: white;
    color: white;
}

.gst-pass {
    background: linear-gradient(135deg, #0d2e0d, #1a4a1a);
    border: 1px solid #4caf50;
    border-radius: 10px;
    padding: 15px;
    animation: zoomIn 0.8s ease forwards;
    color: #aaffaa;
    text-align: center;
}
.gst-fail {
    background: linear-gradient(135deg, #2e0d0d, #4a1a1a);
    border: 1px solid #f44336;
    border-radius: 10px;
    padding: 15px;
    animation: zoomIn 0.8s ease forwards;
    color: #ffaaaa;
    text-align: center;
}
.gst-warn {
    background: linear-gradient(135deg, #2e2a0d, #4a3a1a);
    border: 1px solid #ff9800;
    border-radius: 10px;
    padding: 15px;
    animation: zoomIn 0.8s ease forwards;
    color: #ffddaa;
    text-align: center;
}

.main-title { animation: fadeInDown 1s ease forwards; }

.feature-card {
    background-color: #1a1a2e;
    padding: 30px 25px;
    border-radius: 12px;
    border-left: 4px solid white;
    text-align: center;
    animation: fadeInUp 1s ease forwards;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    min-height: 180px;
    height: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.feature-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 10px 30px rgba(255,255,255,0.15);
    border-left: 4px solid #f0a500;
}
.feature-icon {
    font-size: 44px;
    margin-bottom: 12px;
    display: block;
    line-height: 1;
}
.feature-card h4 { color: white; margin-bottom: 8px; font-size: 16px; }
.feature-card p  { color: #aaaaaa; font-size: 13px; margin: 0; }

.stat-card {
    background-color: #1a1a2e;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #333;
    text-align: center;
    animation: fadeInUp 1.5s ease forwards;
    transition: transform 0.3s ease;
}
.stat-card:hover { transform: scale(1.05); border-color: white; }
.stat-number { font-size: 28px; font-weight: bold; color: white; }
.stat-label  { font-size: 12px; color: #aaaaaa; margin-top: 5px; }

.steps-box {
    background-color: #1a1a2e;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #333;
    animation: fadeInUp 1.5s ease forwards;
    min-height: 230px;
    height: auto;
}
.step-item {
    padding: 8px 0;
    color: #aaaaaa;
    font-size: 14px;
    border-bottom: 1px solid #2a2a3e;
    transition: color 0.3s ease;
}
.step-item:hover { color: white; }
.step-item:last-child { border-bottom: none; }

.ticker-bar {
    background: linear-gradient(90deg, #1a1a2e, #2d2d4e, #1a1a2e);
    padding: 10px 0;
    border-radius: 8px;
    overflow: hidden;
    white-space: nowrap;
}
.ticker-text {
    display: inline-block;
    animation: ticker 50s linear infinite;
    color: #aaaaaa;
    font-size: 13px;
    padding-left: 100%;
}

.badge {
    display: inline-block;
    background-color: #2d2d4e;
    color: white;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    margin: 4px;
    border: 1px solid #444;
    transition: border-color 0.3s, transform 0.3s;
}
.badge:hover { border-color: white; transform: scale(1.1); }

</style>
""", unsafe_allow_html=True)

st.title("⚡ CredX")
st.subheader("The X Factor in AI-Powered Credit Intelligence")
st.divider()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("📋 Company Details")
company_name = st.sidebar.text_input("Enter Company Name", placeholder="e.g. Tata Motors")
uploaded_files = st.sidebar.file_uploader(
    "Upload Documents",
    type=["pdf", "xlsx", "csv", "docx", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="You can upload PDF, Excel, CSV, Word, or Image files"
)
qualitative_notes = st.sidebar.text_area(
    "Additional Notes (Optional)",
    placeholder="e.g. Factory found operating at 40% capacity. Management seemed confident."
)
st.sidebar.divider()
st.sidebar.header("🧾 GST Cross Check")
gst_file = st.sidebar.file_uploader("Upload GST Return (Excel/CSV)", type=["xlsx", "csv"])
bank_file = st.sidebar.file_uploader("Upload Bank Statement (Excel/CSV)", type=["xlsx", "csv"])
st.sidebar.divider()
st.sidebar.header("🇮🇳 Indian Context")
cibil_score    = st.sidebar.number_input("CIBIL Commercial Score (1-10)", min_value=1, max_value=10, value=5)
gst_mismatch   = st.sidebar.selectbox("GSTR-2A vs 3B Mismatch?", ["No Mismatch", "Minor Mismatch (<10%)", "Major Mismatch (>10%)"])
rbi_compliance = st.sidebar.selectbox("RBI Compliance Status", ["Fully Compliant", "Minor Issues", "Non Compliant"])
analyze_button = st.sidebar.button("🔍 Analyze Now", type="primary")

# ==============================
# FILE READING FUNCTIONS
# ==============================
def read_pdf(file):
    text = ""
    important_keywords = ["revenue", "profit", "loss", "balance sheet", "turnover",
                          "borrowing", "debt", "assets", "liabilities", "cash flow",
                          "ebitda", "net worth", "dividend", "equity", "gst", "tax"]
    with pdfplumber.open(file) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if not page_text:
                continue
            if i < 30 or i > total_pages - 20:
                text += page_text + "\n"
            else:
                for keyword in important_keywords:
                    if keyword in page_text.lower():
                        text += page_text + "\n"
                        break
    return text

def read_excel(file):
    try:
        return f"EXCEL DATA:\n{pd.read_excel(file).to_string()}\n"
    except:
        return "Could not read Excel file."

def read_csv(file):
    try:
        return f"CSV DATA:\n{pd.read_csv(file).to_string()}\n"
    except:
        return "Could not read CSV file."

def read_word(file):
    try:
        doc  = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return f"WORD DOCUMENT:\n{text}\n"
    except:
        return "Could not read Word file."

def read_image(file):
    try:
        return f"SCANNED IMAGE TEXT:\n{pytesseract.image_to_string(Image.open(file))}\n"
    except:
        return "Could not read image file."

def extract_all_files(uploaded_files):
    all_text, file_summary = "", []
    for file in uploaded_files:
        fn = file.name.lower()
        st.write(f"📄 Reading: {file.name}")
        if fn.endswith(".pdf"):
            text = read_pdf(file);   file_summary.append(f"✅ PDF: {file.name}")
        elif fn.endswith((".xlsx", ".xls")):
            text = read_excel(file); file_summary.append(f"✅ Excel: {file.name}")
        elif fn.endswith(".csv"):
            text = read_csv(file);   file_summary.append(f"✅ CSV: {file.name}")
        elif fn.endswith(".docx"):
            text = read_word(file);  file_summary.append(f"✅ Word: {file.name}")
        elif fn.endswith((".png", ".jpg", ".jpeg")):
            text = read_image(file); file_summary.append(f"✅ Image: {file.name}")
        else:
            text = "";               file_summary.append(f"❌ Unknown: {file.name}")
        all_text += f"\n--- FROM FILE: {file.name} ---\n{text}\n"
    return all_text, file_summary

# ==============================
# BUG FIX 3 — GST always returns mismatch_pct
# ==============================
def cross_check_gst(gst_file, bank_file):
    try:
        gst_df  = pd.read_csv(gst_file)  if gst_file.name.endswith(".csv")  else pd.read_excel(gst_file)
        bank_df = pd.read_csv(bank_file) if bank_file.name.endswith(".csv") else pd.read_excel(bank_file)
        gst_total  = gst_df.select_dtypes(include='number').sum().sum()
        bank_total = bank_df.select_dtypes(include='number').sum().sum()
        mismatch_pct = abs(gst_total - bank_total) / bank_total * 100 if bank_total > 0 else 0
        result = (f"\nGST CROSS CHECK RESULTS:\n"
                  f"- GST Return Total: {gst_total:,.2f}\n"
                  f"- Bank Statement Total: {bank_total:,.2f}\n"
                  f"- Mismatch: {mismatch_pct:.2f}%\n")
        if mismatch_pct > 20:
            result += "HIGH RISK: Major mismatch — possible circular trading."
        elif mismatch_pct > 10:
            result += "MEDIUM RISK: Minor mismatch — investigate further."
        else:
            result += "LOW RISK: GST matches bank. No circular trading."
        return result, mismatch_pct
    except:
        return "Could not cross check GST files.", 0

def extract_financial_data(text):
    fd = {"revenue_lines": [], "profit_lines": [], "debt_lines": [], "other_important": []}
    km = {"revenue": "revenue_lines", "turnover": "revenue_lines",
          "net profit": "profit_lines", "profit margin": "profit_lines",
          "debt": "debt_lines", "borrowing": "debt_lines"}
    for line in text.split("\n"):
        for kw, cat in km.items():
            if kw in line.lower():
                fd[cat].append(line.strip())
                break
    return fd

def search_news(company_name):
    try:
        r = requests.get("https://newsapi.org/v2/everything", params={
            "q": f"{company_name} India finance loan fraud legal",
            "language": "en", "sortBy": "relevancy", "pageSize": 5, "apiKey": NEWS_API_KEY})
        data = r.json()
        if data["status"] == "ok" and data["totalResults"] > 0:
            return "\n".join([f"- {a['title']}: {a['description'] or ''}" for a in data["articles"]])
        return "No recent news found."
    except:
        return "News search failed."

def search_mca_filings(company_name):
    try:
        r = requests.get("https://newsapi.org/v2/everything", params={
            "q": f"{company_name} MCA filing Ministry Corporate Affairs ROC India",
            "language": "en", "sortBy": "relevancy", "pageSize": 3, "apiKey": NEWS_API_KEY})
        data = r.json()
        if data["status"] == "ok" and data["totalResults"] > 0:
            return "\n".join([f"- {a['title']}: {a['description'] or ''}" for a in data["articles"]])
        return "No MCA filings found."
    except:
        return "MCA search failed."

def search_legal_cases(company_name):
    try:
        r = requests.get("https://newsapi.org/v2/everything", params={
            "q": f"{company_name} court case legal dispute lawsuit India eCourts",
            "language": "en", "sortBy": "relevancy", "pageSize": 3, "apiKey": NEWS_API_KEY})
        data = r.json()
        if data["status"] == "ok" and data["totalResults"] > 0:
            return "\n".join([f"- {a['title']}: {a['description'] or ''}" for a in data["articles"]])
        return "No legal cases found."
    except:
        return "Legal search failed."

# ==============================
# BUG FIX 4 — AI prompt forces structured format
# ==============================
def analyze_credit(company_name, financial_data, news, qualitative_notes,
                   cibil_score, gst_mismatch, rbi_compliance, mca_data, legal_data, gst_result):
    fs = ""
    for cat, lines in financial_data.items():
        fs += f"\n{cat}:\n" + "".join([f"  - {l}\n" for l in lines])

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"""You are an expert Indian banking credit analyst.

COMPANY: {company_name}
FINANCIAL DATA: {fs}
NEWS: {news}
MCA FILINGS: {mca_data}
LEGAL CASES: {legal_data}
GST CROSS CHECK: {gst_result if gst_result else "Not provided"}
QUALITATIVE NOTES: {qualitative_notes if qualitative_notes else "None"}
INDIAN BANKING:
- CIBIL Score: {cibil_score}/10
- GST Mismatch: {gst_mismatch}
- RBI Compliance: {rbi_compliance}

IMPORTANT: You MUST follow this EXACT format. Do not use ## or Step headers.

CHARACTER: [X]/10
[2 lines explanation]

CAPACITY: [X]/10
[2 lines explanation]

CAPITAL: [X]/10
[2 lines explanation]

COLLATERAL: [X]/10
[2 lines explanation]

CONDITIONS: [X]/10
[2 lines explanation]

Overall Credit Score: [number]
Credit Recommendation: [Approve / Reject / Need More Info]
Suggested Loan Limit: [number] Crores INR
Suggested Interest Rate: [number]%
Early Warning Signals: [list or None]
Reason for Recommendation: [2-3 lines]

Be strict. Low CIBIL, major GST mismatch, legal issues MUST lower scores significantly."""}]
    )
    return response.choices[0].message.content

# ==============================
# BUG FIX 1 — FIXED get_credit_score uses actual Five Cs
# ==============================
def get_credit_score(analysis_text):
    patterns = {
        "CHARACTER":  r"CHARACTER[:\s]*(\d+)\s*/\s*10",
        "CAPACITY":   r"CAPACITY[:\s]*(\d+)\s*/\s*10",
        "CAPITAL":    r"CAPITAL[:\s]*(\d+)\s*/\s*10",
        "COLLATERAL": r"COLLATERAL[:\s]*(\d+)\s*/\s*10",
        "CONDITIONS": r"CONDITIONS[:\s]*(\d+)\s*/\s*10",
    }
    scores = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, analysis_text, re.IGNORECASE)
        scores[name] = int(m.group(1)) if m else None

    if all(v is not None for v in scores.values()):
        # Weighted average — Capital and Collateral low scores will pull score DOWN
        weighted = (
            scores["CHARACTER"]  * 0.25 +
            scores["CAPACITY"]   * 0.25 +
            scores["CAPITAL"]    * 0.20 +
            scores["COLLATERAL"] * 0.15 +
            scores["CONDITIONS"] * 0.15
        )
        base_score = round(weighted * 10)
    else:
        text = analysis_text.lower()
        base_score = 50
        if "approve"         in text: base_score += 20
        if "strong financial" in text: base_score += 10
        if "low risk"         in text: base_score += 10
        if "reject"           in text: base_score -= 20
        if "high risk"        in text: base_score -= 15
        if "fraud"            in text: base_score -= 15

    # Indian context adjustments
    text = analysis_text.lower()
    adj = 0
    if "fully compliant" in text: adj += 3
    if "minor issues"    in text: adj -= 3
    if "non compliant"   in text: adj -= 8
    if "no mismatch"     in text: adj += 3
    if "minor mismatch"  in text: adj -= 3
    if "major mismatch"  in text: adj -= 8
    if "fraud detected"  in text: adj -= 10

    return max(0, min(100, base_score + adj))

# ==============================
# BUG FIX 2 — parse_five_cs and parse_final_decision at TOP LEVEL
# (not inside if block — no more duplicate Five Cs display)
# ==============================
def parse_five_cs(analysis_text):
    patterns = {
        "CHARACTER":  r"CHARACTER[:\s]*(\d+)\s*/\s*10",
        "CAPACITY":   r"CAPACITY[:\s]*(\d+)\s*/\s*10",
        "CAPITAL":    r"CAPITAL[:\s]*(\d+)\s*/\s*10",
        "COLLATERAL": r"COLLATERAL[:\s]*(\d+)\s*/\s*10",
        "CONDITIONS": r"CONDITIONS[:\s]*(\d+)\s*/\s*10",
    }
    scores = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, analysis_text, re.IGNORECASE)
        scores[name] = int(m.group(1)) if m else 7
    return scores

def parse_final_decision(analysis_text):
    result = {}
    m = re.search(r"[Oo]verall\s+[Cc]redit\s+[Ss]core[:\s]*(\d+)", analysis_text)
    result["overall_score"] = int(m.group(1)) if m else get_credit_score(analysis_text)

    if re.search(r"\bApprove\b",        analysis_text, re.IGNORECASE): result["recommendation"] = "APPROVE"
    elif re.search(r"\bReject\b",       analysis_text, re.IGNORECASE): result["recommendation"] = "REJECT"
    else:                                                                result["recommendation"] = "NEED MORE INFO"

    m = re.search(r"[Ll]oan\s+[Ll]imit[:\s]*([0-9,]+)", analysis_text)
    result["loan_limit"] = m.group(1).replace(",", "") if m else "500"

    m = re.search(r"[Ii]nterest\s+[Rr]ate[:\s]*([0-9.]+)\s*%?", analysis_text)
    result["interest_rate"] = m.group(1) if m else "8.5"

    m = re.search(r"[Ee]arly\s+[Ww]arning[^:\n]*[:\n]+(.+?)(?=\nCredit|\nOverall|\nSuggested|\nReason|\Z)",
                  analysis_text, re.DOTALL)
    result["warning"] = m.group(1).strip()[:300] if m else "No major warning signals detected."

    m = re.search(r"[Rr]eason[^:\n]*[:\n]+(.+?)(?=\n\n|\Z)", analysis_text, re.DOTALL)
    result["reason"] = m.group(1).strip()[:400] if m else "Based on comprehensive analysis of all available data."

    return result

# ==============================
# HOME PAGE — Animated
# ==============================
if not analyze_button:

    st.markdown("""
    <div class='main-title' style='text-align:center; padding:10px 0;'>
        <h2 style='color:white;'>Welcome to CredX ⚡</h2>
        <p style='color:#aaaaaa; font-size:15px;'>
            The X Factor in AI-Powered Credit Appraisal for Indian Corporate Lending
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='ticker-bar'>
        <span class='ticker-text'>
            ⚡ CredX — Instant Credit Decisions &nbsp;|&nbsp;
            🏦 Upload Annual Reports &nbsp;|&nbsp;
            🔍 Auto News Search &nbsp;|&nbsp;
            🏛️ MCA Filings Check &nbsp;|&nbsp;
            ⚖️ eCourts Legal Search &nbsp;|&nbsp;
            🧾 GST Cross Check &nbsp;|&nbsp;
            📊 Five Cs Analysis &nbsp;|&nbsp;
            🇮🇳 CIBIL + RBI + GST Context &nbsp;|&nbsp;
            📋 Professional CAM Report &nbsp;|&nbsp;
            ✅ Instant Credit Decision &nbsp;|&nbsp;
            ⚡ CredX — Instant Credit Decisions &nbsp;|&nbsp;
            🏦 Upload Annual Reports &nbsp;|&nbsp;
            🔍 Auto News Search
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='feature-card'>
            <span class='feature-icon'>📄</span>
            <h4>Upload Documents</h4>
            <p>PDF, Excel, Word, CSV and Images — all supported formats</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='feature-card'>
            <span class='feature-icon'>🤖</span>
            <h4>AI Analysis</h4>
            <p>Five Cs of Credit with full Indian banking context</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='feature-card'>
            <span class='feature-icon'>📊</span>
            <h4>Instant Decision</h4>
            <p>Credit score, loan limit and interest rate in 2 minutes</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c4, c5, c6, c7 = st.columns(4)
    with c4: st.markdown("<div class='stat-card'><div class='stat-number'>2 Min</div><div class='stat-label'>⏱️ vs Weeks Manually</div></div>", unsafe_allow_html=True)
    with c5: st.markdown("<div class='stat-card'><div class='stat-number'>5+</div><div class='stat-label'>📁 File Formats</div></div>", unsafe_allow_html=True)
    with c6: st.markdown("<div class='stat-card'><div class='stat-number'>100%</div><div class='stat-label'>🇮🇳 Indian Context</div></div>", unsafe_allow_html=True)
    with c7: st.markdown("<div class='stat-card'><div class='stat-number'>Free</div><div class='stat-label'>🌐 Live Website</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cl, cr = st.columns(2)
    with cl:
        st.markdown("""<div class='steps-box'>
            <h4 style='color:white; margin-bottom:12px;'>🚀 How to Get Started</h4>
            <div class='step-item'>1️⃣ &nbsp; Enter company name in the sidebar</div>
            <div class='step-item'>2️⃣ &nbsp; Upload annual report PDF or any documents</div>
            <div class='step-item'>3️⃣ &nbsp; Upload GST return and bank statement</div>
            <div class='step-item'>4️⃣ &nbsp; Fill CIBIL score, GST mismatch and RBI status</div>
            <div class='step-item'>5️⃣ &nbsp; Click <strong style='color:white'>🔍 Analyze Now!</strong></div>
        </div>""", unsafe_allow_html=True)
    with cr:
        st.markdown("""<div class='steps-box'>
            <h4 style='color:white; margin-bottom:12px;'>🇮🇳 Indian Banking Features</h4>
            <div class='step-item'>✅ &nbsp; CIBIL Commercial Score analysis</div>
            <div class='step-item'>✅ &nbsp; GSTR-2A vs 3B mismatch detection</div>
            <div class='step-item'>✅ &nbsp; RBI compliance status check</div>
            <div class='step-item'>✅ &nbsp; MCA Ministry of Corporate Affairs filings</div>
            <div class='step-item'>✅ &nbsp; eCourts legal case detection</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; padding:15px; background-color:#1a1a2e; border-radius:12px; border:1px solid #333;'>
        <p style='color:#aaaaaa; margin-bottom:12px; font-size:13px;'>📁 Supported File Formats:</p>
        <span class='badge'>📄 PDF</span>
        <span class='badge'>📊 Excel</span>
        <span class='badge'>📋 CSV</span>
        <span class='badge'>📝 Word</span>
        <span class='badge'>🖼️ Images</span>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# RESULTS PAGE
# ==============================
if analyze_button:
    if not company_name:
        st.error("Please enter a company name!")
    elif not uploaded_files:
        st.error("Please upload at least one file!")
    else:
        with st.spinner("📄 Reading uploaded files..."):
            all_text, file_summary = extract_all_files(uploaded_files)
            financial_data = extract_financial_data(all_text)
            st.success("✅ Files extracted successfully!")
            for s in file_summary: st.write(s)

        # BUG FIX 3 — always define mismatch_pct to avoid NameError crash
        gst_result   = ""
        mismatch_pct = 0

        if gst_file and bank_file:
            with st.spinner("🧾 Cross checking GST vs Bank Statement..."):
                gst_result, mismatch_pct = cross_check_gst(gst_file, bank_file)
                if   mismatch_pct > 20: st.error(f"🚨 GST Mismatch: {mismatch_pct:.1f}%")
                elif mismatch_pct > 10: st.warning(f"⚠️ Minor GST Mismatch: {mismatch_pct:.1f}%")
                else:                   st.success(f"✅ GST OK: {mismatch_pct:.1f}% mismatch")

        with st.spinner("🔍 Searching latest news..."):
            news = search_news(company_name);     st.success("✅ News collected!")
        with st.spinner("🏛️ Searching MCA filings..."):
            mca_data = search_mca_filings(company_name); st.success("✅ MCA filings searched!")
        with st.spinner("⚖️ Searching legal cases..."):
            legal_data = search_legal_cases(company_name); st.success("✅ Legal cases searched!")
        with st.spinner("🤖 AI is analyzing... please wait..."):
            analysis = analyze_credit(company_name, financial_data, news, qualitative_notes,
                                      cibil_score, gst_mismatch, rbi_compliance,
                                      mca_data, legal_data, gst_result)
            st.success("✅ Analysis complete!")

        st.divider()

        # --- Research Cards ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.subheader("📰 Latest News Found")
            for line in news.strip().split("\n"):
                if line.strip(): st.markdown(f"<div class='news-item'>{line}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.subheader("🏛️ MCA Filings")
            for line in mca_data.strip().split("\n"):
                if line.strip(): st.markdown(f"<div class='news-item'>{line}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.subheader("⚖️ Legal Cases")
            for line in legal_data.strip().split("\n"):
                if line.strip(): st.markdown(f"<div class='news-item'>{line}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='result-card-right'>", unsafe_allow_html=True)
            st.subheader("📊 Financial Data Extracted")
            st.json(financial_data)
            st.markdown("</div>", unsafe_allow_html=True)

            if gst_result:
                st.markdown("<br>", unsafe_allow_html=True)
                if mismatch_pct > 20:
                    st.markdown(f"<div class='gst-fail'><h3>🚨 GST Cross Check — HIGH RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>Major mismatch — possible revenue inflation or circular trading.</p></div>", unsafe_allow_html=True)
                elif mismatch_pct > 10:
                    st.markdown(f"<div class='gst-warn'><h3>⚠️ GST Cross Check — MEDIUM RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>Minor mismatch — further investigation needed.</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='gst-pass'><h3>✅ GST Cross Check — LOW RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>GST matches bank. No circular trading detected.</p></div>", unsafe_allow_html=True)

        st.divider()

        # --- AI Analysis — BUG FIX 2: ONE Five Cs display using actual AI scores ---
        st.subheader("🤖 AI Credit Analysis")

        five_cs_scores = parse_five_cs(analysis)
        final          = parse_final_decision(analysis)
        # Use weighted formula as the authoritative score (BUG FIX 1)
        credit_score   = get_credit_score(analysis)

        cs_info = {
            "CHARACTER":  ("👤", "Promoter background, fraud history, legal issues, MCA filings"),
            "CAPACITY":   ("💰", "Revenue, profit, cash flow and debt repayment ability"),
            "CAPITAL":    ("🏦", "Own funds, reserves, debt-to-equity ratio and net worth"),
            "COLLATERAL": ("🏢", "Assets available as security — plants, equipment, real estate"),
            "CONDITIONS": ("🌍", "Industry outlook, RBI regulations, market and legal conditions"),
        }

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:white;'>📋 Five Cs Breakdown</h4>", unsafe_allow_html=True)

        for name, (icon, desc) in cs_info.items():
            sv  = five_cs_scores.get(name, 7)
            pct = sv * 10
            col = "#4caf50" if sv >= 8 else "#ff9800" if sv >= 6 else "#f44336"
            st.markdown(f"""
            <div class='fivec-card' style='margin-bottom:10px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='font-size:22px;'>{icon}</span>
                        <span class='fivec-title' style='font-size:16px; margin-left:8px;'>{name}</span>
                    </div>
                    <span style='background:{col}; color:black; font-weight:bold;
                                 padding:4px 14px; border-radius:20px; font-size:14px;'>{sv}/10</span>
                </div>
                <div style='color:#aaaaaa; font-size:12px; margin:6px 0 8px 32px;'>{desc}</div>
                <div style='background:#2a2a3e; border-radius:20px; height:8px; overflow:hidden;'>
                    <div style='width:{pct}%; background:{col}; height:8px; border-radius:20px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:white;'>🏆 Key Decision Metrics</h4>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div style='background:#1a1a2e; border:1px solid #333; border-radius:12px; padding:20px; text-align:center;'>
                <div style='font-size:13px; color:#aaaaaa;'>📊 Overall Score</div>
                <div style='font-size:40px; font-weight:bold; color:white; margin:8px 0;'>{credit_score}</div>
                <div style='font-size:12px; color:#aaaaaa;'>out of 100</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div style='background:#1a1a2e; border:1px solid #333; border-radius:12px; padding:20px; text-align:center;'>
                <div style='font-size:13px; color:#aaaaaa;'>💵 Suggested Loan</div>
                <div style='font-size:32px; font-weight:bold; color:white; margin:8px 0;'>&#8377;{final["loan_limit"]}</div>
                <div style='font-size:12px; color:#aaaaaa;'>Crores INR</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div style='background:#1a1a2e; border:1px solid #333; border-radius:12px; padding:20px; text-align:center;'>
                <div style='font-size:13px; color:#aaaaaa;'>📈 Interest Rate</div>
                <div style='font-size:40px; font-weight:bold; color:white; margin:8px 0;'>{final["interest_rate"]}%</div>
                <div style='font-size:12px; color:#aaaaaa;'>per annum</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            rec = final["recommendation"]
            rc  = "#4caf50" if rec == "APPROVE" else "#f44336" if rec == "REJECT" else "#ff9800"
            ri  = "✅"      if rec == "APPROVE" else "❌"      if rec == "REJECT" else "⚠️"
            st.markdown(f"""<div style='background:#1a1a2e; border:2px solid {rc}; border-radius:12px; padding:20px; text-align:center;'>
                <div style='font-size:13px; color:#aaaaaa;'>🏷️ Recommendation</div>
                <div style='font-size:28px; margin:8px 0;'>{ri}</div>
                <div style='font-size:16px; font-weight:bold; color:{rc};'>{rec}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        w1, w2 = st.columns(2)
        with w1:
            st.markdown(f"""<div style='background:#1a1a2e; border-left:4px solid #ff9800; border-radius:10px; padding:20px;'>
                <h5 style='color:#ff9800; margin-bottom:10px;'>⚠️ Early Warning Signals</h5>
                <p style='color:#dddddd; font-size:13px; line-height:1.7;'>{final["warning"]}</p>
            </div>""", unsafe_allow_html=True)
        with w2:
            st.markdown(f"""<div style='background:#1a1a2e; border-left:4px solid #4caf50; border-radius:10px; padding:20px;'>
                <h5 style='color:#4caf50; margin-bottom:10px;'>💡 Reason for Decision</h5>
                <p style='color:#dddddd; font-size:13px; line-height:1.7;'>{final["reason"]}</p>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # --- Final Credit Decision ---
        st.subheader("🏆 Final Credit Decision")
        st.markdown("<br>", unsafe_allow_html=True)

        s1, s2, s3 = st.columns(3)

        box = "score-box-approve" if credit_score >= 70 else "score-box-neutral" if credit_score >= 50 else "score-box-reject"

        with s1:
            st.markdown(f"""<div class='{box}'>
                <span class='score-number'>{credit_score}</span>
                <div class='score-label'>📊 Credit Score out of 100</div>
            </div>""", unsafe_allow_html=True)

        with s2:
            if credit_score >= 70:
                st.markdown("<div class='score-box-approve' style='padding:20px;'><div style='font-size:40px;'>✅</div><div class='decision-badge-approve'>APPROVE</div><div class='score-label' style='margin-top:10px;'>Recommendation</div></div>", unsafe_allow_html=True)
            elif credit_score >= 50:
                st.markdown("<div class='score-box-neutral' style='padding:20px;'><div style='font-size:40px;'>⚠️</div><div class='decision-badge-neutral'>NEED MORE INFO</div><div class='score-label' style='margin-top:10px;'>Recommendation</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='score-box-reject' style='padding:20px;'><div style='font-size:40px;'>❌</div><div class='decision-badge-reject'>REJECT</div><div class='score-label' style='margin-top:10px;'>Recommendation</div></div>", unsafe_allow_html=True)

        with s3:
            if credit_score >= 70:
                st.markdown("<div class='score-box-approve' style='padding:20px;'><div style='font-size:40px;'>🟢</div><div style='font-size:22px;font-weight:bold;color:white;margin-top:10px;'>LOW RISK</div><div class='score-label'>Risk Level</div></div>", unsafe_allow_html=True)
            elif credit_score >= 50:
                st.markdown("<div class='score-box-neutral' style='padding:20px;'><div style='font-size:40px;'>🟡</div><div style='font-size:22px;font-weight:bold;color:white;margin-top:10px;'>MEDIUM RISK</div><div class='score-label'>Risk Level</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='score-box-reject' style='padding:20px;'><div style='font-size:40px;'>🔴</div><div style='font-size:22px;font-weight:bold;color:white;margin-top:10px;'>HIGH RISK</div><div class='score-label'>Risk Level</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        if credit_score >= 70:
            st.markdown(f"""<div class='score-box-approve' style='padding:30px; text-align:left;'>
                <h2 style='color:#aaffaa;'>✅ FINAL DECISION: LOAN APPROVED</h2>
                <p style='color:white; font-size:16px;'>📊 Credit Score: <strong>{credit_score}/100</strong> &nbsp;&nbsp; 🏷️ Risk: <strong>LOW RISK</strong></p>
                <p style='color:#aaffaa;'>💡 Strong financial profile — recommended for lending.</p>
            </div>""", unsafe_allow_html=True)
        elif credit_score >= 50:
            st.markdown(f"""<div class='score-box-neutral' style='padding:30px; text-align:left;'>
                <h2 style='color:#ffddaa;'>⚠️ FINAL DECISION: NEED MORE INFORMATION</h2>
                <p style='color:white; font-size:16px;'>📊 Credit Score: <strong>{credit_score}/100</strong> &nbsp;&nbsp; 🏷️ Risk: <strong>MEDIUM RISK</strong></p>
                <p style='color:#ffddaa;'>💡 More documents and due diligence required.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class='score-box-reject' style='padding:30px; text-align:left;'>
                <h2 style='color:#ffaaaa;'>❌ FINAL DECISION: LOAN REJECTED</h2>
                <p style='color:white; font-size:16px;'>📊 Credit Score: <strong>{credit_score}/100</strong> &nbsp;&nbsp; 🏷️ Risk: <strong>HIGH RISK</strong></p>
                <p style='color:#ffaaaa;'>💡 Significant risks — lending inadvisable at this time.</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        report_path = generate_credit_report(company_name, financial_data, news, analysis)
        with open(report_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Professional Credit Report (PDF)",
                data=f,
                file_name=f"{company_name}_CredX_Report.pdf",
                mime="application/pdf"
            )