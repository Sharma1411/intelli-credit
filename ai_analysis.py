from groq import Groq
import json

# Load your saved financial data
with open("financial_data.json", "r") as f:
    financial_data = json.load(f)

# Convert it to readable text
financial_summary = ""
for category, lines in financial_data.items():
    financial_summary += f"\n{category}:\n"
    for line in lines:
        financial_summary += f"  - {line}\n"

# Connect to Groq AI
client = Groq(api_key="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")

# Ask AI to analyze
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""You are an expert Indian banking credit analyst.

Here is the financial data extracted from a company's annual report:

{financial_summary}

Please analyze this and provide:
1. Overall financial health (Good / Average / Poor)
2. Key strengths you see
3. Key risks you see
4. Preliminary credit recommendation (Approve / Reject / Need More Info)
5. Reason for your recommendation

Keep it simple and clear."""
        }
    ]
)

# Print and save result
result = response.choices[0].message.content

print("=== AI CREDIT ANALYSIS ===\n")
print(result)

with open("ai_analysis.txt", "w") as f:
    f.write(result)

print("\n✅ Analysis saved to ai_analysis.txt")