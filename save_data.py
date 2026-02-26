import pdfplumber
import json

all_text = ""

with pdfplumber.open("sample.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_text += text + "\n"

# We will store extracted data here
financial_data = {
    "revenue_lines": [],
    "profit_lines": [],
    "debt_lines": [],
    "other_important": []
}

keywords_map = {
    "revenue": "revenue_lines",
    "turnover": "revenue_lines",
    "net profit": "profit_lines",
    "profit margin": "profit_lines",
    "debt": "debt_lines",
    "borrowing": "debt_lines",
}

for line in all_text.split("\n"):
    for keyword, category in keywords_map.items():
        if keyword.lower() in line.lower():
            financial_data[category].append(line.strip())
            break

# Save to a JSON file
with open("financial_data.json", "w") as f:
    json.dump(financial_data, f, indent=4)

print("✅ Data saved to financial_data.json")
print("\nHere's what we found:\n")
for category, lines in financial_data.items():
    print(f"--- {category} ---")
    for line in lines:
        print(line)
    print()