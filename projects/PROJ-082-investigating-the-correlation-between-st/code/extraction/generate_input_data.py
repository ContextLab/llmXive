"""
Utility to generate a realistic input CSV for T013 testing.
This script creates data/raw/input_studies.csv with a mix of:
- Complete rows (r, n, tract)
- Rows with p-value instead of r
- Rows with text descriptions but no numbers
- Rows missing data entirely
"""
import csv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INPUT_PATH = RAW_DIR / "input_studies.csv"

def generate_input_data():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    data = [
        # Complete row
        {"id": "S001", "author": "Smith", "year": "2020", "tract": "arcuate fasciculus", "r": "0.45", "n": "50", "p": "0.01", "notes": "Strong correlation in arcuate fasciculus."},
        # Missing r, has p
        {"id": "S002", "author": "Doe", "year": "2019", "tract": "cingulum bundle", "r": "", "n": "30", "p": "0.03", "notes": "Significant finding in cingulum."},
        # Missing numbers, text only
        {"id": "S003", "author": "Lee", "year": "2021", "tract": "", "r": "", "n": "", "p": "", "notes": "Increased connectivity observed in the uncinate fasciculus associated with reward processing."},
        # Missing numbers, no tract text
        {"id": "S004", "author": "Kim", "year": "2018", "tract": "uncinate fasciculus", "r": "", "n": "", "p": "", "notes": "General observation of brain structure."},
        # Complete row
        {"id": "S005", "author": "Garcia", "year": "2022", "tract": "inferior longitudinal fasciculus", "r": "0.32", "n": "45", "p": "0.05", "notes": "Moderate correlation."},
        # Missing r/n completely
        {"id": "S006", "author": "Brown", "year": "2017", "tract": "auditory cortex", "r": "", "n": "", "p": "", "notes": "No specific numbers reported."},
        # Complete row
        {"id": "S007", "author": "Wilson", "year": "2023", "tract": "ventral striatum", "r": "0.55", "n": "60", "p": "0.001", "notes": "Strong association."},
        # Text with tract but no numbers
        {"id": "S008", "author": "Taylor", "year": "2020", "tract": "", "r": "", "n": "", "p": "", "notes": "Decreased connectivity in the arcuate fasciculus."},
        # Complete row
        {"id": "S009", "author": "Anderson", "year": "2019", "tract": "arcuate fasciculus", "r": "0.28", "n": "40", "p": "0.08", "notes": "Weak correlation."},
        # Complete row
        {"id": "S010", "author": "Thomas", "year": "2021", "tract": "cingulum bundle", "r": "0.40", "n": "35", "p": "0.02", "notes": "Moderate positive correlation."},
        # Text only
        {"id": "S011", "author": "Jackson", "year": "2022", "tract": "", "r": "", "n": "", "p": "", "notes": "Ventral striatum activation linked to music preference."},
        # Complete row
        {"id": "S012", "author": "White", "year": "2018", "tract": "inferior longitudinal fasciculus", "r": "0.35", "n": "55", "p": "0.04", "notes": "Significant."},
        # Complete row
        {"id": "S013", "author": "Harris", "year": "2020", "tract": "auditory cortex", "r": "0.50", "n": "48", "p": "0.01", "notes": "Strong."},
        # Complete row
        {"id": "S014", "author": "Martin", "year": "2023", "tract": "uncinate fasciculus", "r": "0.22", "n": "30", "p": "0.10", "notes": "Non-significant trend."},
        # Complete row
        {"id": "S015", "author": "Thompson", "year": "2019", "tract": "ventral striatum", "r": "0.60", "n": "70", "p": "0.005", "notes": "Very strong."},
    ]
    
    fieldnames = ["id", "author", "year", "tract", "r", "n", "p", "notes"]
    
    with open(INPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated input data at {INPUT_PATH}")

if __name__ == "__main__":
    generate_input_data()
