import pdfplumber

# Open the PDF file
with pdfplumber.open("sample.pdf") as pdf:
    
    print(f"Total pages: {len(pdf.pages)}")
    
    # Read first 5 pages
    for i, page in enumerate(pdf.pages[:5]):
        text = page.extract_text()
        print(f"\n--- Page {i+1} ---")
        print(text)