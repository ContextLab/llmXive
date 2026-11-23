import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def find_raw_dataset() -> Path:
    """
    Locate the merged dataset file.
    Expected path: data/processed/merged_dialogues.parquet
    """
    base_path = Path.cwd()
    candidate = base_path / "data" / "processed" / "merged_dialogues.parquet"
    
    if not candidate.exists():
        # Try relative to script location if running from code/
        script_dir = Path(__file__).resolve().parent.parent
        candidate = script_dir / "data" / "processed" / "merged_dialogues.parquet"
    
    if not candidate.exists():
        raise FileNotFoundError(
            f"Could not find merged dataset at {candidate}. "
            "Ensure T018 (Merge) has been completed successfully."
        )
    
    logger.info(f"Found merged dataset at: {candidate}")
    return candidate

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load the parquet dataset.
    """
    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def verify_sample_sizes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify sample sizes for subgroups and primary analysis.
    
    Logic:
    1. Check Completeness: Verify >= 80% of dialogues have 'age' and 'gender'.
    2. Check Subgroups: Count dialogues per age and gender group.
    3. Gate Condition: If any subgroup (e.g., Male, Female, Age 18-25) has n < 30,
       mark it as excluded but do not halt the main analysis.
    
    Returns:
        Dict containing the validation report structure.
    """
    report = {
        "status": "full",
        "demographic_completeness_pct": 0.0,
        "total_sample_size": len(df),
        "primary_analysis_valid": True,
        "missing_fields": [],
        "subgroup_counts": {},
        "subgroups_eligible": [],
        "subgroups_excluded": [],
        "gate_status": "passed"
    }

    # 1. Check Completeness
    # We need both 'age' and 'gender' to be present (non-null)
    required_fields = ['age', 'gender']
    missing_fields = []
    
    for field in required_fields:
        if field not in df.columns:
            missing_fields.append(field)
            logger.warning(f"Column '{field}' is missing from the dataset.")
    
    if missing_fields:
        report["missing_fields"] = missing_fields
        report["status"] = "missing_demographics"
        report["gate_status"] = "failed_80pct"
        report["primary_analysis_valid"] = False
        return report

    # Calculate completeness
    # A row is complete if it has non-null values for BOTH age and gender
    complete_mask = df['age'].notna() & df['gender'].notna()
    completeness_count = complete_mask.sum()
    total_count = len(df)
    completeness_pct = (completeness_count / total_count * 100) if total_count > 0 else 0.0
    
    report["demographic_completeness_pct"] = round(completeness_pct, 2)

    if completeness_pct < 80.0:
        logger.critical(f"Demographic completeness ({completeness_pct:.2f}%) is below 80% threshold.")
        report["status"] = "partial" # Or missing_demographics if we want to be strict
        report["gate_status"] = "failed_80pct"
        report["primary_analysis_valid"] = False
        # Even if failed, we can still report counts for debugging
    else:
        logger.info(f"Demographic completeness ({completeness_pct:.2f}%) meets 80% threshold.")

    # 2. Check Subgroups
    # Filter to only complete rows for subgroup analysis to ensure accuracy
    df_complete = df[complete_mask]

    # Analyze Gender
    if 'gender' in df_complete.columns:
        gender_counts = df_complete['gender'].value_counts().to_dict()
        # Normalize keys to string to ensure JSON compatibility
        report["subgroup_counts"]["gender"] = {str(k): int(v) for k, v in gender_counts.items()}
        
        for group, count in gender_counts.items():
            if count >= 30:
                report["subgroups_eligible"].append(f"gender_{group}")
            else:
                report["subgroups_excluded"].append(f"gender_{group}")
                logger.warning(f"Subgroup 'gender_{group}' has n={count} < 30. Excluded from subgroup analysis.")

    # Analyze Age (Binning logic)
    # Assuming 'age' is numeric. We'll create standard bins: 18-25, 26-35, 36-45, 46-55, 55+
    # If 'age' is already binned (string), we just count unique values.
    if 'age' in df_complete.columns:
        age_series = df_complete['age']
        # Check if age is numeric
        if pd.api.types.is_numeric_dtype(age_series):
            # Define bins
            bins = [18, 25, 35, 45, 55, 100]
            labels = ['18-25', '26-35', '36-45', '46-55', '55+']
            
            # Filter out ages < 18 if any
            df_valid_age = df_complete[df_complete['age'] >= 18]
            
            if len(df_valid_age) > 0:
                try:
                    age_binned = pd.cut(df_valid_age['age'], bins=bins, labels=labels, right=True)
                    age_counts = age_binned.value_counts().sort_index().to_dict()
                    # Convert to serializable format
                    report["subgroup_counts"]["age"] = {str(k): int(v) for k, v in age_counts.items()}
                    
                    for group, count in age_counts.items():
                        if count >= 30:
                            report["subgroups_eligible"].append(f"age_{group}")
                        else:
                            report["subgroups_excluded"].append(f"age_{group}")
                            logger.warning(f"Subgroup 'age_{group}' has n={count} < 30. Excluded from subgroup analysis.")
                except Exception as e:
                    logger.error(f"Failed to bin age data: {e}")
                    report["subgroup_counts"]["age"] = {}
            else:
                logger.warning("No valid ages >= 18 found.")
                report["subgroup_counts"]["age"] = {}
        else:
            # Assume it's already binned or categorical
            age_counts = age_series.value_counts().to_dict()
            report["subgroup_counts"]["age"] = {str(k): int(v) for k, v in age_counts.items()}
            for group, count in age_counts.items():
                if count >= 30:
                    report["subgroups_eligible"].append(f"age_{group}")
                else:
                    report["subgroups_excluded"].append(f"age_{group}")

    # Determine Final Gate Status for US3
    # The gate fails if < 80% completeness.
    # Subgroup exclusions do NOT fail the main analysis, only the specific subgroup tests.
    if report["gate_status"] != "failed_80pct":
        report["gate_status"] = "passed"
        logger.info("Sample size verification PASSED for primary analysis.")
    else:
        logger.error("Sample size verification FAILED (<80% completeness). US3 subgroup analysis cannot proceed reliably.")

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to: {output_path}")

def main() -> int:
    """
    Main entry point for T012.
    """
    try:
        # 1. Find and Load Data
        data_path = find_raw_dataset()
        df = load_dataset(data_path)

        # 2. Verify Sample Sizes
        report = verify_sample_sizes(df)

        # 3. Save Report
        output_path = Path.cwd() / "data" / "processed" / "validation_report.json"
        # Fallback if running from code/
        if not output_path.exists():
            script_dir = Path(__file__).resolve().parent.parent
            output_path = script_dir / "data" / "processed" / "validation_report.json"
        
        save_report(report, output_path)

        # 4. Exit with appropriate code
        if report["gate_status"] == "failed_80pct":
            logger.warning("Gate Failed: US3 may be blocked.")
            return 0 # Still return 0 as the script ran successfully, just flagged a condition
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
