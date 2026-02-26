import requests
import json
from groq import Groq

# ==============================
# PASTE YOUR KEYS HERE
# ==============================
GROQ_API_KEY = "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"
NEWS_API_KEY = "a86cb2ce9c944edb911864ef2f8c0077"
# ==============================
# STEP 1: Search News about company
# ==============================
def search_company_news(company_name):
    print(f"\n🔍 Searching news about: {company_name}")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{company_name} India finance loan fraud legal",
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    news_summary = ""
    if data["status"] == "ok" and data["totalResults"] > 0:
        for article in data["articles"]:
            title = article["title"]
            description = article["description"] or ""
            news_summary += f"- {title}: {description}\n"
    else:
        news_summary = "No recent news found."
    
    return news_summary

# ==============================
# STEP 2: Load financial data
# ==============================
with open("financial_data.json", "r") as f:
    financial_data = json.load(f)

financial_summary = ""
for category, lines in financial_data.items():
    financial_summary += f"\n{category}:\n"
    for line in lines:
        financial_summary += f"  - {line}\n"

# ==============================
# STEP 3: Ask user for company name
# ==============================
company_name = input("\nEnter the company name: ")

# ==============================
# STEP 4: Get news
# ==============================
news = search_company_news(company_name)
print("\n📰 News Found:")
print(news)

# ==============================
# STEP 5: Send everything to AI
# ==============================
client = Groq(api_key=GROQ_API_KEY)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""You are an expert Indian banking credit analyst.

COMPANY NAME: {company_name}

FINANCIAL DATA FROM ANNUAL REPORT:
{financial_summary}

RECENT NEWS ABOUT THE COMPANY:
{news}

Based on BOTH the financial data AND the news, provide:
1. Overall financial health (Good / Average / Poor)
2. Key strengths
3. Key risks (include any news-based risks)
4. Credit recommendation (Approve / Reject / Need More Info)
5. Suggested loan limit (give a number)
6. Suggested interest rate (give a percentage)
7. Reason for recommendation

Be specific and mention if any news affected your decision."""
        }
    ]
)

result = response.choices[0].message.content

print("\n=== FINAL AI CREDIT ANALYSIS ===\n")
print(result)

# Save everything
with open("final_analysis.txt", "w", encoding="utf-8") as f:
    f.write(f"Company: {company_name}\n\n")
    f.write(f"NEWS FOUND:\n{news}\n\n")
    f.write(f"AI ANALYSIS:\n{result}")

print("\n✅ Final analysis saved to final_analysis.txt")