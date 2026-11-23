"""
T012: Verification Gate for Demographic Fields.
Validates the presence of required fields (quality_rating, user_id, age, gender)
in the merged dataset (or primary HCI_P2 source).
"""
import json
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.schema_validator import get_missing_fields, load_schema, validate_dataset_schema

def find_dataset_file() -> Optional[Path]:
    """
    Locate the processed scored dialogues or merged dataset.
    Priority:
    1. data/processed/scored_dialogues.parquet (Primary HCI_P2 output)
    2. data/processed/merged_dialogues.parquet (Fallback merged output)
    """
    candidates = [
        Path("data/processed/scored_dialogues.parquet"),
        Path("data/processed/merged_dialogues.parquet")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load the dataset from parquet.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    try:
        df = pd.read_parquet(file_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {file_path}: {e}")

def validate_fields(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate presence of required fields:
    - Critical (must exist): quality_rating, user_id
    - Optional (for US3): age, gender
    
    Returns a report dict with status and missing fields.
    """
    required_critical = ['quality_rating', 'user_id']
    required_optional = ['age', 'gender']
    
    columns = set(df.columns)
    
    missing_critical = [f for f in required_critical if f not in columns]
    missing_optional = [f for f in required_optional if f not in columns]
    
    report = {
        "total_rows": len(df),
        "columns_found": list(columns),
        "missing_critical": missing_critical,
        "missing_optional": missing_optional,
        "status": "unknown"
    }
    
    if missing_critical:
        report["status"] = "critical_failure"
    elif missing_optional:
        report["status"] = "partial"
    else:
        report["status"] = "full"
        
    return report

def main():
    """
    Main execution for T012.
    1. Find dataset.
    2. Validate fields.
    3. If critical missing -> Log error, exit 1.
    4. If partial -> Write validation_report.json with status: partial.
    5. If full -> Write validation_report.json with status: full.
    """
    print("T012: Starting Demographic Verification Gate...")
    
    # 1. Locate dataset
    dataset_path = find_dataset_file()
    if not dataset_path:
        print("CRITICAL: No processed dataset found (scored_dialogues.parquet or merged_dialogues.parquet).")
        print("This task cannot run before US1 (Download/Score) or US1-merge logic.")
        # We exit 1 because the gate cannot pass without data.
        sys.exit(1)
    
    print(f"Found dataset: {dataset_path}")
    
    # 2. Load
    try:
        df = load_dataset(dataset_path)
    except Exception as e:
        print(f"CRITICAL: Failed to load dataset: {e}")
        sys.exit(1)
    
    # 3. Validate
    report = validate_fields(df)
    
    output_path = Path("data/raw/validation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 4. Logic based on report
    if report["status"] == "critical_failure":
        print(f"CRITICAL ERROR: Missing required fields: {report['missing_critical']}")
        print("The pipeline cannot proceed to US1/US2/US3 without these fields.")
        # Write report for audit trail even on failure
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    elif report["status"] == "partial":
        print(f"WARNING: Partial data. Missing optional fields: {report['missing_optional']}")
        print("Proceeding with US1 and US2. US3 (Subgroup Analysis) will be skipped per FR-006.")
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Validation report written to {output_path}")
        # Exit 0, but log the skip condition for downstream tasks
        
    elif report["status"] == "full":
        print("SUCCESS: All required fields (quality_rating, user_id, age, gender) present.")
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Validation report written to {output_path}")
    
    else:
        # Should not happen
        print(f"UNKNOWN STATUS: {report['status']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
