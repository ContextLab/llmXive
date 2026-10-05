"""
Task T009: Verify Unified Dataset
Verifies that data/processed/reef_species_unified.csv exists, has the correct schema,
and contains no nulls in critical fields.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to path if necessary (though typically run from root)
project_root = Path(__file__).parent.parent
data_path = project_root / "data" / "processed" / "reef_species_unified.csv"
output_status_path = project_root / "data" / "processed" / "t009_verification_status.json"

REQUIRED_COLUMNS = [
    "reef_id",
    "species_id",
    "SST",
    "DHW",
    "thermal_tolerance",
    "bleaching_label",
    "trait_missing_flag"
]

CRITICAL_COLUMNS = ["SST", "DHW", "thermal_tolerance", "bleaching_label"]

def verify_dataset():
    """
    Verifies the unified dataset exists and meets schema/null constraints.
    Returns a dictionary with verification results.
    """
    result = {
        "task_id": "T009",
        "status": "pending",
        "message": "",
        "file_exists": False,
        "row_count": 0,
        "column_check": {},
        "null_check": {}
    }

    if not data_path.exists():
        result["status"] = "failed"
        result["message"] = f"File not found: {data_path}"
        return result

    result["file_exists"] = True

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        result["status"] = "failed"
        result["message"] = f"Failed to read CSV: {str(e)}"
        return result

    result["row_count"] = len(df)

    # Check columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        result["status"] = "failed"
        result["message"] = f"Missing required columns: {missing_cols}"
        result["column_check"] = {
            "required": REQUIRED_COLUMNS,
            "present": list(df.columns),
            "missing": missing_cols
        }
        return result

    result["column_check"] = {
        "required": REQUIRED_COLUMNS,
        "present": list(df.columns),
        "missing": []
    }

    # Check nulls in critical columns
    null_counts = {}
    has_nulls = False
    for col in CRITICAL_COLUMNS:
        count = df[col].isna().sum()
        null_counts[col] = int(count)
        if count > 0:
            has_nulls = True

    result["null_check"] = null_counts

    if has_nulls:
        result["status"] = "failed"
        result["message"] = f"Critical columns contain null values: {null_counts}"
    else:
        result["status"] = "passed"
        result["message"] = "Verification successful: Schema correct and no nulls in critical fields."

    return result

def main():
    print(f"Verifying unified dataset at: {data_path}")
    result = verify_dataset()

    # Ensure output directory exists
    output_status_path.parent.mkdir(parents=True, exist_ok=True)

    # Save verification status
    with open(output_status_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))

    if result["status"] == "failed":
        print("Verification FAILED.")
        sys.exit(1)
    else:
        print("Verification PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
