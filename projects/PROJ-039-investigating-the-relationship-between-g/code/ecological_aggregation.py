import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config import get_project_root
from logging_config import get_analysis_logger, log_structured_event, save_analysis_results

# Configure logging
logger = get_analysis_logger("ecological_aggregation")

def load_microbiome_data(filepath: Path) -> pd.DataFrame:
    """Load the preprocessed microbiome features CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Microbiome features file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure numeric columns are float
    numeric_cols = ['age', 'bmi', 'alpha_power']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def load_eeg_data(filepath: Path) -> pd.DataFrame:
    """Load the preprocessed EEG features CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"EEG features file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure numeric columns are float
    numeric_cols = ['age', 'bmi', 'alpha_power']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def handle_missing_demographics(df: pd.DataFrame, cohort_name: str) -> Tuple[pd.DataFrame, int]:
    """
    Handle missing Age, Sex, BMI, Diet.
    Strategy: Exclude rows where Sex or BMI are missing (critical for binning).
    For Age, if missing, exclude (cannot bin).
    For Diet, if missing, exclude (cannot bin by diet).
    If a row is excluded, it is dropped.
    Returns the cleaned dataframe and the count of excluded rows.
    """
    required_cols = ['age', 'sex', 'bmi', 'diet']
    missing_mask = pd.Series([False] * len(df), index=df.index)
    
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Required column '{col}' missing in {cohort_name} data.")
            raise ValueError(f"Missing required column: {col}")
        
        # Check for NaN in required columns
        missing_mask |= df[col].isna()
    
    excluded_count = missing_mask.sum()
    if excluded_count > 0:
        logger.warning(f"{cohort_name}: Excluding {excluded_count} subjects due to missing demographics (Age, Sex, BMI, or Diet).")
        df_clean = df[~missing_mask].reset_index(drop=True)
    else:
        df_clean = df
    
    return df_clean, excluded_count

def create_strata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign stratum IDs based on exact binning rules:
    Age: [20, 30), [30, 40), [40, 50), [50, 60), [60, 70), [70, 100]
    Sex: M, F
    BMI: <25, [25, 30), >=30
    Diet: Vegan, Vegetarian, Omnivore, Other
    """
    def bin_age(age):
        if age < 20 or age >= 100: return None
        if age < 30: return "20-30"
        if age < 40: return "30-40"
        if age < 50: return "40-50"
        if age < 60: return "50-60"
        if age < 70: return "60-70"
        return "70-100"

    def bin_bmi(bmi):
        if bmi < 25: return "<25"
        if bmi < 30: return "25-30"
        return ">=30"

    df = df.copy()
    df['age_bin'] = df['age'].apply(bin_age)
    df['bmi_bin'] = df['bmi'].apply(bin_bmi)
    
    # Normalize Sex and Diet to strings and strip whitespace
    df['sex'] = df['sex'].astype(str).str.strip().str.upper()
    df['diet'] = df['diet'].astype(str).str.strip().str.title() # Capitalize for consistency

    # Filter out any rows that didn't bin correctly (e.g. age < 20)
    valid_strata_mask = df['age_bin'].notna() & df['bmi_bin'].notna()
    df = df[valid_strata_mask].reset_index(drop=True)

    # Create unique stratum ID
    df['stratum_id'] = df['age_bin'].astype(str) + '_' + df['sex'] + '_' + df['bmi_bin'].astype(str) + '_' + df['diet'].astype(str)
    
    return df

def aggregate_strata(microbiome_df: pd.DataFrame, eeg_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate data into strata.
    Requirement: Identify groups with >=5 subjects in BOTH cohorts.
    Output: raw_stratum_agg.csv and strata_report.json.
    Exit logic: If valid_strata_count < 5, exit with code 1.
    """
    
    # Process Microbiome
    logger.info("Processing Microbiome data for aggregation...")
    mg_clean, m_excl = handle_missing_demographics(microbiome_df, "Microbiome")
    mg_stratified = create_strata(mg_clean)
    
    # Count subjects per stratum in Microbiome
    mg_counts = mg_stratified.groupby('stratum_id').size().to_dict()
    mg_subjects = mg_stratified.groupby('stratum_id').agg({
        'alpha_power': 'mean',
        'age': 'mean',
        'bmi': 'mean',
        'sex': 'first',
        'diet': 'first'
    }).reset_index()
    mg_subjects['n_mg'] = mg_subjects['stratum_id'].map(mg_counts)

    # Process EEG
    logger.info("Processing EEG data for aggregation...")
    eeg_clean, e_excl = handle_missing_demographics(eeg_df, "EEG")
    eeg_stratified = create_strata(eeg_clean)
    
    # Count subjects per stratum in EEG
    eeg_counts = eeg_stratified.groupby('stratum_id').size().to_dict()
    eeg_subjects = eeg_stratified.groupby('stratum_id').agg({
        'alpha_power': 'mean',
        'age': 'mean',
        'bmi': 'mean',
        'sex': 'first',
        'diet': 'first'
    }).reset_index()
    eeg_subjects['n_eeg'] = eeg_subjects['stratum_id'].map(eeg_counts)

    # Merge counts to find common strata
    all_strata = set(mg_counts.keys()) & set(eeg_counts.keys())
    
    # Filter for strata with >=5 in BOTH
    valid_strata_ids = [s for s in all_strata if mg_counts.get(s, 0) >= 5 and eeg_counts.get(s, 0) >= 5]
    
    logger.info(f"Found {len(valid_strata_ids)} valid strata (>=5 subjects in both cohorts).")
    
    if len(valid_strata_ids) < 5:
        logger.error(f"Insufficient valid strata (<5) for ecological analysis. Found: {len(valid_strata_ids)}. Exiting.")
        log_structured_event("ERROR", "Insufficient strata", {"count": len(valid_strata_ids), "threshold": 5})
        save_analysis_results({"valid_strata_count": len(valid_strata_ids), "status": "failed", "reason": "Insufficient strata"})
        sys.exit(1)

    # Construct the final aggregation dataframe
    # We combine the means from both cohorts? Or just list them?
    # The task says: "Output: Write data/processed/raw_stratum_agg.csv"
    # Let's create a unified view. Since we need to compute means later (T015),
    # we might want to keep the individual subject data or just the stratum stats.
    # T015 says "Load data/processed/raw_stratum_agg.csv" and "Compute Means".
    # This implies raw_stratum_agg.csv might contain the raw subject data mapped to strata,
    # OR the stratum-level stats. Given T015 computes means, raw_stratum_agg likely holds
    # the subject-level data with stratum IDs, OR the intermediate stratum stats from each cohort.
    # However, T015 says "Compute mean alpha power per stratum". If we already aggregated in T014,
    # T015 would just read the mean.
    # Let's interpret "raw_stratum_agg" as the combined subject-level data with stratum IDs assigned,
    # filtered to valid strata. This allows T015 to compute the final means across both cohorts if needed,
    # or just read the pre-aggregated means if we assume they are the same.
    # Actually, T015 says "Load raw_stratum_agg.csv... Compute mean alpha power per stratum".
    # This strongly suggests raw_stratum_agg contains the subjects (or at least the stratum-level stats from T014).
    # Let's output the stratum-level summary from T014 (mean alpha, mean age, etc) for the valid strata.
    
    # We need to merge MG and EEG stats for the valid strata.
    # Since they are separate cohorts, we might not have the same subjects.
    # We will create a row for each valid stratum, showing the stats from MG and EEG separately.
    
    valid_strata_list = []
    for sid in valid_strata_ids:
        mg_row = mg_subjects[mg_subjects['stratum_id'] == sid].iloc[0] if not mg_subjects[mg_subjects['stratum_id'] == sid].empty else None
        eeg_row = eeg_subjects[eeg_subjects['stratum_id'] == sid].iloc[0] if not eeg_subjects[eeg_subjects['stratum_id'] == sid].empty else None
        
        # We only keep strata where BOTH have data (guaranteed by valid_strata_ids filter)
        row = {
            'stratum_id': sid,
            'age_bin': sid.split('_')[0],
            'sex': sid.split('_')[1],
            'bmi_bin': sid.split('_')[2],
            'diet': sid.split('_')[3],
            'n_mg': mg_counts[sid],
            'n_eeg': eeg_counts[sid],
            'mg_mean_alpha': mg_row['alpha_power'] if mg_row is not None else np.nan,
            'eeg_mean_alpha': eeg_row['alpha_power'] if eeg_row is not None else np.nan,
            'mg_mean_age': mg_row['age'] if mg_row is not None else np.nan,
            'eeg_mean_age': eeg_row['age'] if eeg_row is not None else np.nan,
        }
        valid_strata_list.append(row)
    
    final_df = pd.DataFrame(valid_strata_list)
    
    # Save raw_stratum_agg.csv
    output_csv = Path(get_project_root()) / "data" / "processed" / "raw_stratum_agg.csv"
    final_df.to_csv(output_csv, index=False)
    logger.info(f"Saved aggregated strata to {output_csv}")
    
    # Prepare report
    report = {
        "valid_strata_count": len(valid_strata_ids),
        "strata_ids": valid_strata_ids,
        "excluded_microbiome_subjects": m_excl,
        "excluded_eeg_subjects": e_excl,
        "status": "success"
    }
    
    # Save strata_report.json
    report_path = Path(get_project_root()) / "artifacts" / "strata_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved strata report to {report_path}")
    
    log_structured_event("SUCCESS", "Ecological Aggregation Complete", report)
    
    return final_df, report

def main():
    project_root = get_project_root()
    microbiome_path = Path(project_root) / "data" / "processed" / "microbiome_features.csv"
    eeg_path = Path(project_root) / "data" / "processed" / "eeg_features.csv"
    
    logger.info("Starting Ecological Aggregation...")
    
    try:
        mg_data = load_microbiome_data(microbiome_path)
        eeg_data = load_eeg_data(eeg_path)
        
        _, _ = aggregate_strata(mg_data, eeg_data)
        
        logger.info("Ecological Aggregation completed successfully.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()