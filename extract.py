import pdfplumber
import re

# Store all text from PDF
all_text = ""

with pdfplumber.open("sample.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_text += text + "\n"

# Now search for important keywords
keywords = ["revenue", "net profit", "total debt", "total assets", "turnover", "borrowings"]

print("=== KEY FINANCIAL INFORMATION FOUND ===\n")

for line in all_text.split("\n"):
    for keyword in keywords:
        if keyword.lower() in line.lower():
            print(line)
            break