import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats

from logging_config import get_logger, raise_on_missing_data
from hygiene import update_artifact_hash, load_artifact_hashes, save_artifact_hashes
from seed import set_seed, ensure_seed_set
from config.loader import load_schema_map

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

# Constants for required columns based on T006/T011 logic
REQUIRED_PREDICTORS = [
    'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
    'hardness', 'elastic_modulus'
]
OPTIONAL_NORMALIZATION_INPUTS = ['contact_load', 'sliding_speed']
TARGET_COLUMNS = REQUIRED_PREDICTORS + OPTIONAL_NORMALIZATION_INPUTS + ['wear_rate', 'density', 'geometry', 'normalization_method']


def load_clean_data(input_path: str) -> pd.DataFrame:
    """Load the aggregated raw data after schema mapping and missing predictor handling."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T010/T011/T012 first.")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df


def flag_raw_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement T013d: Flag records with missing contact_load/sliding_speed as 'raw'.
    
    Logic:
    1. Records missing any of REQUIRED_PREDICTORS should have already been dropped (T012).
    2. Check for OPTIONAL_NORMALIZATION_INPUTS (contact_load, sliding_speed).
    3. If EITHER is missing (NaN), set normalization_method='raw'.
    4. If BOTH are present, set normalization_method='normalized'.
    5. Ensure the column exists and contains only 'raw' or 'normalized'.
    
    FR-013: Physically separate raw from normalized for primary training.
    This function tags them; T014 will perform the physical split.
    """
    logger.info("Starting flag_raw_records...")
    
    # Ensure columns exist
    missing_cols = [col for col in OPTIONAL_NORMALIZATION_INPUTS if col not in df.columns]
    if missing_cols:
        # If columns are missing entirely, treat all as raw (cannot normalize)
        logger.warning(f"Columns {missing_cols} missing. Treating all records as 'raw'.")
        df['normalization_method'] = 'raw'
        return df

    # Determine status row by row
    # A record is 'normalized' ONLY if both contact_load AND sliding_speed are NOT null
    # Otherwise it is 'raw'
    def classify_row(row):
        has_load = pd.notna(row['contact_load'])
        has_speed = pd.notna(row['sliding_speed'])
        if has_load and has_speed:
            return 'normalized'
        else:
            return 'raw'

    df['normalization_method'] = df.apply(classify_row, axis=1)
    
    # Verification
    counts = df['normalization_method'].value_counts()
    logger.info(f"Flagging complete. Counts: {counts.to_dict()}")
    
    if 'normalized' not in counts.index and len(df) > 0:
        logger.warning("No records found with 'normalized' status. All data will be in 'raw' subset.")
    
    return df


def run_statistical_validity_check(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Implement T017d: Perform Shapiro-Wilk (normality) and Levene's (homogeneity) tests 
    on the 'raw' subset of the data.
    
    Logic (FR-017):
    1. Load the clean data (aggregated_clean.csv) which contains the 'normalization_method' flag.
    2. Filter for records where 'normalization_method' == 'raw'.
    3. If the 'raw' subset is empty or has < 3 records, report 'raw_subset_invalid' due to insufficient data.
    4. Select numeric predictor columns for testing. We use 'power', 'scanning_speed', 'hardness' as representative
       continuous predictors for the normality test. For Levene's, we need a grouping variable; we use 'pattern_geometry'
       as the group.
    5. Shapiro-Wilk Test: Test if the distribution of numeric predictors is normal.
       - We test each continuous predictor. If ANY fails (p < 0.05), normality is rejected.
    6. Levene's Test: Test for homogeneity of variance across groups (pattern_geometry).
       - We test the variance of a target-like variable (e.g., 'wear_rate' if present, or a proxy) across groups.
       - If p < 0.05, homogeneity is rejected.
    7. If EITHER test fails (p < 0.05), set 'validity_status' to 'raw_subset_invalid'.
    8. Otherwise, set 'validity_status' to 'valid'.
    9. Output JSON report to `output_path`.
    
    Returns:
        Dict containing the report data.
    """
    logger.info(f"Starting statistical validity check on {input_path}...")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T013d first.")
    
    df = pd.read_csv(input_path)
    
    # Filter for raw subset
    raw_df = df[df['normalization_method'] == 'raw'].copy()
    
    report = {
        "subset": "raw",
        "total_raw_records": len(raw_df),
        "tests_performed": [],
        "validity_status": "unknown"
    }
    
    if len(raw_df) < 3:
        logger.warning("Raw subset has fewer than 3 records. Cannot perform statistical tests.")
        report["validity_status"] = "raw_subset_invalid"
        report["reason"] = "insufficient_data"
        report["message"] = f"Raw subset has only {len(raw_df)} records. Minimum 3 required for Shapiro-Wilk."
        
        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved validity report to {output_path}")
        return report
    
    # Select numeric columns for Shapiro-Wilk
    numeric_cols = raw_df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude non-predictor columns like 'wear_rate' if we are testing predictors, 
    # but the spec says "on the 'raw' subset". Let's test a representative set of continuous predictors.
    # We'll test 'power', 'scanning_speed', 'hardness' if they exist.
    test_cols = [col for col in ['power', 'scanning_speed', 'hardness', 'elastic_modulus'] if col in numeric_cols]
    
    if not test_cols:
        logger.warning("No suitable continuous predictor columns found for Shapiro-Wilk test.")
        report["validity_status"] = "raw_subset_invalid"
        report["reason"] = "no_testable_columns"
        report["message"] = "No continuous predictor columns found."
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved validity report to {output_path}")
        return report
    
    shapiro_results = {}
    shapiro_failed = False
    
    for col in test_cols:
        # Drop NaNs for this column
        col_data = raw_df[col].dropna()
        if len(col_data) < 3:
            logger.warning(f"Not enough data for Shapiro-Wilk on column {col}.")
            continue
        
        try:
            stat, p_value = stats.shapiro(col_data)
            shapiro_results[col] = {"statistic": float(stat), "p_value": float(p_value), "passed": p_value >= 0.05}
            report["tests_performed"].append({
                "test": "Shapiro-Wilk",
                "column": col,
                "statistic": float(stat),
                "p_value": float(p_value),
                "passed": p_value >= 0.05
            })
            if p_value < 0.05:
                shapiro_failed = True
        except Exception as e:
            logger.warning(f"Shapiro-Wilk test failed for {col}: {e}")
            shapiro_results[col] = {"error": str(e)}
    
    # Levene's Test for homogeneity of variance
    # We need a numeric dependent variable and a categorical grouping variable.
    # Group by 'pattern_geometry' (if it exists and is categorical/string)
    # Dependent variable: 'wear_rate' (if exists) or 'hardness' as proxy
    levene_results = []
    levene_failed = False
    
    group_col = 'pattern_geometry'
    dependent_var = 'wear_rate' if 'wear_rate' in raw_df.columns else ('hardness' if 'hardness' in raw_df.columns else None)
    
    if group_col in raw_df.columns and dependent_var:
        groups = raw_df[group_col].unique()
        if len(groups) >= 2:
            # Prepare data for Levene's test
            group_data = [raw_df[raw_df[group_col] == g][dependent_var].dropna() for g in groups]
            # Filter out empty groups
            group_data = [g for g in group_data if len(g) >= 2]
            
            if len(group_data) >= 2:
                try:
                    stat, p_value = stats.levene(*group_data)
                    levene_results.append({
                        "test": "Levene's",
                        "dependent_variable": dependent_var,
                        "grouping_variable": group_col,
                        "groups": list(groups),
                        "statistic": float(stat),
                        "p_value": float(p_value),
                        "passed": p_value >= 0.05
                    })
                    report["tests_performed"].append(levene_results[-1])
                    if p_value < 0.05:
                        levene_failed = True
                except Exception as e:
                    logger.warning(f"Levene's test failed: {e}")
                    report["tests_performed"].append({
                        "test": "Levene's",
                        "error": str(e)
                    })
            else:
                logger.warning("Not enough groups with sufficient data for Levene's test.")
        else:
            logger.warning("Not enough unique groups for Levene's test.")
    else:
        logger.warning(f"Missing required columns for Levene's test: group='{group_col}', dep='{dependent_var}'")
    
    # Determine overall validity
    # FR-017: if p < 0.05 for either, exclude 'raw' subset from sensitivity analysis and report `raw_subset_invalid`
    if shapiro_failed or levene_failed:
        report["validity_status"] = "raw_subset_invalid"
        report["message"] = "Normality or homogeneity assumption violated (p < 0.05)."
        if shapiro_failed:
            report["message"] += " Shapiro-Wilk test failed."
        if levene_failed:
            report["message"] += " Levene's test failed."
    else:
        report["validity_status"] = "valid"
        report["message"] = "Raw subset passed statistical validity checks."
    
    # Save report
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistical validity check complete. Status: {report['validity_status']}")
    logger.info(f"Saved report to {output_path}")
    
    return report


def main():
    """
    Main entry point for T017d.
    1. Load the clean data (output of T013d).
    2. Run statistical validity check on the 'raw' subset.
    3. Save the report to reports/raw_subset_validity.json.
    """
    ensure_seed_set()
    
    input_path = Path("data/processed/aggregated_clean.csv")
    output_path = Path("reports/raw_subset_validity.json")
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file {input_path} not found. "
            "Please ensure T013d (flag_raw_records) has completed successfully."
        )
    
    try:
        result = run_statistical_validity_check(str(input_path), str(output_path))
        
        # Update artifact hashes if needed (though this is a report, not a data artifact)
        # We can register the report hash if desired, but hygiene usually tracks data/models.
        # For now, we just ensure the file exists.
        
        logger.info("T017d completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in T017d: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()