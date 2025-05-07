import pdfplumber
import re
import pandas as pd
import spacy
from fuzzywuzzy import fuzz

# Load the Spacy model for NER
nlp = spacy.load("en_core_web_sm")

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Split the text into sentences
def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

# Extract structured data from the text
def extract_structured_data(text):
    sentences = split_sentences(text)
    results = []

    for sentence in sentences:
        # Use Spacy NER to extract entities
        doc = nlp(sentence)
        company = location = year = emission = ""

        # Get values from NER
        for ent in doc.ents:
            if ent.label_ == 'ORG' and not company:
                company = ent.text.strip()

            elif ent.label_ == 'GPE' and not location:
                location = ent.text.strip()

            elif ent.label_ == 'DATE' and not year:
                year_match = re.search(r"\b(19|20)\d{2}\b", ent.text)
                if year_match:
                    year = year_match.group()

        # If year is still empty, try regex fallback
        if not year:
            year_match = re.search(r"\b(19|20)\d{2}\b", sentence)
            if year_match:
                year = year_match.group()

        # Refined regex for emission
        match = re.search(r"\b\d{1,3}(?:\.\d+)?\s*(MtCO2e|million\s*tonnes|tons|tonnes|kilotonnes|kgCO2)\b", sentence, re.IGNORECASE)
        if match:
            emission = match.group()

        # Filter out sentences that contain "Location" or "Carbon Emissions" alongside the company name
        if company and (emission or year or location):
            # Clean company name (remove any extra text such as "Location" or "Carbon Emissions")
            company = re.sub(r"\s*(Location|Carbon Emissions|•).*", "", company)
            company = company.replace("•", "").strip()  # Remove extra "•" characters
            if company and year and location:
                results.append([company, year, location, emission])

    # Remove duplicates (fuzzy match)
    cleaned = []
    seen = set()

    for row in results:
        name = row[0]
        if any(fuzz.ratio(name, old[0]) > 90 for old in cleaned):
            continue
        cleaned.append(row)

    return cleaned

# Save the extracted data to a CSV file
def save_to_csv(data, filename):
    df = pd.DataFrame(data, columns=["Company Name", "Year", "Location", "Carbon Emission"])
    df.to_csv(filename, index=False)
    print(f"✅ Saved: {filename}")

# Main function to run the script
def main():
    pdf_path = "data.pdf"
    output_csv = "cleaned_data.csv"

    text = extract_text_from_pdf(pdf_path)
    data = extract_structured_data(text)
    if not data:
        print("❌ No data extracted.")
        return
    save_to_csv(data, output_csv)

# Run the main function
main()
