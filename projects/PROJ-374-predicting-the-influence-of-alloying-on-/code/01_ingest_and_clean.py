import os
import sys
import json
import re
import csv
import urllib.request
from pathlib import Path
from io import StringIO
import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Constants
DATA_URL = "https://www.nature.com/articles/sdata201785.files/sdata201785-c1.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "cleaned_compositions.csv"
STATE_DIR = project_root / "state"
MAPPING_PATH = project_root / "code" / "utils" / "mapping.json"
TARGET_FAMILIES = ["Bi-Te", "Pb-Te", "Skutterudites"]

def fetch_data(url: str) -> str:
    """Fetch CSV data from a URL."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data from {url}: {e}")

def parse_csv_data(csv_content: str) -> pd.DataFrame:
    """Parse CSV string into a DataFrame."""
    try:
        # Use StringIO to read the string as a file-like object
        df = pd.read_csv(StringIO(csv_content))
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to parse CSV data: {e}")

def clean_record(row: pd.Series) -> pd.Series:
    """
    Clean a single record.
    - Strip whitespace from string columns.
    - Normalize missing values (e.g., 'NA', 'N/A', 'null') to np.nan.
    - Ensure numeric columns are numeric.
    """
    import numpy as np
    
    # Handle missing value strings
    for col in row.index:
        if isinstance(row[col], str):
            val = row[col].strip()
            if val.lower() in ['na', 'n/a', 'null', 'none', '']:
                row[col] = np.nan
            else:
                row[col] = val
    
    # Ensure numeric columns are numeric
    for col in row.index:
        if row[col] is not None and not isinstance(row[col], (int, float)):
            try:
                row[col] = float(row[col])
            except (ValueError, TypeError):
                pass # Keep as string if conversion fails
    
    return row

def load_family_mapping(mapping_path: str) -> dict:
    """Load the family mapping JSON."""
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
    with open(mapping_path, 'r') as f:
        return json.load(f)

def map_family(row: pd.Series, mapping: dict) -> str:
    """
    Map a material to a family based on its formula.
    Returns 'Unknown' if no match is found.
    """
    formula = str(row.get('formula', row.get('Formula', ''))).strip()
    if not formula:
        return "Unknown"
    
    # Check direct match
    if formula in mapping:
        return mapping[formula]
    
    # Check partial match (e.g., "Bi2Te3" matches keys starting with "Bi")
    # The mapping is expected to be {formula: family}
    # We need to handle variations. Let's assume the mapping covers specific stoichiometries
    # or prefixes. For this task, we rely on the mapping.json content.
    # If the mapping has "Bi2Te3": "Bi-Te", we check exact first.
    # If not found, we might need to check if the formula contains elements of a family.
    # However, the task says "Use utils/mapping.json".
    # Let's implement a simple substring check if the mapping keys are prefixes or patterns.
    # Given the constraint, we'll assume the mapping covers the specific formulas we care about.
    # If the mapping is sparse, we might need to infer.
    # For now, let's try to match if the formula starts with a key in the mapping
    # or if the mapping keys are sub-formulas.
    
    # Simple heuristic: if the formula contains the elements of a known family formula
    # This is tricky without a full periodic table check here.
    # Let's stick to the mapping provided. If the formula is exactly in mapping, use it.
    # Otherwise, return 'Unknown' for now, as T013 handles more complex logic.
    # But T011 needs to produce a file. Let's assume the mapping covers the target families.
    
    # Fallback: check if any key in mapping is a substring of the formula or vice versa
    for key, family in mapping.items():
        if family in TARGET_FAMILIES:
            # If the key is a substring of the formula (e.g. "Bi2Te" in "Bi2Te3")
            if key.lower() in formula.lower():
                return family
            # If the formula is a substring of the key (unlikely but possible)
            if formula.lower() in key.lower():
                return family
    
    return "Unknown"

def filter_records(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Filter records to retain only Bi-Te, Pb-Te, Skutterudites.
    Exclude records missing Seebeck or Composition (Formula).
    """
    # Ensure columns exist
    # The dataset might have 'Seebeck' or 'Seebeck_coefficient' or similar.
    # The prompt says "exclude missing Seebeck/Composition".
    # Let's look for common column names.
    seebeck_col = None
    formula_col = None
    
    cols_lower = {c.lower(): c for c in df.columns}
    
    # Identify Seebeck column
    for k in ['seebeck', 'seebeck_coefficient', 's', 's_u', 'seebeck_coeff']:
        if k in cols_lower:
            seebeck_col = cols_lower[k]
            break
    
    # Identify Formula column
    for k in ['formula', 'composition', 'comp', 'material']:
        if k in cols_lower:
            formula_col = cols_lower[k]
            break
    
    if not seebeck_col or not formula_col:
        # Fallback: assume first numeric column is seebeck, first string is formula?
        # Or raise error. Let's raise a clear error.
        raise ValueError(f"Could not identify Seebeck or Formula columns. Found: {list(df.columns)}")
    
    # Drop rows with missing Formula
    df = df.dropna(subset=[formula_col])
    
    # Drop rows with missing Seebeck
    df = df.dropna(subset=[seebeck_col])
    
    # Map family
    df['material_family'] = df.apply(lambda row: map_family(row, mapping), axis=1)
    
    # Filter for target families
    df = df[df['material_family'].isin(TARGET_FAMILIES)]
    
    return df

def log_retention(total_input: int, retained_count: int, status: str):
    """
    Log retention metrics to state/retention_log.json.
    """
    retention_rate = retained_count / total_input if total_input > 0 else 0.0
    
    log_entry = {
        "retention_rate": retention_rate,
        "total_input": total_input,
        "retained_count": retained_count,
        "status": status
    }
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log_path = STATE_DIR / "retention_log.json"
    
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    if retention_rate < 0.95:
        print(f"CRITICAL: Retention < 95% ({retention_rate:.2%})", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Retention check passed: {retention_rate:.2%}")

def main():
    """Main entry point for data ingestion and cleaning."""
    print("Starting data ingestion...")
    
    # 1. Fetch Data
    try:
        raw_csv = fetch_data(DATA_URL)
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 2. Parse Data
    try:
        df = parse_csv_data(raw_csv)
    except Exception as e:
        print(f"Error parsing data: {e}", file=sys.stderr)
        sys.exit(1)
    
    total_input = len(df)
    print(f"Loaded {total_input} records.")
    
    if total_input == 0:
        print("Error: No records found in dataset.", file=sys.stderr)
        sys.exit(1)
    
    # 3. Load Mapping
    try:
        mapping = load_family_mapping(str(MAPPING_PATH))
    except Exception as e:
        print(f"Error loading mapping: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 4. Clean and Filter
    # Clean records (strip, normalize NaN)
    # Apply cleaning function row-wise
    df = df.apply(clean_record, axis=1)
    
    # Filter records (target families, non-null seebeck/formula)
    try:
        filtered_df = filter_records(df, mapping)
    except Exception as e:
        print(f"Error filtering records: {e}", file=sys.stderr)
        sys.exit(1)
    
    retained_count = len(filtered_df)
    print(f"Filtered to {retained_count} records.")
    
    # 5. Log Retention
    # Determine status based on retention rate
    status = "PASS" if retained_count / total_input >= 0.95 else "FAIL"
    log_retention(total_input, retained_count, status)
    
    # 6. Save Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved cleaned data to {OUTPUT_PATH}")
    
    # Verify row count
    if len(filtered_df) <= 0:
        print("Error: Output file has 0 rows.", file=sys.stderr)
        sys.exit(1)
    
    print("Task T011 completed successfully.")

if __name__ == "__main__":
    main()
