"""
T012: Verification Gate for Demographic Fields.

Validates the presence of critical fields (quality_rating, user_id, age, gender)
in the dataset to be used for analysis.

Logic:
1. Check for 'quality_rating' and 'user_id'. If missing, halt pipeline (Critical Error).
2. Check for 'age' and 'gender'. If missing, generate a 'partial' status report
   and log that US-3 (subgroup analysis) will be skipped, but allow US-1/US-2 to proceed.
3. If all present, generate a 'full' status report.

Output:
- data/raw/validation_report.json
"""
import json
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.schema_validator import get_missing_fields, load_schema, validate_dataset_schema

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_REPORT_PATH = DATA_RAW_DIR / "validation_report.json"

# Fields to check
CRITICAL_FIELDS = ["quality_rating", "user_id"]
OPTIONAL_DEMOGRAPHIC_FIELDS = ["age", "gender"]
ALL_REQUIRED_FIELDS = CRITICAL_FIELDS + OPTIONAL_DEMOGRAPHIC_FIELDS

def find_dataset_file(data_dir: Path) -> Optional[Path]:
    """
    Scans data/raw for the first available dataset file (parquet, csv, jsonl).
    In a real pipeline, this might be passed as an argument, but for the gate,
    we look for the merged dataset or the first available source.
    """
    extensions = [".parquet", ".csv", ".jsonl", ".json"]
    for ext in extensions:
        # Look for generic merged file or any data file if merged doesn't exist yet
        # Since T012 runs before download/scoring, we might be checking a raw source
        # or a placeholder. However, per spec, we check the "merged dataset".
        # If no merged dataset exists yet, we check if the *structure* of the 
        # expected input is valid, or if we are checking a raw source.
        # Given the task says "Validate... in the merged dataset", but T015 downloads it,
        # this task likely runs *after* a download step or checks the *schema* of the 
        # expected input. 
        # However, T012 is listed in Phase 2 (Foundational) and T015 in Phase 3.
        # This implies T012 might need to validate a *sample* or a *raw source* 
        # that is expected to exist, OR it validates the *schema definition* 
        # against the *expected* data structure.
        #
        # Re-reading T012: "Validate presence... in the merged dataset."
        # If T012 runs before T015 (Download), the merged dataset doesn't exist.
        # BUT, T012 is a "Verification Gate". It might be checking a *raw* source 
        # that is assumed to be present (e.g. a pre-downloaded HCI dataset) or 
        # it validates the *schema* to ensure that *if* we download, we know what to expect.
        #
        # Actually, looking at the task description: "This task MUST run before any download 
        # or scoring logic to prevent wasted effort."
        # This implies we are checking a *source* dataset that is ALREADY available or 
        # we are checking the *schema* of the *expected* data.
        #
        # However, the task says "in the merged dataset". If the merged dataset is not created yet,
        # we cannot validate it.
        # Let's assume the project has a `data/raw/` directory with some source data 
        # (perhaps from a previous run or a mounted volume) or we are validating 
        # the *schema* against a *sample* of the expected data.
        #
        # Given the constraint "Real data only", and T012 is before T015, 
        # it is highly likely that this task is meant to validate the *raw source* 
        # that will be merged, OR it is a placeholder to ensure the *schema* is correct.
        #
        # BUT, the prompt says: "If a task needs real external data... get it from a real source".
        # Since T012 is a gate, it likely checks the *first available* data source in `data/raw`.
        # If `data/raw` is empty, we cannot validate.
        #
        # Let's look for any data file in data/raw.
        for f in data_dir.iterdir():
            if f.is_file() and any(f.suffix == ext for ext in extensions):
                return f
    return None

def load_dataset(file_path: Path) -> pd.DataFrame:
    """Loads a dataset from various formats."""
    suffix = file_path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    elif suffix == ".csv":
        return pd.read_csv(file_path)
    elif suffix in [".jsonl", ".json"]:
        # Attempt to load JSON lines or list of dicts
        try:
            return pd.read_json(file_path, lines=True)
        except ValueError:
            return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def validate_fields(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the presence of required fields.
    Returns a report dictionary.
    """
    existing_columns = set(df.columns)
    
    missing_critical = [f for f in CRITICAL_FIELDS if f not in existing_columns]
    missing_demo = [f for f in OPTIONAL_DEMOGRAPHIC_FIELDS if f not in existing_columns]
    
    status = "full"
    message = "All required fields present."
    
    if missing_critical:
        status = "critical_failure"
        message = f"Critical fields missing: {missing_critical}. Pipeline halted."
    elif missing_demo:
        status = "partial"
        message = f"Demographic fields missing: {missing_demo}. US-3 (subgroup analysis) will be skipped."
    
    report = {
        "status": status,
        "message": message,
        "missing_critical_fields": missing_critical,
        "missing_demographic_fields": missing_demo,
        "available_fields": list(existing_columns),
        "row_count": len(df)
    }
    
    return report

def main():
    print("Starting T012: Demographic Verification Gate...")
    
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find dataset
    dataset_path = find_dataset_file(DATA_RAW_DIR)
    
    if not dataset_path:
        # If no dataset exists yet, we cannot validate.
        # However, the task implies we are checking the *merged* dataset.
        # If the merged dataset doesn't exist, we should check if we are 
        # in a state where we expect to download it later.
        # But the task says "Validate... in the merged dataset".
        # If it doesn't exist, we can't validate.
        # Let's assume for the sake of the pipeline that if no data exists,
        # we report a failure or a state where data is missing.
        #
        # Wait, T015 downloads data. T012 runs before T015.
        # This implies T012 might be checking a *raw source* that is expected to be there.
        # If `data/raw` is empty, we should report that.
        #
        # Let's create a report indicating no data found.
        report = {
            "status": "no_data",
            "message": "No dataset found in data/raw. Cannot validate fields.",
            "missing_critical_fields": ALL_REQUIRED_FIELDS,
            "missing_demographic_fields": ALL_REQUIRED_FIELDS,
            "available_fields": [],
            "row_count": 0
        }
        # Write report
        with open(OUTPUT_REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {OUTPUT_REPORT_PATH}")
        print("ERROR: No dataset found. Pipeline cannot proceed without data.")
        return 1
    
    print(f"Found dataset: {dataset_path}")
    
    try:
        df = load_dataset(dataset_path)
        print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
        print(f"Columns: {list(df.columns)}")
        
        report = validate_fields(df)
        
        # Write report
        with open(OUTPUT_REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report written to {OUTPUT_REPORT_PATH}")
        
        if report["status"] == "critical_failure":
            print("CRITICAL ERROR: Missing quality_rating or user_id. Halting pipeline.")
            return 1
        elif report["status"] == "partial":
            print("WARNING: Demographic fields missing. Proceeding with US-1 and US-2 only.")
            return 0
        elif report["status"] == "full":
            print("SUCCESS: All fields present. Proceeding with all user stories.")
            return 0
        else:
            print("INFO: No data to validate.")
            return 0
            
    except Exception as e:
        print(f"ERROR: Failed to load or validate dataset: {e}")
        report = {
            "status": "error",
            "message": str(e),
            "missing_critical_fields": [],
            "missing_demographic_fields": [],
            "available_fields": [],
            "row_count": 0
        }
        with open(OUTPUT_REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)
        return 1

if __name__ == "__main__":
    sys.exit(main())
