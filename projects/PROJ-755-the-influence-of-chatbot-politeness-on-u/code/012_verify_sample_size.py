"""
T012: Sample Size Verification for Subgroups and Primary Analysis.

This script loads the raw HCI_P2 dataset (downloaded by T015), checks the total
sample size for primary analysis viability (n >= 100), and counts dialogues per
demographic subgroup (age, gender). It generates a validation report in JSON
format to gate downstream subgroup analyses (US3).

Dependencies:
- T015: Raw data must exist in data/raw/hci_p2/
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "hci_p2"
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "validation_report.json"
MIN_TOTAL_SAMPLE = 100
MIN_SUBGROUP_SAMPLE = 30

def find_raw_dataset() -> Optional[Path]:
    """Locate the raw dataset file in the expected directory."""
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DATA_DIR}")
        return None

    # Look for common dataset formats
    candidates = list(RAW_DATA_DIR.glob("*.parquet")) + list(RAW_DATA_DIR.glob("*.csv"))
    if not candidates:
        logger.error(f"No dataset file found in {RAW_DATA_DIR}")
        return None

    # Prefer the most recently modified or the first found
    dataset_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    logger.info(f"Found dataset: {dataset_path}")
    return dataset_path

def load_dataset(path: Path) -> pd.DataFrame:
    """Load the dataset based on its extension."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    elif path.suffix == ".csv":
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def verify_sample_sizes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform sample size verification.
    
    Returns a dictionary with the validation report schema.
    """
    report = {
        "status": "full",
        "total_sample_size": 0,
        "primary_analysis_valid": False,
        "missing_fields": [],
        "subgroup_counts": {},
        "subgroups_eligible": [],
        "subgroups_excluded": []
    }

    # Check total sample size
    total_n = len(df)
    report["total_sample_size"] = total_n
    
    if total_n < MIN_TOTAL_SAMPLE:
        report["status"] = "missing_demographics"
        report["primary_analysis_valid"] = False
        logger.error(f"STOP: Insufficient data for primary analysis. Total n={total_n} < {MIN_TOTAL_SAMPLE}")
        return report

    report["primary_analysis_valid"] = True
    logger.info(f"Primary analysis valid: Total n={total_n} >= {MIN_TOTAL_SAMPLE}")

    # Identify demographic columns
    potential_age_cols = [c for c in df.columns if "age" in c.lower()]
    potential_gender_cols = [c for c in df.columns if "gender" in c.lower() or "sex" in c.lower()]

    if not potential_age_cols and not potential_gender_cols:
        report["status"] = "missing_demographics"
        report["missing_fields"].extend(["age", "gender"])
        logger.warning("Demographic columns (age/gender) not found. Subgroup analysis will be skipped.")
        return report

    # Determine which columns to use (prefer specific names if available)
    age_col = potential_age_cols[0] if potential_age_cols else None
    gender_col = potential_gender_cols[0] if potential_gender_cols else None

    # Analyze Gender Subgroups
    if gender_col:
        if age_col and age_col in df.columns:
            # Check for missing values in the specific column
            valid_df = df.dropna(subset=[gender_col])
            gender_counts = valid_df[gender_col].value_counts().to_dict()
            report["subgroup_counts"].update({str(k): int(v) for k, v in gender_counts.items()})
            
            for group, count in gender_counts.items():
                if count >= MIN_SUBGROUP_SAMPLE:
                    report["subgroups_eligible"].append(str(group))
                else:
                    report["subgroups_excluded"].append(str(group))
        else:
            # Fallback if age column logic is complex, just count gender
            valid_df = df.dropna(subset=[gender_col])
            gender_counts = valid_df[gender_col].value_counts().to_dict()
            report["subgroup_counts"].update({str(k): int(v) for k, v in gender_counts.items()})
            for group, count in gender_counts.items():
                if count >= MIN_SUBGROUP_SAMPLE:
                    report["subgroups_eligible"].append(str(group))
                else:
                    report["subgroups_excluded"].append(str(group))

    # Analyze Age Subgroups
    if age_col:
        # Age might be continuous or binned. If continuous, we bin it or count unique values.
        # For simplicity in this gate, we treat unique age values as groups if they meet the count.
        # Or if it's already binned (e.g., "18-25"), we count those.
        valid_df = df.dropna(subset=[age_col])
        age_counts = valid_df[age_col].value_counts().to_dict()
        
        # Update counts (may overlap with gender keys if naming is weird, but schema expects distinct keys usually)
        # We'll prefix to avoid collision if needed, but standard practice is distinct keys.
        # Let's assume the key is the value itself.
        for group, count in age_counts.items():
            key = f"age_{str(group)}"
            report["subgroup_counts"][key] = int(count)
            if count >= MIN_SUBGROUP_SAMPLE:
                report["subgroups_eligible"].append(key)
            else:
                report["subgroups_excluded"].append(key)

    # Determine final status
    if not report["subgroups_eligible"]:
        report["status"] = "partial" if report["primary_analysis_valid"] else "missing_demographics"
        logger.warning("No subgroups met the minimum sample size (n >= 30). Subgroup analysis (US3) will be skipped.")
    else:
        logger.info(f"Subgroups eligible for analysis: {report['subgroups_eligible']}")
        logger.info(f"Subgroups excluded due to low n: {report['subgroups_excluded']}")

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Validation report saved to: {output_path}")

def main() -> int:
    """Main entry point."""
    logger.info("Starting T012: Sample Size Verification")
    
    dataset_path = find_raw_dataset()
    if not dataset_path:
        logger.error("Failed to locate raw dataset. Aborting.")
        return 1

    try:
        df = load_dataset(dataset_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return 1

    report = verify_sample_sizes(df)
    save_report(report, OUTPUT_FILE)

    # Exit with error code if primary analysis is invalid to halt pipeline
    if not report["primary_analysis_valid"]:
        logger.critical("Pipeline halted: Primary analysis sample size insufficient.")
        return 1

    logger.info("T012 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
