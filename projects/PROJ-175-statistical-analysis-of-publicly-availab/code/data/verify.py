"""
Data Verification Module.

Checks URL availability and schema of Recipe1M, FlavorDB, and Counterfactual datasets.
Validates that the data conforms to the expected schema defined in specs/001-statistical-analysis-of-recipe-data/contracts/.
"""
import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from io import StringIO

# Add parent to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# URLs for real data sources
RECIPE1M_URL = "https://huggingface.co/datasets/llmXive/recipe1m/resolve/main/recipe1m_processed.csv"
FLAVORDB_URL = "https://raw.githubusercontent.com/llmXive/flavordb/main/chemical_matrix.csv"
COUNTERFACTUAL_URL = "https://raw.githubusercontent.com/llmXive/counterfactual/main/labels.csv"

# Expected schema definitions (simplified for verification)
EXPECTED_SCHEMAS = {
    "Recipe1M": {
        "required_columns": ["recipe_id", "ingredients", "instructions"],
        "sample_size": 5
    },
    "FlavorDB": {
        "required_columns": ["ingredient_id", "chemical_vector"], # Vector might be stringified or JSON
        "sample_size": 5
    },
    "Counterfactual": {
        "required_columns": ["pair_id", "ingredient_a", "ingredient_b", "label"],
        "sample_size": 5
    }
}

def fetch_schema_sample(url: str, sample_size: int = 5) -> dict:
    """
    Fetches the first N rows of a CSV to verify schema.
    Returns a dict with 'columns' and 'sample_count'.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Read just the header and first few rows
        # We use StringIO to parse the text response without saving to disk
        text_data = response.text
        df = pd.read_csv(StringIO(text_data), nrows=sample_size)
        
        return {
            "columns": list(df.columns),
            "sample_count": len(df),
            "has_all_required": True
        }
    except Exception as e:
        return {
            "columns": [],
            "sample_count": 0,
            "has_all_required": False,
            "error": str(e)
        }

def verify_schema(name: str, url: str, schema_def: dict) -> bool:
    """
    Verifies that the data at the URL matches the expected schema.
    """
    required_cols = set(schema_def.get("required_columns", []))
    sample_size = schema_def.get("sample_size", 5)
    
    print(f"  Verifying schema for {name}...")
    result = fetch_schema_sample(url, sample_size)
    
    if result["sample_count"] == 0:
        print(f"    [FAIL] Could not fetch sample data: {result.get('error', 'Unknown error')}")
        return False
    
    found_cols = set(result["columns"])
    missing_cols = required_cols - found_cols
    
    if missing_cols:
        print(f"    [FAIL] Missing required columns: {missing_cols}")
        print(f"    Found columns: {found_cols}")
        return False
    
    print(f"    [OK] Schema valid. Found {len(found_cols)} columns, sample size {result['sample_count']}.")
    return True

def verify_data_sources():
    """
    Verify that all data sources are reachable and conform to expected schemas.
    Returns True if all checks pass, raises an error otherwise.
    """
    sources = [
        ("Recipe1M", RECIPE1M_URL, EXPECTED_SCHEMAS["Recipe1M"]),
        ("FlavorDB", FLAVORDB_URL, EXPECTED_SCHEMAS["FlavorDB"]),
        ("Counterfactual", COUNTERFACTUAL_URL, EXPECTED_SCHEMAS["Counterfactual"])
    ]
    
    all_ok = True
    for name, url, schema_def in sources:
        print(f"Verifying {name} availability and schema...")
        
        # Check availability first (HEAD request)
        try:
            head_response = requests.head(url, timeout=10)
            if head_response.status_code != 200:
                print(f"  [FAIL] {name} URL returned {head_response.status_code}")
                all_ok = False
                continue
            print(f"  [OK] {name} URL is accessible.")
        except Exception as e:
            print(f"  [FAIL] {name} connection error: {e}")
            all_ok = False
            continue
        
        # Check schema
        if not verify_schema(name, url, schema_def):
            all_ok = False
    
    if not all_ok:
        raise RuntimeError("One or more data sources are unavailable or do not match the expected schema.")
    
    print("\n[SUCCESS] All data sources verified successfully.")
    return True

if __name__ == "__main__":
    verify_data_sources()