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

try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    pass

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except KeyError as e:
    st.error(f"❌ Missing secret: {e}. Please add it in Streamlit → Settings → Secrets.")
    st.stop()

if not GROQ_API_KEY or not GROQ_API_KEY.startswith("gsk_"):
    st.error("❌ GROQ_API_KEY looks invalid. It should start with 'gsk_'.")
    st.stop()

GROQ_MODEL = "llama-3.3-70b-versatile"

st.set_page_config(page_title="CredX", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@keyframes fadeInDown { from{opacity:0;transform:translateY(-30px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeInUp   { from{opacity:0;transform:translateY(30px)}  to{opacity:1;transform:translateY(0)} }
@keyframes slideInLeft  { from{opacity:0;transform:translateX(-40px)} to{opacity:1;transform:translateX(0)} }
@keyframes slideInRight { from{opacity:0;transform:translateX(40px)}  to{opacity:1;transform:translateX(0)} }
@keyframes zoomIn    { from{opacity:0;transform:scale(0.7)} to{opacity:1;transform:scale(1)} }
@keyframes shimmer   { 0%{background-position:-200% center} 100%{background-position:200% center} }
@keyframes borderGlow{ 0%{box-shadow:0 0 5px #ffffff22} 50%{box-shadow:0 0 20px #ffffff66} 100%{box-shadow:0 0 5px #ffffff22} }
@keyframes scoreCount{ from{opacity:0;transform:scale(0.3) rotate(-10deg)} to{opacity:1;transform:scale(1) rotate(0deg)} }
@keyframes ticker    { 0%{transform:translateX(100%)} 100%{transform:translateX(-100%)} }
@keyframes orbFloat  { 0%,100%{transform:translate(0,0)} 33%{transform:translate(30px,-20px)} 66%{transform:translate(-20px,15px)} }

/* ── BACKGROUND ONLY CHANGES ── */
.stApp {
    background: #03030a !important;
    background-attachment: fixed !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 900px 600px at 15% 20%, rgba(99,102,241,0.07) 0%, transparent 70%),
        radial-gradient(ellipse 700px 500px at 85% 75%, rgba(139,92,246,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 600px 400px at 50% 100%, rgba(16,185,129,0.04) 0%, transparent 70%),
        radial-gradient(ellipse 400px 300px at 90% 10%, rgba(56,189,248,0.04) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: orbFloat 20s ease-in-out infinite;
}
.main .block-container {
    background: transparent !important;
    position: relative;
    z-index: 1;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080818 0%, #0a0a22 50%, #050510 100%) !important;
}
header[data-testid="stHeader"] {
    background: rgba(3,3,10,0.95) !important;
}

/* ── ALL YOUR ORIGINAL STYLES BELOW — UNCHANGED ── */
.result-card{background:#1a1a2e;padding:20px;border-radius:12px;border:1px solid #333;animation:slideInLeft 0.8s ease forwards;transition:transform .3s,box-shadow .3s}
.result-card:hover{transform:translateY(-5px);box-shadow:0 8px 25px rgba(255,255,255,.1);border-color:#555}
.result-card-right{background:#1a1a2e;padding:20px;border-radius:12px;border:1px solid #333;animation:slideInRight 0.8s ease forwards;transition:transform .3s,box-shadow .3s}
.result-card-right:hover{transform:translateY(-5px);box-shadow:0 8px 25px rgba(255,255,255,.1);border-color:#555}
.score-box-approve{background:linear-gradient(135deg,#1a2e1a,#0d3d0d);border:2px solid #4caf50;border-radius:16px;padding:30px;text-align:center;animation:zoomIn 1s ease forwards,borderGlow 4s ease-in-out infinite}
.score-box-reject {background:linear-gradient(135deg,#2e1a1a,#3d0d0d);border:2px solid #f44336;border-radius:16px;padding:30px;text-align:center;animation:zoomIn 1s ease forwards,borderGlow 4s ease-in-out infinite}
.score-box-neutral{background:linear-gradient(135deg,#2e2a1a,#3d300d);border:2px solid #ff9800;border-radius:16px;padding:30px;text-align:center;animation:zoomIn 1s ease forwards,borderGlow 4s ease-in-out infinite}
.score-number{font-size:72px;font-weight:bold;color:white;animation:scoreCount 1.2s ease forwards;display:block;line-height:1}
.score-label{font-size:14px;color:#aaaaaa;margin-top:8px}
.decision-badge-approve{display:inline-block;background:linear-gradient(90deg,#1a6e1a,#2d9e2d,#1a6e1a);background-size:200% auto;animation:shimmer 5s linear infinite;color:white;font-size:22px;font-weight:bold;padding:12px 30px;border-radius:50px;margin-top:15px;letter-spacing:2px}
.decision-badge-reject {display:inline-block;background:linear-gradient(90deg,#6e1a1a,#9e2d2d,#6e1a1a);background-size:200% auto;animation:shimmer 5s linear infinite;color:white;font-size:22px;font-weight:bold;padding:12px 30px;border-radius:50px;margin-top:15px;letter-spacing:2px}
.decision-badge-neutral{display:inline-block;background:linear-gradient(90deg,#6e5a1a,#9e7d2d,#6e5a1a);background-size:200% auto;animation:shimmer 5s linear infinite;color:white;font-size:22px;font-weight:bold;padding:12px 30px;border-radius:50px;margin-top:15px;letter-spacing:2px}
.fivec-card{background:#1a1a2e;border-radius:10px;padding:15px 20px;margin:8px 0;border-left:4px solid white;animation:slideInLeft 0.6s ease forwards;transition:transform .3s,border-left-color .3s}
.fivec-card:hover{transform:translateX(8px);border-left-color:#f0a500}
.fivec-title{color:white;font-weight:bold;font-size:15px}
.news-item{background:#1a1a2e;padding:12px 16px;border-radius:8px;margin:6px 0;border-left:3px solid #555;animation:fadeInUp 0.5s ease forwards;transition:border-left-color .3s;color:#cccccc;font-size:13px}
.news-item:hover{border-left-color:white;color:white}
.gst-pass{background:linear-gradient(135deg,#0d2e0d,#1a4a1a);border:1px solid #4caf50;border-radius:10px;padding:15px;animation:zoomIn .8s ease forwards;color:#aaffaa;text-align:center}
.gst-fail{background:linear-gradient(135deg,#2e0d0d,#4a1a1a);border:1px solid #f44336;border-radius:10px;padding:15px;animation:zoomIn .8s ease forwards;color:#ffaaaa;text-align:center}
.gst-warn{background:linear-gradient(135deg,#2e2a0d,#4a3a1a);border:1px solid #ff9800;border-radius:10px;padding:15px;animation:zoomIn .8s ease forwards;color:#ffddaa;text-align:center}
.main-title{animation:fadeInDown 1s ease forwards}
.feature-card{background:#1a1a2e;padding:30px 25px;border-radius:12px;border-left:4px solid white;text-align:center;animation:fadeInUp 1s ease forwards;transition:transform .3s,box-shadow .3s;min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.feature-card:hover{transform:translateY(-8px);box-shadow:0 10px 30px rgba(255,255,255,.15);border-left:4px solid #f0a500}
.feature-icon{font-size:44px;margin-bottom:12px;display:block;line-height:1}
.feature-card h4{color:white;margin-bottom:8px;font-size:16px}
.feature-card p{color:#aaaaaa;font-size:13px;margin:0}
.stat-card{background:#1a1a2e;padding:18px;border-radius:10px;border:1px solid #333;text-align:center;animation:fadeInUp 1.5s ease forwards;transition:transform .3s}
.stat-card:hover{transform:scale(1.05);border-color:white}
.stat-number{font-size:28px;font-weight:bold;color:white}
.stat-label{font-size:12px;color:#aaaaaa;margin-top:5px}
.steps-box{background:#1a1a2e;padding:22px;border-radius:12px;border:1px solid #333;animation:fadeInUp 1.5s ease forwards;min-height:230px}
.step-item{padding:8px 0;color:#aaaaaa;font-size:14px;border-bottom:1px solid #2a2a3e;transition:color .3s}
.step-item:hover{color:white}
.step-item:last-child{border-bottom:none}
.ticker-bar{background:linear-gradient(90deg,#1a1a2e,#2d2d4e,#1a1a2e);padding:10px 0;border-radius:8px;overflow:hidden;white-space:nowrap}
.ticker-text{display:inline-block;animation:ticker 50s linear infinite;color:#aaaaaa;font-size:13px;padding-left:100%}
.badge{display:inline-block;background:#2d2d4e;color:white;padding:5px 14px;border-radius:20px;font-size:12px;margin:4px;border:1px solid #444;transition:border-color .3s,transform .3s}
.badge:hover{border-color:white;transform:scale(1.1)}
</style>
""", unsafe_allow_html=True)

# ── TITLE
st.title("⚡ CredX")
st.subheader("The X Factor in AI-Powered Credit Intelligence")
st.divider()

# ── SIDEBAR
st.sidebar.header("📋 Company Details")
company_name = st.sidebar.text_input("Enter Company Name", placeholder="e.g. Tata Motors")
uploaded_files = st.sidebar.file_uploader(
    "Upload Documents",
    type=["pdf","xlsx","csv","docx","png","jpg","jpeg"],
    accept_multiple_files=True,
    help="PDF, Excel, CSV, Word or Image files"
)
qualitative_notes = st.sidebar.text_area("Additional Notes (Optional)", placeholder="e.g. Factory at 40% capacity.")
st.sidebar.divider()
st.sidebar.header("🧾 GST Cross Check")
gst_file  = st.sidebar.file_uploader("Upload GST Return (Excel/CSV)",    type=["xlsx","csv"])
bank_file = st.sidebar.file_uploader("Upload Bank Statement (Excel/CSV)", type=["xlsx","csv"])
st.sidebar.divider()
st.sidebar.header("🇮🇳 Indian Context")
cibil_score    = st.sidebar.number_input("CIBIL Commercial Score (1-10)", min_value=1, max_value=10, value=5)
gst_mismatch   = st.sidebar.selectbox("GSTR-2A vs 3B Mismatch?", ["No Mismatch","Minor Mismatch (<10%)","Major Mismatch (>10%)"])
rbi_compliance = st.sidebar.selectbox("RBI Compliance Status", ["Fully Compliant","Minor Issues","Non Compliant"])
analyze_button = st.sidebar.button("🔍 Analyze Now", type="primary")

# ── FILE READING
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        total = len(pdf.pages)
        st.info(f"📄 PDF has {total} pages — extracting key financial pages only...")
        pages_to_check = sorted(set(list(range(min(30,total))) + list(range(max(0,total-15),total))))
        extracted = 0
        for i in pages_to_check:
            if extracted > 30: break
            try:
                pt = pdf.pages[i].extract_text()
                if not pt or len(pt.strip()) < 30: continue
                text += pt + "\n"; extracted += 1
            except: continue
        if not text.strip():
            st.warning("⚠️ PDF appears to be scanned. Trying OCR on first 5 pages...")
            try:
                for i in range(min(5,total)):
                    try:
                        img = pdf.pages[i].to_image(resolution=150).original
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip(): text += ocr_text + "\n"
                    except: continue
            except: pass
    return text if text.strip() else "Could not extract text from PDF."

def read_excel(file):
    try:    return f"EXCEL DATA:\n{pd.read_excel(file).to_string()}\n"
    except: return "Could not read Excel file."

def read_csv(file):
    try:    return f"CSV DATA:\n{pd.read_csv(file).to_string()}\n"
    except: return "Could not read CSV file."

def read_word(file):
    try:
        d = docx.Document(file)
        return "WORD DOCUMENT:\n" + "\n".join([p.text for p in d.paragraphs]) + "\n"
    except: return "Could not read Word file."

def read_image(file):
    try:    return f"SCANNED IMAGE TEXT:\n{pytesseract.image_to_string(Image.open(file))}\n"
    except: return "Could not read image file."

def extract_all_files(uploaded_files):
    all_text, summary = "", []
    for file in uploaded_files:
        fn = file.name.lower()
        st.write(f"📄 Reading: {file.name}")
        if   fn.endswith(".pdf"):                  text = read_pdf(file);   summary.append(f"✅ PDF: {file.name}")
        elif fn.endswith((".xlsx",".xls")):        text = read_excel(file); summary.append(f"✅ Excel: {file.name}")
        elif fn.endswith(".csv"):                  text = read_csv(file);   summary.append(f"✅ CSV: {file.name}")
        elif fn.endswith(".docx"):                 text = read_word(file);  summary.append(f"✅ Word: {file.name}")
        elif fn.endswith((".png",".jpg",".jpeg")): text = read_image(file); summary.append(f"✅ Image: {file.name}")
        else:                                      text = "";               summary.append(f"❌ Unknown: {file.name}")
        all_text += f"\n--- FROM FILE: {file.name} ---\n{text}\n"
    return all_text, summary

def cross_check_gst(gst_file, bank_file):
    try:
        gst_df  = pd.read_csv(gst_file)  if gst_file.name.endswith(".csv")  else pd.read_excel(gst_file)
        bank_df = pd.read_csv(bank_file) if bank_file.name.endswith(".csv") else pd.read_excel(bank_file)
        gst_total  = gst_df.select_dtypes(include='number').sum().sum()
        bank_total = bank_df.select_dtypes(include='number').sum().sum()
        pct  = abs(gst_total-bank_total)/bank_total*100 if bank_total>0 else 0
        msg  = f"\nGST CROSS CHECK:\n- GST Total: {gst_total:,.2f}\n- Bank Total: {bank_total:,.2f}\n- Mismatch: {pct:.2f}%\n"
        msg += "HIGH RISK: Major mismatch." if pct>20 else "MEDIUM RISK: Minor mismatch." if pct>10 else "LOW RISK: GST matches bank."
        return msg, pct
    except: return "Could not cross check GST files.", 0

def extract_financial_data(text):
    fd = {"revenue_lines":[],"profit_lines":[],"debt_lines":[],"other_important":[]}
    km = {"revenue":"revenue_lines","turnover":"revenue_lines","net profit":"profit_lines","profit margin":"profit_lines","debt":"debt_lines","borrowing":"debt_lines"}
    for line in text.split("\n"):
        for kw, cat in km.items():
            if kw in line.lower(): fd[cat].append(line.strip()); break
    return fd

def search_news(company_name):
    results = []
    for query in [f"{company_name} India financial results revenue profit",f"{company_name} India fraud scam RBI penalty regulatory",f"{company_name} India loan default NPA bankruptcy",f"{company_name} latest news business"]:
        try:
            r = requests.get("https://newsapi.org/v2/everything", params={"q":query,"language":"en","sortBy":"publishedAt","pageSize":3,"apiKey":NEWS_API_KEY},timeout=8)
            data = r.json()
            if data.get("status")=="ok" and data.get("totalResults",0)>0:
                for a in data["articles"]:
                    title=a.get("title",""); desc=(a.get("description") or "")[:120]
                    if company_name.split()[0].lower() in title.lower(): results.append(f"- {title}: {desc}")
        except: continue
    seen,unique=set(),[]
    for r in results:
        if r not in seen: seen.add(r); unique.append(r)
    return "\n".join(unique[:8]) if unique else "No recent news found."

def search_mca_filings(company_name):
    results = []
    for query in [f"{company_name} MCA ROC Ministry Corporate Affairs India",f"{company_name} SEBI director shareholding India 2024",f"{company_name} GST penalty tax evasion India 2024"]:
        try:
            r = requests.get("https://newsapi.org/v2/everything", params={"q":query,"language":"en","sortBy":"relevancy","pageSize":2,"apiKey":NEWS_API_KEY},timeout=8)
            data = r.json()
            if data.get("status")=="ok" and data.get("totalResults",0)>0:
                for a in data["articles"]:
                    title=a.get("title",""); desc=(a.get("description") or "")[:120]
                    if company_name.split()[0].lower() in title.lower(): results.append(f"- {title}: {desc}")
        except: continue
    return "\n".join(results) if results else "No MCA filings found."

def research_legal_cases(company_name):
    client = Groq(api_key=GROQ_API_KEY)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL, max_tokens=400, temperature=0.0,
            messages=[
                {"role":"system","content":"You are a legal researcher. List real Indian court cases only. Be brief."},
                {"role":"user","content":f"List all known Indian legal cases for {company_name}. Format: [COURT] Title - Year - Summary. If none, write: NO_CASES"}
            ]
        )
        result = response.choices[0].message.content.strip()
        if "NO_CASES" in result or len(result)<20: return "No known legal cases found in Indian courts."
        return result
    except Exception as e: return f"Legal search error: {str(e)[:100]}"

def analyze_credit(company_name, financial_data, news, qualitative_notes, cibil_score, gst_mismatch, rbi_compliance, mca_data, gst_result, legal_cases):
    fs = ""
    for cat, lines in financial_data.items():
        fs += f"\n{cat}:\n" + "".join([f"  - {l}\n" for l in lines])
    client = Groq(api_key=GROQ_API_KEY)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL, max_tokens=800, temperature=0.1,
            messages=[{"role":"user","content":f"""Indian banking credit analyst. Analyze {company_name}.

FINANCIALS: {fs[:800]}
NEWS: {news[:200]}
LEGAL CASES: {legal_cases[:400]}
GST: {gst_result[:150] if gst_result else "Not provided"}
CIBIL:{cibil_score}/10 | GST MISMATCH:{gst_mismatch} | RBI:{rbi_compliance}

Output EXACTLY:
CHARACTER: X/10
[1 line]
CAPACITY: X/10
[1 line]
CAPITAL: X/10
[1 line]
COLLATERAL: X/10
[1 line]
CONDITIONS: X/10
[1 line]
Overall Credit Score: X
Credit Recommendation: Approve/Reject/Need More Info
Suggested Loan Limit: X Crores INR
Suggested Interest Rate: X%
Recommended Tenor: X Years
Early Warning Signals: [list all legal cases and issues]
Reason for Recommendation: [MUST follow this format exactly]
- Decision: [Approved/Rejected/Need More Info]
- Primary Driver: [state the MAIN reason with data source]
- Supporting Factors: [2-3 bullet points each mentioning source]
- Risk Caveat: [any remaining concerns with source]

CHARACTER SCALE: 0 cases=9-10, 1-2 cases=7-8, 3-5 cases=5-6, 6+ cases=3-4, ED/fraud=1-2
Count legal cases above and apply scale strictly."""}]
        )
        return response.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "401" in err or "invalid_api_key" in err.lower(): st.error("❌ Groq API Key is invalid.")
        elif "429" in err or "rate_limit" in err.lower():    st.error("⚠️ Groq rate limit reached. Wait a few minutes.")
        elif "model" in err.lower():                          st.error(f"⚠️ Model error: {err[:200]}")
        else:                                                  st.error(f"⚠️ Analysis failed: {err[:200]}")
        st.stop()

def get_credit_score(analysis_text):
    patterns = {"CHARACTER":r"CHARACTER[:\s]*(\d+)\s*/\s*10","CAPACITY":r"CAPACITY[:\s]*(\d+)\s*/\s*10","CAPITAL":r"CAPITAL[:\s]*(\d+)\s*/\s*10","COLLATERAL":r"COLLATERAL[:\s]*(\d+)\s*/\s*10","CONDITIONS":r"CONDITIONS[:\s]*(\d+)\s*/\s*10"}
    scores = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, analysis_text, re.IGNORECASE)
        scores[name] = int(m.group(1)) if m else None
    if all(v is not None for v in scores.values()):
        base_score = round((scores["CHARACTER"]*0.25+scores["CAPACITY"]*0.25+scores["CAPITAL"]*0.20+scores["COLLATERAL"]*0.15+scores["CONDITIONS"]*0.15)*10)
    else:
        t = analysis_text.lower(); base_score = 50
        if "approve" in t:          base_score += 20
        if "strong financial" in t: base_score += 10
        if "low risk" in t:         base_score += 10
        if "reject" in t:           base_score -= 20
        if "high risk" in t:        base_score -= 15
        if "fraud" in t:            base_score -= 15
    t = analysis_text.lower(); adj = 0
    if "fully compliant" in t: adj += 3
    if "minor issues"    in t: adj -= 3
    if "non compliant"   in t: adj -= 8
    if "no mismatch"     in t: adj += 3
    if "minor mismatch"  in t: adj -= 3
    if "major mismatch"  in t: adj -= 8
    if "fraud detected"  in t: adj -= 10
    return max(0, min(100, base_score+adj))

def parse_five_cs(text):
    scores = {}
    for name in ["CHARACTER","CAPACITY","CAPITAL","COLLATERAL","CONDITIONS"]:
        m = re.search(rf"{name}[:\s]*(\d+)\s*/\s*10", text, re.IGNORECASE)
        scores[name] = int(m.group(1)) if m else 7
    return scores

def parse_final_decision(text):
    r = {}
    m = re.search(r"Overall Credit Score[:\s]*(\d+)", text, re.IGNORECASE)
    r["overall_score"] = int(m.group(1)) if m else get_credit_score(text)
    if   re.search(r"\bApprove\b", text, re.IGNORECASE): r["recommendation"] = "APPROVE"
    elif re.search(r"\bReject\b",  text, re.IGNORECASE): r["recommendation"] = "REJECT"
    else:                                                  r["recommendation"] = "NEED MORE INFO"
    m = re.search(r"Suggested Loan Limit[:\s]*([0-9,]+)", text, re.IGNORECASE)
    r["loan_limit"] = m.group(1).replace(",","") if m else "500"
    m = re.search(r"Suggested Interest Rate[:\s]*([0-9.]+)", text, re.IGNORECASE)
    r["interest_rate"] = m.group(1) if m else "8.5"
    m = re.search(r"Recommended Tenor[:\s]*([0-9]+)", text, re.IGNORECASE)
    r["tenor"] = m.group(1) if m else "5"
    m = re.search(r"Early Warning Signals[:\s]*(.+?)(?=Reason for Recommendation|$)", text, re.IGNORECASE|re.DOTALL)
    if m:
        w = m.group(1).strip()
        r["warning"] = "⚠️ Check Legal Cases section above." if w.lower() in ["none","none.","n/a","none found."] else w[:600]
    else: r["warning"] = "No major warning signals detected."
    m = re.search(r"Reason for Recommendation[:\s]*(.+?)$", text, re.IGNORECASE|re.DOTALL)
    r["reason"] = m.group(1).strip()[:800] if m else "Based on comprehensive analysis of all available data."
    return r

# ══════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════
if not analyze_button:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px;animation:fadeInDown 1s ease forwards;'>
        <h2 style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:6px;
                   background:linear-gradient(135deg,#fff,#6366f1,#8b5cf6);-webkit-background-clip:text;
                   -webkit-text-fill-color:transparent;'>Welcome to CredX ⚡</h2>
        <p style='color:#475569;font-size:15px;letter-spacing:0.03em;'>
            The X Factor in AI-Powered Credit Appraisal for Indian Corporate Lending
        </p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class='ticker-bar'><span class='ticker-text'>
        ⚡ CredX — Instant Credit Decisions &nbsp;|&nbsp; 🏦 Upload Annual Reports &nbsp;|&nbsp;
        🔍 Auto News Search &nbsp;|&nbsp; 🏛️ MCA Filings Check &nbsp;|&nbsp;
        ⚖️ Legal Case Research &nbsp;|&nbsp; 🧾 GST Cross Check &nbsp;|&nbsp;
        📊 Five Cs Analysis &nbsp;|&nbsp; 🇮🇳 CIBIL + RBI + GST Context &nbsp;|&nbsp;
        📋 Professional CAM Report &nbsp;|&nbsp; ✅ Instant Credit Decision &nbsp;|&nbsp;
        ⚡ CredX — Instant Credit Decisions
    </span></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown("<div class='feature-card'><span class='feature-icon'>📄</span><h4>Upload Documents</h4><p>PDF, Excel, Word, CSV and Images — all supported formats</p></div>",  unsafe_allow_html=True)
    with c2: st.markdown("<div class='feature-card'><span class='feature-icon'>🤖</span><h4>AI Analysis</h4><p>Five Cs of Credit with full Indian banking context</p></div>",             unsafe_allow_html=True)
    with c3: st.markdown("<div class='feature-card'><span class='feature-icon'>📊</span><h4>Instant Decision</h4><p>Credit score, loan limit, tenor and interest rate in 2 minutes</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c4,c5,c6,c7 = st.columns(4)
    with c4: st.markdown("<div class='stat-card'><div class='stat-number'>2 Min</div><div class='stat-label'>⏱️ vs Weeks Manually</div></div>", unsafe_allow_html=True)
    with c5: st.markdown("<div class='stat-card'><div class='stat-number'>5+</div><div class='stat-label'>📁 File Formats</div></div>",         unsafe_allow_html=True)
    with c6: st.markdown("<div class='stat-card'><div class='stat-number'>100%</div><div class='stat-label'>🇮🇳 Indian Context</div></div>",    unsafe_allow_html=True)
    with c7: st.markdown("<div class='stat-card'><div class='stat-number'>Free</div><div class='stat-label'>🌐 Live Website</div></div>",        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cl,cr = st.columns(2)
    with cl:
        st.markdown("""<div class='steps-box'>
            <h4 style='color:white;margin-bottom:14px;font-family:Syne,sans-serif;font-weight:700;'>🚀 How to Get Started</h4>
            <div class='step-item'>1️⃣ &nbsp; Enter company name in the sidebar</div>
            <div class='step-item'>2️⃣ &nbsp; Upload annual report PDF or any documents</div>
            <div class='step-item'>3️⃣ &nbsp; Upload GST return and bank statement</div>
            <div class='step-item'>4️⃣ &nbsp; Fill CIBIL score, GST mismatch and RBI status</div>
            <div class='step-item'>5️⃣ &nbsp; Click <strong style='color:white'>🔍 Analyze Now!</strong></div>
        </div>""", unsafe_allow_html=True)
    with cr:
        st.markdown("""<div class='steps-box'>
            <h4 style='color:white;margin-bottom:14px;font-family:Syne,sans-serif;font-weight:700;'>🇮🇳 Indian Banking Features</h4>
            <div class='step-item'>✅ &nbsp; CIBIL Commercial Score analysis</div>
            <div class='step-item'>✅ &nbsp; GSTR-2A vs 3B mismatch detection</div>
            <div class='step-item'>✅ &nbsp; RBI compliance status check</div>
            <div class='step-item'>✅ &nbsp; MCA Ministry of Corporate Affairs filings</div>
            <div class='step-item'>✅ &nbsp; AI-powered legal case research</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;padding:22px;background:rgba(255,255,255,0.03);border-radius:16px;
                border:1px solid rgba(255,255,255,0.07);backdrop-filter:blur(12px);'>
        <p style='color:#475569;margin-bottom:14px;font-size:12px;letter-spacing:0.1em;
                  text-transform:uppercase;font-weight:600;'>Supported File Formats</p>
        <span class='badge'>📄 PDF</span><span class='badge'>📊 Excel</span>
        <span class='badge'>📋 CSV</span><span class='badge'>📝 Word</span><span class='badge'>🖼️ Images</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# RESULTS PAGE
# ══════════════════════════════════════════════════════════════════
if analyze_button:
    if not company_name:
        st.error("Please enter a company name!")
    elif not uploaded_files:
        st.error("Please upload at least one file!")
    else:
        company_name = company_name.strip().title()

        with st.spinner("📄 Reading uploaded files..."):
            all_text, file_summary = extract_all_files(uploaded_files)
            financial_data = extract_financial_data(all_text)
            st.success("✅ Files extracted successfully!")
            for s in file_summary: st.write(s)

        gst_result, mismatch_pct = "", 0
        if gst_file and bank_file:
            with st.spinner("🧾 Cross checking GST vs Bank Statement..."):
                gst_result, mismatch_pct = cross_check_gst(gst_file, bank_file)
                if   mismatch_pct>20: st.error(f"🚨 GST Mismatch: {mismatch_pct:.1f}%")
                elif mismatch_pct>10: st.warning(f"⚠️ Minor GST Mismatch: {mismatch_pct:.1f}%")
                else:                 st.success(f"✅ GST OK: {mismatch_pct:.1f}% mismatch")

        with st.spinner("🔍 Researching news, MCA filings and legal cases simultaneously..."):
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results_map = {}
            def safe_legal(name):
                try:    return research_legal_cases(name)
                except: return "Legal research unavailable."
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(search_news, company_name):        "news",
                    executor.submit(search_mca_filings, company_name): "mca",
                    executor.submit(safe_legal, company_name):         "legal",
                }
                for future in as_completed(futures):
                    key = futures[future]
                    try:    results_map[key] = future.result()
                    except: results_map[key] = f"Could not fetch {key}."
            news       = results_map.get("news",  "No recent news found.")
            mca_data   = results_map.get("mca",   "No MCA filings found.")
            legal_data = results_map.get("legal", "No known legal cases found.")
            st.success("✅ Research complete!")

        with st.spinner("🤖 AI is analyzing credit..."):
            analysis = analyze_credit(company_name, financial_data, news, qualitative_notes,
                                      cibil_score, gst_mismatch, rbi_compliance, mca_data, gst_result, legal_data)

        st.divider()
        col1,col2 = st.columns(2)

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
                if   mismatch_pct>20: st.markdown(f"<div class='gst-fail'><h3>🚨 GST — HIGH RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>Major mismatch — possible circular trading.</p></div>", unsafe_allow_html=True)
                elif mismatch_pct>10: st.markdown(f"<div class='gst-warn'><h3>⚠️ GST — MEDIUM RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>Minor mismatch — investigate further.</p></div>", unsafe_allow_html=True)
                else:                 st.markdown(f"<div class='gst-pass'><h3>✅ GST — LOW RISK</h3><p style='font-size:18px;font-weight:bold;'>Mismatch: {mismatch_pct:.1f}%</p><p>GST matches bank. No circular trading detected.</p></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("🤖 AI Credit Analysis")

        five_cs = parse_five_cs(analysis)
        final   = parse_final_decision(analysis)
        score   = get_credit_score(analysis)

        cs_info = {
            "CHARACTER":  ("👤","Promoter background, fraud history, legal issues, MCA filings"),
            "CAPACITY":   ("💰","Revenue, profit, cash flow and debt repayment ability"),
            "CAPITAL":    ("🏦","Own funds, reserves, debt-to-equity ratio and net worth"),
            "COLLATERAL": ("🏢","Assets available as security — plants, equipment, real estate"),
            "CONDITIONS": ("🌍","Industry outlook, RBI regulations, market and legal conditions"),
        }

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:white;font-family:Syne,sans-serif;'>📋 Five Cs Breakdown</h4>", unsafe_allow_html=True)

        for name,(icon,desc) in cs_info.items():
            sv  = five_cs.get(name,7)
            pct = sv*10
            col = "#10b981" if sv>=8 else "#f59e0b" if sv>=6 else "#f43f5e"
            st.markdown(f"""
            <div class='fivec-card'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div><span style='font-size:22px;'>{icon}</span>
                         <span class='fivec-title' style='margin-left:10px;'>{name}</span></div>
                    <span style='background:{col}22;color:{col};border:1px solid {col}55;
                                 font-weight:700;padding:4px 16px;border-radius:20px;font-size:14px;
                                 font-family:Syne,sans-serif;'>{sv}/10</span>
                </div>
                <div style='color:#475569;font-size:12px;margin:8px 0 10px 32px;'>{desc}</div>
                <div style='background:rgba(255,255,255,0.05);border-radius:20px;height:6px;overflow:hidden;'>
                    <div style='width:{pct}%;background:linear-gradient(90deg,{col},{col}88);
                                height:6px;border-radius:20px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:white;font-family:Syne,sans-serif;'>🏆 Key Decision Metrics</h4>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        def metric_card(icon, label, value, sub):
            return f"""<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                        border-radius:16px;padding:22px;text-align:center;backdrop-filter:blur(16px);
                        box-shadow:0 4px 24px rgba(0,0,0,0.3);'>
                <div style='font-size:11px;color:#475569;letter-spacing:0.08em;text-transform:uppercase;
                            font-weight:600;margin-bottom:8px;'>{icon} {label}</div>
                <div style='font-size:34px;font-weight:900;color:white;font-family:Syne,sans-serif;
                            line-height:1;margin:8px 0;'>{value}</div>
                <div style='font-size:12px;color:#475569;'>{sub}</div>
            </div>"""

        m1,m2,m3,m4,m5 = st.columns(5)
        with m1: st.markdown(metric_card("📊","Score",     score,                   "out of 100"), unsafe_allow_html=True)
        with m2: st.markdown(metric_card("💰","Loan",      f"₹{final['loan_limit']}","Crores INR"), unsafe_allow_html=True)
        with m3: st.markdown(metric_card("📈","Interest",  f"{final['interest_rate']}%","per annum"), unsafe_allow_html=True)
        with m4: st.markdown(metric_card("📅","Tenor",     final['tenor'],           "Years"),      unsafe_allow_html=True)
        with m5:
            rec=final["recommendation"]
            rc ="#10b981" if rec=="APPROVE" else "#f43f5e" if rec=="REJECT" else "#f59e0b"
            ri ="✅" if rec=="APPROVE" else "❌" if rec=="REJECT" else "⚠️"
            st.markdown(f"""<div style='background:rgba(255,255,255,0.03);border:2px solid {rc}44;
                        border-radius:16px;padding:22px;text-align:center;backdrop-filter:blur(16px);
                        box-shadow:0 0 40px {rc}18;'>
                <div style='font-size:11px;color:#475569;letter-spacing:0.08em;text-transform:uppercase;
                            font-weight:600;margin-bottom:8px;'>🏷️ Decision</div>
                <div style='font-size:30px;margin:8px 0;'>{ri}</div>
                <div style='font-size:14px;font-weight:700;color:{rc};font-family:Syne,sans-serif;
                            letter-spacing:0.05em;'>{rec}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        w1,w2 = st.columns(2)
        with w1:
            st.markdown(f"""<div style='background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.2);
                        border-left:3px solid #f59e0b;border-radius:14px;padding:22px;backdrop-filter:blur(12px);'>
                <h5 style='color:#f59e0b;margin-bottom:12px;font-family:Syne,sans-serif;'>⚠️ Early Warning Signals</h5>
                <p style='color:#94a3b8;font-size:13px;line-height:1.75;white-space:pre-line;'>{final["warning"]}</p>
            </div>""", unsafe_allow_html=True)
        with w2:
            st.markdown(f"""<div style='background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);
                        border-left:3px solid #10b981;border-radius:14px;padding:22px;backdrop-filter:blur(12px);'>
                <h5 style='color:#10b981;margin-bottom:12px;font-family:Syne,sans-serif;'>💡 Reason for Decision</h5>
                <p style='color:#94a3b8;font-size:13px;line-height:1.75;'>{final["reason"]}</p>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # ── FINAL CREDIT DECISION BANNER
        st.markdown("""<h2 style='color:white;text-align:center;font-family:Syne,sans-serif;
                       font-weight:800;letter-spacing:-0.02em;margin-bottom:4px;'>
                       🏆 FINAL CREDIT DECISION</h2>""", unsafe_allow_html=True)
        st.markdown("""<p style='color:#475569;text-align:center;font-size:13px;letter-spacing:0.05em;margin-bottom:32px;'>
                       AI-powered assessment based on Five Cs · News · Legal Research · GST Analysis</p>""", unsafe_allow_html=True)

        if score>=70:
            mc="#10b981"; bg="135deg,rgba(16,185,129,0.06),rgba(5,150,105,0.04),rgba(3,3,10,0.8)"
            bc="rgba(16,185,129,0.35)"; gc="rgba(16,185,129,0.12)"
            dt="LOAN APPROVED"; di="✅"; rl="LOW RISK"; ri2="🟢"
            adv="Strong financial profile. Recommended for lending with standard covenants."; tc="#6ee7b7"
        elif score>=50:
            mc="#f59e0b"; bg="135deg,rgba(245,158,11,0.06),rgba(180,83,9,0.04),rgba(3,3,10,0.8)"
            bc="rgba(245,158,11,0.35)"; gc="rgba(245,158,11,0.10)"
            dt="NEED MORE INFO"; di="⚠️"; rl="MEDIUM RISK"; ri2="🟡"
            adv="Borderline profile. Additional documents and due diligence required."; tc="#fcd34d"
        else:
            mc="#f43f5e"; bg="135deg,rgba(244,63,94,0.06),rgba(185,28,28,0.04),rgba(3,3,10,0.8)"
            bc="rgba(244,63,94,0.35)"; gc="rgba(244,63,94,0.10)"
            dt="LOAN REJECTED"; di="❌"; rl="HIGH RISK"; ri2="🔴"
            adv="Significant risks identified. Lending is inadvisable at this time."; tc="#fca5a5"

        st.markdown(f"""
        <div style='background:linear-gradient({bg});border:1px solid {bc};border-radius:22px;
                    padding:44px 52px;margin-bottom:24px;backdrop-filter:blur(30px);
                    box-shadow:0 0 80px {gc},0 20px 60px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.05);
                    position:relative;overflow:hidden;'>
            <div style='position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,{mc},transparent);'></div>
            <div style='display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:24px;'>
                <div>
                    <div style='font-size:11px;color:#475569;letter-spacing:4px;text-transform:uppercase;margin-bottom:10px;font-weight:600;'>Credit Decision</div>
                    <div style='font-size:40px;font-weight:900;color:white;letter-spacing:-0.01em;line-height:1;font-family:Syne,sans-serif;'>{di} {dt}</div>
                    <div style='font-size:14px;color:{tc};margin-top:14px;max-width:520px;line-height:1.7;'>💡 {adv}</div>
                </div>
                <div style='text-align:center;background:rgba(255,255,255,0.04);border:1px solid {bc};
                            border-radius:18px;padding:24px 40px;min-width:170px;box-shadow:0 8px 32px rgba(0,0,0,0.3);'>
                    <div style='font-size:70px;font-weight:900;color:white;line-height:1;font-family:Syne,sans-serif;'>{score}</div>
                    <div style='font-size:12px;color:#475569;margin-top:8px;letter-spacing:0.06em;text-transform:uppercase;font-weight:600;'>Credit Score / 100</div>
                    <div style='margin-top:12px;background:rgba(255,255,255,0.07);border-radius:20px;height:5px;overflow:hidden;'>
                        <div style='width:{score}%;background:{mc};height:5px;border-radius:20px;'></div>
                    </div>
                </div>
            </div>
            <div style='position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,{mc},transparent);'></div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;'>
            <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-top:2px solid {mc};border-radius:16px;padding:24px;text-align:center;backdrop-filter:blur(16px);'>
                <div style='font-size:11px;color:#475569;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;font-weight:600;'>Risk Level</div>
                <div style='font-size:28px;margin-bottom:8px;'>{ri2}</div>
                <div style='font-size:17px;font-weight:700;color:{mc};font-family:Syne,sans-serif;'>{rl}</div>
            </div>
            <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-top:2px solid #6366f1;border-radius:16px;padding:24px;text-align:center;backdrop-filter:blur(16px);'>
                <div style='font-size:11px;color:#475569;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;font-weight:600;'>Loan Limit</div>
                <div style='font-size:28px;margin-bottom:8px;'>💰</div>
                <div style='font-size:17px;font-weight:700;color:white;font-family:Syne,sans-serif;'>₹{final["loan_limit"]} Cr</div>
            </div>
            <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-top:2px solid #8b5cf6;border-radius:16px;padding:24px;text-align:center;backdrop-filter:blur(16px);'>
                <div style='font-size:11px;color:#475569;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;font-weight:600;'>Interest Rate</div>
                <div style='font-size:28px;margin-bottom:8px;'>📈</div>
                <div style='font-size:17px;font-weight:700;color:white;font-family:Syne,sans-serif;'>{final["interest_rate"]}% p.a.</div>
            </div>
            <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-top:2px solid #38bdf8;border-radius:16px;padding:24px;text-align:center;backdrop-filter:blur(16px);'>
                <div style='font-size:11px;color:#475569;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;font-weight:600;'>Tenor</div>
                <div style='font-size:28px;margin-bottom:8px;'>📅</div>
                <div style='font-size:17px;font-weight:700;color:white;font-family:Syne,sans-serif;'>{final["tenor"]} Years</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Five Cs summary
        def c_col(v): return "#10b981" if v>=8 else "#f59e0b" if v>=6 else "#f43f5e"
        def c_card(name,val):
            col=c_col(val)
            return (f"<div style='text-align:center;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px 12px;backdrop-filter:blur(12px);'>"
                    f"<div style='font-size:10px;color:#475569;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;font-weight:600;'>{name}</div>"
                    f"<div style='font-size:28px;font-weight:900;color:{col};line-height:1;font-family:Syne,sans-serif;'>{val}"
                    f"<span style='font-size:13px;color:#334155;font-weight:400;'>/10</span></div>"
                    f"<div style='background:rgba(255,255,255,0.05);border-radius:4px;height:4px;margin-top:12px;overflow:hidden;'>"
                    f"<div style='width:{val*10}%;background:linear-gradient(90deg,{col},{col}88);height:4px;border-radius:4px;'></div></div></div>")

        st.markdown(
            f"<div style='background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:18px;"
            f"padding:28px 30px;backdrop-filter:blur(20px);box-shadow:0 8px 40px rgba(0,0,0,0.3),'>"
            f"<div style='font-size:11px;color:#475569;letter-spacing:3px;text-transform:uppercase;margin-bottom:18px;font-weight:600;'>Five Cs Summary</div>"
            f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:12px;'>"
            + c_card("CHARACTER",  five_cs.get("CHARACTER",7))
            + c_card("CAPACITY",   five_cs.get("CAPACITY",7))
            + c_card("CAPITAL",    five_cs.get("CAPITAL",7))
            + c_card("COLLATERAL", five_cs.get("COLLATERAL",7))
            + c_card("CONDITIONS", five_cs.get("CONDITIONS",7))
            + "</div></div>",
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        report_path = generate_credit_report(company_name, financial_data, news, analysis)
        with open(report_path,"rb") as f:
            st.download_button(
                label="⬇️ Download Professional Credit Report (PDF)",
                data=f,
                file_name=f"{company_name}_CredX_Report.pdf",
                mime="application/pdf"
            )
