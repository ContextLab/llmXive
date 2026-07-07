import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from loguru import logger
from src.utils.logging import get_logger

logger = get_logger()

def load_interactions(data_dir: str) -> pd.DataFrame:
    """
    Load interaction data from the raw directory.
    Expects 'interactions_merged.csv' in data_dir/raw.
    """
    raw_dir = Path(data_dir) / "raw"
    file_path = raw_dir / "interactions_merged.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Interaction file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} interaction records from {file_path}")
    return df

def filter_unknown_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where the interaction label is 'unknown'.
    These are excluded from training but tracked for quality metrics.
    """
    initial_count = len(df)
    if 'interaction' in df.columns:
        df_clean = df[df['interaction'] != 'unknown']
        removed_count = initial_count - len(df_clean)
        logger.info(f"Removed {removed_count} records with 'unknown' labels.")
        return df_clean
    elif 'label' in df.columns:
        df_clean = df[df['label'] != 'unknown']
        removed_count = initial_count - len(df_clean)
        logger.info(f"Removed {removed_count} records with 'unknown' labels.")
        return df_clean
    else:
        logger.warning("No 'interaction' or 'label' column found. Returning original data.")
        return df

def load_valid_pathogens(data_dir: str) -> List[str]:
    """
    Load the list of valid pathogens (those with >0 interactions) from the processed directory.
    """
    processed_dir = Path(data_dir) / "processed"
    file_path = processed_dir / "valid_pathogens.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Valid pathogens file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        pathogens = json.load(f)
    
    logger.info(f"Loaded {len(pathogens)} valid pathogens.")
    return pathogens

def split_pathogen_stratified(
    df: pd.DataFrame, 
    valid_pathogens: List[str], 
    test_size: float = 0.2, 
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the interaction dataframe into train and test sets based on pathogen.
    Ensures pathogen distribution is maintained (stratified by pathogen ID).
    """
    # Identify the pathogen column
    pathogen_col = 'pathogen_id' if 'pathogen_id' in df.columns else 'pathogen'
    
    # Filter to valid pathogens first
    df_valid = df[df[pathogen_col].isin(valid_pathogens)]
    
    if len(df_valid) == 0:
        raise ValueError("No valid interactions found after filtering.")
    
    # Stratified split by pathogen
    # We group by pathogen to ensure all interactions for a pathogen stay together
    pathogen_groups = df_valid.groupby(pathogen_col)
    
    train_paths = []
    test_paths = []
    
    # Simple random split of pathogen IDs for stratification approximation
    pathogen_ids = list(pathogen_groups.groups.keys())
    np.random.seed(seed)
    np.random.shuffle(pathogen_ids)
    
    split_idx = int(len(pathogen_ids) * (1 - test_size))
    train_paths = pathogen_ids[:split_idx]
    test_paths = pathogen_ids[split_idx:]
    
    train_df = df_valid[df_valid[pathogen_col].isin(train_paths)]
    test_df = df_valid[df_valid[pathogen_col].isin(test_paths)]
    
    logger.info(f"Split complete: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

def save_split_metadata(train_df: pd.DataFrame, test_df: pd.DataFrame, output_dir: str):
    """
    Save metadata about the train/test split.
    """
    out_path = Path(output_dir) / "processed"
    out_path.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "train_count": len(train_df),
        "test_count": len(test_df),
        "train_pathogens": list(train_df['pathogen_id'].unique() if 'pathogen_id' in train_df.columns else train_df['pathogen'].unique()),
        "test_pathogens": list(test_df['pathogen_id'].unique() if 'pathogen_id' in test_df.columns else test_df['pathogen'].unique())
    }
    
    with open(out_path / "split_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved split metadata to {out_path / 'split_metadata.json'}")

def generate_sensitivity_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a sensitivity dataset by treating missing/unknown interactions as negative (0).
    This creates a dense label vector for sensitivity analysis.
    """
    df_sens = df.copy()
    
    if 'interaction' in df_sens.columns:
        # Replace 'unknown' with 0 (negative)
        df_sens['interaction'] = df_sens['interaction'].replace('unknown', 0)
        # Ensure numeric
        df_sens['interaction'] = pd.to_numeric(df_sens['interaction'], errors='coerce').fillna(0).astype(int)
    elif 'label' in df_sens.columns:
        df_sens['label'] = df_sens['label'].replace('unknown', 0)
        df_sens['label'] = pd.to_numeric(df_sens['label'], errors='coerce').fillna(0).astype(int)
    
    logger.info(f"Generated sensitivity dataset with {len(df_sens)} records.")
    return df_sens

def run_preprocessing_pipeline(data_dir: str, output_dir: str) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline: load, filter, split, and generate sensitivity data.
    """
    logger.info("Starting preprocessing pipeline.")
    
    # Load
    df = load_interactions(data_dir)
    
    # Filter unknowns for primary model
    df_clean = filter_unknown_labels(df)
    
    # Load valid pathogens
    valid_pathogens = load_valid_pathogens(data_dir)
    
    # Split
    train_df, test_df = split_pathogen_stratified(df_clean, valid_pathogens)
    
    # Save metadata
    save_split_metadata(train_df, test_df, output_dir)
    
    # Generate sensitivity dataset (treat unknowns as 0)
    df_sens = generate_sensitivity_dataset(df)
    sens_path = Path(output_dir) / "processed" / "sensitivity_interactions.csv"
    df_sens.to_csv(sens_path, index=False)
    logger.info(f"Saved sensitivity dataset to {sens_path}")
    
    return {
        "train_count": len(train_df),
        "test_count": len(test_df),
        "sensitivity_count": len(df_sens)
    }

def generate_data_quality_report(data_dir: str, output_dir: str) -> Dict[str, Any]:
    """
    Generate a data quality report quantifying missing % per pathogen (FR-013).
    
    Logic:
    1. Load raw interactions (interactions_merged.csv).
    2. Identify all unique pathogen-host pairs that SHOULD exist based on the
       cartesian product of observed pathogens and observed hosts in the raw file,
       OR compare against a known reference matrix if available.
       For this implementation, we calculate the percentage of 'unknown' or missing
       interactions relative to the total possible interactions observed in the raw data
       per pathogen.
    
    3. If the data format includes a 'status' or 'label' column with 'unknown',
       count those as missing.
    
    Output: data/reports/data_quality_report.json
    """
    logger.info("Generating data quality report.")
    
    raw_dir = Path(data_dir) / "raw"
    report_dir = Path(output_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = raw_dir / "interactions_merged.csv"
    
    if not file_path.exists():
        logger.error(f"Cannot generate report: {file_path} not found.")
        return {}
    
    df = pd.read_csv(file_path)
    
    # Determine column names dynamically
    pathogen_col = 'pathogen_id' if 'pathogen_id' in df.columns else 'pathogen'
    label_col = 'interaction' if 'interaction' in df.columns else 'label'
    
    if pathogen_col not in df.columns:
        logger.error(f"Pathogen column '{pathogen_col}' not found in {file_path}")
        return {}
    
    # Identify missing/unknown interactions
    # We assume 'unknown' string or NaN represents missing data
    missing_mask = df[label_col].isna() | (df[label_col].astype(str).str.lower() == 'unknown')
    
    df['is_missing'] = missing_mask
    
    # Group by pathogen to calculate stats
    stats = []
    
    for pathogen, group in df.groupby(pathogen_col):
        total = len(group)
        missing_count = group['is_missing'].sum()
        missing_pct = (missing_count / total * 100) if total > 0 else 0.0
        
        stats.append({
            "pathogen_id": pathogen,
            "total_interactions_observed": total,
            "missing_interactions_count": int(missing_count),
            "missing_percentage": round(missing_pct, 2)
        })
    
    # Sort by missing percentage descending
    report_data = sorted(stats, key=lambda x: x['missing_percentage'], reverse=True)
    
    # Calculate summary
    total_records = len(df)
    total_missing = df['is_missing'].sum()
    overall_missing_pct = (total_missing / total_records * 100) if total_records > 0 else 0.0
    
    summary = {
        "total_records_analyzed": total_records,
        "total_missing_records": int(total_missing),
        "overall_missing_percentage": round(overall_missing_pct, 2),
        "pathogen_count": len(report_data)
    }
    
    final_report = {
        "summary": summary,
        "per_pathogen_details": report_data
    }
    
    output_file = report_dir / "data_quality_report.json"
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Data quality report saved to {output_file}")
    return final_report

def main():
    """
    Entry point for running preprocessing or quality report generation via CLI.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Preprocessing and Quality Report Generation")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to data directory")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to output directory")
    parser.add_argument("--mode", type=str, choices=["pipeline", "quality"], default="pipeline",
                        help="Mode: 'pipeline' for full preprocessing, 'quality' for quality report only")
    
    args = parser.parse_args()
    
    if args.mode == "quality":
        generate_data_quality_report(args.data_dir, args.output_dir)
    else:
        run_preprocessing_pipeline(args.data_dir, args.output_dir)
        generate_data_quality_report(args.data_dir, args.output_dir)

if __name__ == "__main__":
    main()
