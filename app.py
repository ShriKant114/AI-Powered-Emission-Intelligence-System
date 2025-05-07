import pdfplumber
import re
import pandas as pd
from transformers import pipeline
from fuzzywuzzy import fuzz

# Extract text
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Chunk into sentences
def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

# Smart pairings from sentence-level extraction
def extract_structured_data(text):
    ner = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
    sentences = split_sentences(text)
    results = []

    for sentence in sentences:
        entities = ner(sentence)
        company = location = year = emission = ""

        # Get values from NER
        for ent in entities:
            label = ent['entity_group']
            word = ent['word'].strip()
            if label == 'ORG' and not company:
                company = word
            elif label == 'LOC' and not location:
                location = word
            elif label == 'DATE' and not year:
                match = re.search(r"\b(19|20)\d{2}\b", word)
                if match:
                    year = match.group()

        # Regex for emission
        match = re.search(r"\b\d{1,3}(?:\.\d+)?\s*(MtCO2e|million tonnes|tons|tonnes)\b", sentence, re.IGNORECASE)
        if match:
            emission = match.group()

        if company and (emission or year or location):
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

# Save
def save_to_csv(data, filename):
    df = pd.DataFrame(data, columns=["Company Name", "Year", "Location", "Carbon Emission"])
    df.to_csv(filename, index=False)
    print(f"✅ Saved: {filename}")

# Main
def main():
    pdf_path = "data.pdf"
    output_csv = "cleaned_data.csv"

    text = extract_text_from_pdf(pdf_path)
    data = extract_structured_data(text)
    if not data:
        print("❌ No data extracted.")
        return
    save_to_csv(data, output_csv)

# Run
main()
