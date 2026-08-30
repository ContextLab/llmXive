"""
T012: Sample Size Verification for Subgroups and Primary Analysis.

This script loads the filtered datasets (produced by T019), verifies the completeness
of demographic fields (age, gender), counts dialogues per subgroup, and generates
a validation report (data/raw/validation_report.json) to gate User Story 3.

Logic:
1. Load filtered datasets from data/raw/filtered/ (or the merged file if T018 ran,
   but per T012 dependency it expects raw filtered files or a merged intermediate).
   Since T018 is not yet complete, we look for the individual filtered parquet files
   or a consolidated file if T019 produced one.
   Per T019 description: "Filtered raw datasets in data/raw/filtered/".
   We will attempt to load all parquet files in that directory and concatenate them.
2. Check completeness of 'age' and 'gender'.
3. Count dialogues per subgroup.
4. Apply gate logic:
   - If < 80% have demographics -> status 'missing_demographics', gate 'failed_80pct'.
   - If any subgroup < 30 -> exclude from US3 (log, do not halt primary).
5. Save report to data/raw/validation_report.json.
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_raw_dataset(base_dir: Path) -> Optional[Path]:
    """
    Locate the filtered dataset files.
    T019 saves to data/raw/filtered/. We expect parquet files there.
    If a single merged file exists (e.g., filtered_dialogues.parquet), use it.
    Otherwise, glob all .parquet files and concatenate.
    """
    filtered_dir = base_dir / "data" / "raw" / "filtered"
    if not filtered_dir.exists():
        logger.error(f"Filtered directory not found: {filtered_dir}")
        return None

    parquet_files = list(filtered_dir.glob("*.parquet"))
    if not parquet_files:
        logger.error(f"No parquet files found in {filtered_dir}")
        return None

    logger.info(f"Found {len(parquet_files)} parquet files in {filtered_dir}")
    return filtered_dir  # Return directory to load all

def load_dataset(directory: Path) -> pd.DataFrame:
    """
    Load all parquet files in the directory and concatenate them.
    Assumes each file contains dialogue-level data with columns:
    dialogue_id, quality_rating, user_id, age, gender, source_dataset, etc.
    """
    dfs = []
    for file_path in sorted(directory.glob("*.parquet")):
        logger.info(f"Loading {file_path.name}...")
        try:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    if not dfs:
        raise ValueError("No data loaded from filtered directory.")

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset shape: {combined_df.shape}")
    return combined_df

def verify_sample_sizes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify sample sizes and demographic completeness.

    Returns a dictionary matching the required schema:
    {
      "status": "full" | "partial" | "missing_demographics",
      "demographic_completeness_pct": float,
      "total_sample_size": int,
      "primary_analysis_valid": bool,
      "missing_fields": List[str],
      "subgroup_counts": Dict[str, int],
      "subgroups_eligible": List[str],
      "subgroups_excluded": List[str],
      "gate_status": "passed" | "failed_80pct"
    }
    """
    required_fields = ['age', 'gender', 'dialogue_id']
    missing_fields = []
    for field in required_fields:
        if field not in df.columns:
            missing_fields.append(field)

    if missing_fields:
        logger.warning(f"Missing required fields: {missing_fields}")
        # If critical fields are missing, we cannot compute stats.
        # Assume 0% completeness.
        return {
            "status": "missing_demographics",
            "demographic_completeness_pct": 0.0,
            "total_sample_size": len(df),
            "primary_analysis_valid": False,
            "missing_fields": missing_fields,
            "subgroup_counts": {},
            "subgroups_eligible": [],
            "subgroups_excluded": [],
            "gate_status": "failed_80pct"
        }

    # Check completeness of age and gender
    # We consider a row complete if BOTH age and gender are non-null
    complete_mask = df['age'].notna() & df['gender'].notna()
    total_rows = len(df)
    complete_rows = complete_mask.sum()
    completeness_pct = (complete_rows / total_rows * 100) if total_rows > 0 else 0.0

    logger.info(f"Demographic completeness: {completeness_pct:.2f}% ({complete_rows}/{total_rows})")

    # Gate Condition: < 80% completeness -> fail
    if completeness_pct < 80.0:
        status = "missing_demographics"
        gate_status = "failed_80pct"
        primary_valid = False
        logger.warning("CRITICAL: Demographic completeness < 80%. US3 will be blocked.")
    else:
        status = "full" if completeness_pct == 100.0 else "partial"
        gate_status = "passed"
        primary_valid = True
        logger.info("Demographic completeness >= 80%. Primary analysis valid.")

    # Analyze subgroups
    # Filter to complete rows for subgroup analysis
    df_complete = df[complete_mask].copy()

    subgroup_counts = {}
    subgroups_eligible = []
    subgroups_excluded = []

    # Count by gender
    if 'gender' in df_complete.columns:
        gender_counts = df_complete['gender'].value_counts().to_dict()
        # Normalize keys to lowercase for consistency if needed, but keep original for now
        for gender, count in gender_counts.items():
            key = str(gender).lower() if isinstance(gender, str) else str(gender)
            subgroup_counts[f"gender_{key}"] = count
            if count >= 30:
                subgroups_eligible.append(f"gender_{key}")
            else:
                subgroups_excluded.append(f"gender_{key}")
                logger.warning(f"Subgroup {key} has n={count} (< 30). Excluded from US3.")

    # Count by age groups
    # Define age bins: 18-25, 26-35, 36-45, 46-55, 56+
    # This is a heuristic; adjust if specific bins are defined elsewhere.
    if 'age' in df_complete.columns:
        # Create age group column
        def categorize_age(age):
            if pd.isna(age):
                return None
            age = int(age)
            if 18 <= age <= 25:
                return "age_18_25"
            elif 26 <= age <= 35:
                return "age_26_35"
            elif 36 <= age <= 45:
                return "age_36_45"
            elif 46 <= age <= 55:
                return "age_46_55"
            else:
                return "age_56_plus"

        df_complete['age_group'] = df_complete['age'].apply(categorize_age)
        age_group_counts = df_complete['age_group'].value_counts().to_dict()

        for group, count in age_group_counts.items():
            subgroup_counts[group] = count
            if count >= 30:
                subgroups_eligible.append(group)
            else:
                subgroups_excluded.append(group)
                logger.warning(f"Subgroup {group} has n={count} (< 30). Excluded from US3.")

    result = {
        "status": status,
        "demographic_completeness_pct": round(completeness_pct, 2),
        "total_sample_size": total_rows,
        "primary_analysis_valid": primary_valid,
        "missing_fields": missing_fields,
        "subgroup_counts": subgroup_counts,
        "subgroups_eligible": subgroups_eligible,
        "subgroups_excluded": subgroups_excluded,
        "gate_status": gate_status
    }

    return result

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main() -> int:
    """
    Main entry point for T012.
    """
    project_root = Path.cwd()
    logger.info(f"Project root: {project_root}")

    # 1. Find dataset
    dataset_dir = find_raw_dataset(project_root)
    if not dataset_dir:
        logger.error("Could not locate filtered dataset files. Aborting.")
        return 1

    # 2. Load dataset
    try:
        df = load_dataset(dataset_dir)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return 1

    # 3. Verify sample sizes
    report = verify_sample_sizes(df)

    # 4. Save report
    output_path = project_root / "data" / "raw" / "validation_report.json"
    save_report(report, output_path)

    # 5. Print summary
    print("\n--- T012 Verification Summary ---")
    print(f"Status: {report['status']}")
    print(f"Completeness: {report['demographic_completeness_pct']}%")
    print(f"Total Sample: {report['total_sample_size']}")
    print(f"Primary Analysis Valid: {report['primary_analysis_valid']}")
    print(f"Gate Status: {report['gate_status']}")
    print(f"Eligible Subgroups: {report['subgroups_eligible']}")
    print(f"Excluded Subgroups: {report['subgroups_excluded']}")
    print("---------------------------------\n")

    if report['gate_status'] == "failed_80pct":
        logger.critical("Gate failed: Demographic completeness < 80%. US3 blocked.")
        return 2 # Non-zero exit for gate failure
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
