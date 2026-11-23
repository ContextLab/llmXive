import os
import sys
import json
import re
import csv
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root resolution
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"
STATE_DIR = ROOT / "state"
UTILS_DIR = ROOT / "code" / "utils"

# Ensure directories exist (idempotent)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Constants
DOI_URL = "https://www.nature.com/articles/sdata201785.csv"
# Fallback direct link if the DOI landing page doesn't serve CSV directly.
# The dataset is from: "A large-scale dataset of thermoelectric materials properties"
# Direct data link often used for this specific dataset:
REAL_DATA_URL = "https://ndownloader.figstatic.com/files/8663971"
TARGET_FAMILIES = ["Bi-Te", "Pb-Te", "Skutterudites"]
MAPPING_FILE = UTILS_DIR / "mapping.json"
OUTPUT_FILE = DATA_PROCESSED_DIR / "cleaned_compositions.csv"
RETENTION_LOG = STATE_DIR / "retention_log.json"

def fetch_data() -> str:
    """
    Downloads the raw CSV data from the real source.
    Raises an exception if the download fails.
    """
    if not DATA_RAW_DIR.exists():
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = DATA_RAW_DIR / "raw_thermoelectric.csv"
    
    # Attempt to fetch from the verified real source
    try:
        print(f"Fetching data from {REAL_DATA_URL}...")
        urllib.request.urlretrieve(REAL_DATA_URL, output_path)
        print(f"Data saved to {output_path}")
    except Exception as e:
        print(f"CRITICAL: Failed to download real data from {REAL_DATA_URL}: {e}", file=sys.stderr)
        # Do not fallback to synthetic data. Fail loudly.
        raise RuntimeError(f"Data download failed: {e}")
    
    return str(output_path)

def parse_csv_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Parses the CSV file into a list of dictionaries.
    Handles potential encoding issues and empty lines.
    """
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Use csv.DictReader for robust parsing
            reader = csv.DictReader(f)
            for row in reader:
                # Filter out completely empty rows
                if any(v.strip() for v in row.values()):
                    records.append(row)
    except Exception as e:
        print(f"Error parsing CSV: {e}", file=sys.stderr)
        raise
    
    return records

def load_family_mapping() -> Dict[str, str]:
    """
    Loads the stoichiometry to family mapping from utils/mapping.json.
    """
    if not MAPPING_FILE.exists():
        print(f"CRITICAL: Mapping file not found at {MAPPING_FILE}", file=sys.stderr)
        raise FileNotFoundError(f"Mapping file not found: {MAPPING_FILE}")
    
    with open(MAPPING_FILE, 'r') as f:
        return json.load(f)

def map_family(composition: str, mapping: Dict[str, str]) -> Optional[str]:
    """
    Maps a stoichiometric formula to a material family using the provided mapping.
    Returns None if no match is found.
    """
    if not composition or not isinstance(composition, str):
        return None
    
    # Normalize composition string (remove spaces, standardize case if needed)
    normalized = composition.replace(" ", "").strip()
    
    # Direct lookup
    if normalized in mapping:
        return mapping[normalized]
    
    # Try case-insensitive lookup
    lower_map = {k.lower(): v for k, v in mapping.items()}
    if normalized.lower() in lower_map:
        return lower_map[normalized.lower()]
    
    # Partial match for complex formulas if exact match fails
    # e.g., "Bi2Te3" might be mapped, but we check if the key is a substring
    # or if the composition contains a known key.
    for key, family in mapping.items():
        if key in normalized or normalized in key:
            return family
    
    return None

def clean_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cleans a single record:
    - Extracts composition and Seebeck coefficient.
    - Validates that required fields exist and are not empty.
    - Returns None if the record is invalid.
    """
    # Identify fields. The dataset usually has 'Composition' and 'Seebeck_Coefficient'
    # or similar. We need to be flexible.
    comp_val = None
    seebeck_val = None
    
    # Heuristic field names
    comp_keys = ['Composition', 'composition', 'Formula', 'formula', 'Stoichiometry']
    seebeck_keys = ['Seebeck_Coefficient', 'Seebeck', 'Seebeck_Coeff', 'S (uV/mK)', 'Seebeck (uV/mK)']
    
    for key in comp_keys:
        if key in record and record[key]:
            comp_val = str(record[key]).strip()
            break
    
    for key in seebeck_keys:
        if key in record and record[key]:
            seebeck_val = record[key]
            break
    
    if not comp_val or not seebeck_val:
        return None
    
    # Try to parse Seebeck as float
    try:
        # Handle potential unit suffixes or weird formatting
        s_clean = re.sub(r'[^\d.\-]', '', str(seebeck_val))
        if not s_clean:
            return None
        seebeck_float = float(s_clean)
    except (ValueError, TypeError):
        return None
    
    return {
        "original_record": record,
        "composition": comp_val,
        "seebeck": seebeck_float
    }

def filter_records(records: List[Dict[str, Any]], mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Filters records:
    1. Cleans the record (removes invalid entries).
    2. Maps the composition to a family.
    3. Retains only records where family is in TARGET_FAMILIES.
    """
    cleaned_records = []
    
    for record in records:
        # Clean
        clean = clean_record(record)
        if not clean:
            continue
        
        # Map Family
        family = map_family(clean["composition"], mapping)
        if not family:
            continue
        
        # Filter by Target Families
        if family not in TARGET_FAMILIES:
            continue
        
        # Add family to the clean record
        clean["family"] = family
        cleaned_records.append(clean)
    
    return cleaned_records

def log_retention(total_input: int, retained_count: int) -> Dict[str, Any]:
    """
    Calculates retention rate and logs the result.
    Exits with code 1 if retention < 95%.
    """
    rate = retained_count / total_input if total_input > 0 else 0.0
    status = "PASS" if rate >= 0.95 else "FAIL"
    
    log_entry = {
        "retention_rate": rate,
        "total_input": total_input,
        "retained_count": retained_count,
        "status": status
    }
    
    # Write log
    with open(RETENTION_LOG, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"Retention Check: {rate:.2%} ({retained_count}/{total_input}) - {status}")
    
    if status == "FAIL":
        print("CRITICAL: Retention < 95%", file=sys.stderr)
        sys.exit(1)
    
    return log_entry

def main():
    """
    Main execution flow:
    1. Fetch data.
    2. Parse data.
    3. Load mapping.
    4. Filter and map families.
    5. Save cleaned data.
    6. Log retention.
    """
    print("Starting data ingestion and cleaning pipeline...")
    
    # 1. Fetch
    raw_file = fetch_data()
    
    # 2. Parse
    records = parse_csv_data(raw_file)
    if not records:
        print("CRITICAL: No records found in downloaded file.", file=sys.stderr)
        sys.exit(1)
    print(f"Parsed {len(records)} raw records.")
    
    # 3. Load Mapping
    mapping = load_family_mapping()
    print(f"Loaded family mapping with {len(mapping)} entries.")
    
    # 4. Filter & Map
    # Note: This step includes the stoichiometry mapping logic required for T013
    filtered_records = filter_records(records, mapping)
    print(f"Filtered records: {len(filtered_records)} (Target families: {TARGET_FAMILIES})")
    
    # 5. Save
    if not DATA_PROCESSED_DIR.exists():
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        if filtered_records:
            writer = csv.DictWriter(f, fieldnames=["composition", "seebeck", "family"])
            writer.writeheader()
            for rec in filtered_records:
                writer.writerow({
                    "composition": rec["composition"],
                    "seebeck": rec["seebeck"],
                    "family": rec["family"]
                })
        else:
            # Write empty file with header if no records
            writer = csv.DictWriter(f, fieldnames=["composition", "seebeck", "family"])
            writer.writeheader()
    
    print(f"Saved {len(filtered_records)} records to {OUTPUT_FILE}")
    
    # 6. Log Retention
    log_retention(len(records), len(filtered_records))
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()