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

def verify_counterfactual_label_schema(url: str) -> bool:
    """
    Strict schema validation for the Counterfactual dataset.
    Ensures the 'compatibility_label' column (or 'label' if mapped) contains
    only binary values (0/1) or valid float scores.
    
    Fails the pipeline (raises ValueError) if the schema deviates.
    
    Args:
        url: The URL of the Counterfactual dataset.
        
    Returns:
        True if validation passes.
        
    Raises:
        ValueError: If the column is missing or contains invalid values.
    """
    print("Verifying Counterfactual 'compatibility_label' schema (T042)...")
    
    try:
        # Fetch a sample to check column names and values
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        text_data = response.text
        
        # Load a larger sample to check value distribution, but not the whole file
        # Using nrows=10000 to ensure we have enough data to detect anomalies
        df_sample = pd.read_csv(StringIO(text_data), nrows=10000)
        
        # Determine the label column name (Task description says 'compatibility_label', 
        # but existing schema says 'label'. We check for both).
        label_col = None
        if "compatibility_label" in df_sample.columns:
            label_col = "compatibility_label"
        elif "label" in df_sample.columns:
            label_col = "label"
        
        if label_col is None:
            error_msg = f"Counterfactual dataset missing required label column. Expected 'compatibility_label' or 'label'. Found: {list(df_sample.columns)}"
            print(f"  [FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        print(f"  Found label column: '{label_col}'")
        
        # Check for valid values: 0, 1, or floats (e.g., 0.0, 1.0, 0.5)
        # We allow numeric types. If there are strings or other types, it fails.
        # We also check if the unique values are within a reasonable binary/score range.
        
        # Ensure column is numeric
        try:
            numeric_col = pd.to_numeric(df_sample[label_col], errors='raise')
        except (ValueError, TypeError) as e:
            error_msg = f"Column '{label_col}' contains non-numeric values. Error: {e}"
            print(f"  [FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        unique_vals = numeric_col.unique()
        
        # Define valid set: integers 0, 1 OR floats that are effectively 0.0 or 1.0
        # Or strictly numeric scores between 0 and 1 if it's a probability.
        # The task says "binary values (0/1) or valid float scores".
        # We assume valid scores are in [0, 1].
        
        invalid_vals = []
        for val in unique_vals:
            if not (0.0 <= val <= 1.0):
                invalid_vals.append(val)
        
        if invalid_vals:
            error_msg = f"Column '{label_col}' contains invalid values outside [0, 1]: {invalid_vals[:10]}..."
            print(f"  [FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        # Check if it's purely binary or has float scores
        is_binary = set(unique_vals).issubset({0.0, 1.0})
        if is_binary:
            print(f"  [OK] Column '{label_col}' contains valid binary values (0/1).")
        else:
            print(f"  [OK] Column '{label_col}' contains valid float scores in [0, 1]. Unique values: {sorted(unique_vals)[:10]}...")
        
        return True

    except requests.RequestException as e:
        error_msg = f"Failed to fetch Counterfactual data for schema validation: {e}"
        print(f"  [FAIL] {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        # Re-raise validation errors specifically
        if isinstance(e, ValueError):
            raise
        error_msg = f"Unexpected error during Counterfactual schema validation: {e}"
        print(f"  [FAIL] {error_msg}")
        raise ValueError(error_msg)

def verify_data_sources_with_label_check():
    """
    Extended verification that includes the strict label schema check for Counterfactual.
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
    
    # Specific check for Counterfactual label column (T042 requirement)
    if all_ok:
        try:
            verify_counterfactual_label_schema(COUNTERFACTUAL_URL)
        except ValueError as e:
            print(f"\n[CRITICAL] Counterfactual label schema validation failed: {e}")
            all_ok = False
    
    if not all_ok:
        raise RuntimeError("One or more data sources are unavailable, do not match the expected schema, or failed label validation.")
    
    print("\n[SUCCESS] All data sources and label schemas verified successfully.")
    return True

if __name__ == "__main__":
    verify_data_sources_with_label_check()