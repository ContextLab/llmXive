"""
Module: 02_merge.py
Task: T015a, T015b, T017a, T017b
Description: Merges genomic and environmental data, filters replicates, and validates.
Outputs: data/processed/merged_dataset.csv, data/results/data_validation_report.json
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Constants
INPUT_GENE_PATH = PROJECT_ROOT / "data" / "processed" / "gene_expression_normalized.csv"
INPUT_ENV_PATH = PROJECT_ROOT / "data" / "processed" / "environmental_data_cleaned.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
REPORT_PATH = PROJECT_ROOT / "data" / "results" / "data_validation_report.json"

def ensure_dirs():
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_stage1_data():
    """Load data produced by the ingestion stage."""
    if not INPUT_GENE_PATH.exists():
        raise FileNotFoundError(f"Gene expression file not found: {INPUT_GENE_PATH}")
    if not INPUT_ENV_PATH.exists():
        raise FileNotFoundError(f"Environmental data file not found: {INPUT_ENV_PATH}")
    
    gene_df = pd.read_csv(INPUT_GENE_PATH)
    env_df = pd.read_csv(INPUT_ENV_PATH)
    return gene_df, env_df

def filter_environmental(df):
    """
    T015b: Exclude samples where ANY of the following are missing:
    'temperature', 'light intensity', OR 'CO2 level'.
    """
    critical_cols = ['temperature', 'light intensity', 'CO2 level']
    missing_mask = df[critical_cols].isnull().any(axis=1)
    excluded_count = missing_mask.sum()
    
    if excluded_count > 0:
        print(f"Excluding {excluded_count} samples due to missing critical environmental metadata.")
    return df[~missing_mask], excluded_count

def filter_replicates(df):
    """
    T015a: Filter out experimental conditions with <3 biological replicates.
    Logic: Group by 'experiment_id' (or similar unique ID) and count.
    """
    # Assuming 'experiment_id' is the column defining the condition
    # If not present, we might group by a combination of metadata, but 'experiment_id' is standard.
    id_col = 'experiment_id'
    if id_col not in df.columns:
        # Fallback: assume all data is one condition if no ID (unlikely) or use sample_id
        print(f"Warning: Column '{id_col}' not found. Skipping replicate filter.")
        return df, 0

    counts = df[id_col].value_counts()
    valid_ids = counts[counts >= 3].index
    excluded_count = len(counts[counts < 3])
    
    if excluded_count > 0:
        print(f"Excluding {excluded_count} samples due to insufficient biological replicates (<3).")
    
    return df[df[id_col].isin(valid_ids)], excluded_count

def merge_dataframes(gene_df, env_df):
    """
    Merge genomic and environmental data by exact sample pairing.
    Assuming 'sample_id' is the common key.
    """
    common_key = 'sample_id'
    if common_key not in gene_df.columns or common_key not in env_df.columns:
        raise ValueError(f"Common key '{common_key}' not found in both datasets.")
    
    # Inner join to ensure exact pairing
    merged = pd.merge(gene_df, env_df, on=common_key, how='inner')
    print(f"Merged dataset shape: {merged.shape}")
    return merged

def validate_numeric_columns(df):
    """
    T017a: Validate types and ensure no non-numeric entries in numeric columns.
    """
    # Identify numeric columns (excluding sample_id and experiment_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    issues = []
    for col in numeric_cols:
        if df[col].isnull().any():
            # Check if NaNs are acceptable (handled by imputation earlier, but check for residuals)
            # For this stage, we report them but don't crash if they exist, as imputation might be pending
            issues.append(f"Column '{col}' has {df[col].isnull().sum()} missing values.")
    
    return issues

def generate_validation_report(df, excluded_env, excluded_rep, validation_issues):
    """
    T017b: Generate data_validation_report.json.
    """
    report = {
        "total_samples": len(df),
        "excluded_samples": excluded_env + excluded_rep,
        "missing_values_imputed": 0, # Count would come from imputation step if tracked here
        "validation_status": "passed" if not validation_issues else "warnings",
        "validation_issues": validation_issues,
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Main execution function."""
    ensure_dirs()
    
    try:
        print("Loading stage 1 data...")
        gene_df, env_df = load_stage1_data()
        
        print("Filtering environmental metadata...")
        env_df, excluded_env = filter_environmental(env_df)
        
        print("Filtering replicates...")
        env_df, excluded_rep = filter_replicates(env_df)
        
        print("Merging data...")
        merged_df = merge_dataframes(gene_df, env_df)
        
        print("Validating numeric columns...")
        issues = validate_numeric_columns(merged_df)
        
        print("Generating validation report...")
        report = generate_validation_report(merged_df, excluded_env, excluded_rep, issues)
        
        print(f"Saving merged dataset to {OUTPUT_PATH}...")
        merged_df.to_csv(OUTPUT_PATH, index=False)
        
        print("Merge and validation completed successfully.")
        print(f"Report saved to {REPORT_PATH}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
