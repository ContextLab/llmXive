"""
Validation logic to exclude trait/personality measures from primary regression.

This module implements the logic to:
1. Identify and exclude trait/personality measures from the primary feature set.
2. Allow these measures only as covariates in secondary checks.

Assumption: Trait measures are typically post-task ratings or psychometric scores.
"""
import os
import pandas as pd
import json
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any

# Standardized list of known trait/personality measure column patterns
# These should be excluded from primary regression features
TRAIT_MEASURE_PATTERNS = [
    'trait', 'personality', 'big_five', 'neuroticism', 'extraversion',
    'openness', 'agreeableness', 'conscientiousness', 'bfi', 'iip',
    'post_task_rating', 'survey_score', 'psychometric', 'trait_anxiety',
    'trait_self_report', 'demographic_trait'
]

# Columns that are strictly outcome variables (not features)
OUTCOME_COLUMNS = ['agency_score', 'participant_id']

def is_trait_measure(column_name: str) -> bool:
    """
    Check if a column name matches known trait/personality measure patterns.
    
    Args:
        column_name: The name of the column to check.
        
    Returns:
        True if the column appears to be a trait/personality measure.
    """
    col_lower = column_name.lower()
    return any(pattern in col_lower for pattern in TRAIT_MEASURE_PATTERNS)

def filter_features_for_primary_regression(
    df: pd.DataFrame, 
    exclude_patterns: List[str] = None
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Separate features into primary regression set and covariate-only set.
    
    Primary regression features: Motion features (latency, smoothness, lead_time, etc.)
    Covariate set: Trait/personality measures (excluded from primary, allowed in secondary)
    
    Args:
        df: The input DataFrame.
        exclude_patterns: Optional list of additional column patterns to exclude from primary.
        
    Returns:
        Tuple of (primary_features_df, primary_feature_names, covariate_feature_names)
    """
    all_columns = set(df.columns)
    
    # Remove outcome variables
    feature_columns = all_columns - set(OUTCOME_COLUMNS)
    
    primary_features = []
    covariate_features = []
    
    for col in feature_columns:
        if is_trait_measure(col):
            covariate_features.append(col)
        else:
            primary_features.append(col)
    
    # Apply additional exclusions if provided
    if exclude_patterns:
        additional_exclusions = []
        for col in primary_features:
            if any(pat.lower() in col.lower() for pat in exclude_patterns):
                additional_exclusions.append(col)
        
        primary_features = [f for f in primary_features if f not in additional_exclusions]
        covariate_features.extend(additional_exclusions)
    
    # Create DataFrames
    primary_df = df[[c for c in primary_features if c in df.columns]]
    
    return primary_df, primary_features, covariate_features

def run_covariate_filtering(
    input_path: str,
    output_primary_path: str,
    output_covariate_path: str,
    output_log_path: str,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main function to run covariate filtering on the cleaned dataset.
    
    Args:
        input_path: Path to the cleaned input CSV (from T017).
        output_primary_path: Path to save primary features CSV.
        output_covariate_path: Path to save covariate features CSV.
        output_log_path: Path to save the filtering log/report.
        config: Optional configuration dictionary.
        
    Returns:
        Dictionary with filtering results and metadata.
    """
    config = config or {}
    
    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Extract features
    primary_df, primary_cols, covariate_cols = filter_features_for_primary_regression(
        df, 
        exclude_patterns=config.get('additional_exclude_patterns', [])
    )
    
    # Save primary features (for primary regression)
    os.makedirs(os.path.dirname(output_primary_path), exist_ok=True)
    primary_df.to_csv(output_primary_path, index=False)
    
    # Save covariate features (for secondary checks only)
    if covariate_cols:
        covariate_df = df[[c for c in covariate_cols if c in df.columns]]
        os.makedirs(os.path.dirname(output_covariate_path), exist_ok=True)
        covariate_df.to_csv(output_covariate_path, index=False)
    else:
        # Create empty file if no covariates found
        os.makedirs(os.path.dirname(output_covariate_path), exist_ok=True)
        pd.DataFrame(columns=covariate_cols).to_csv(output_covariate_path, index=False)
    
    # Generate log report
    log_report = {
        "input_file": input_path,
        "total_rows": len(df),
        "total_columns_initial": len(df.columns),
        "primary_features": primary_cols,
        "primary_feature_count": len(primary_cols),
        "covariate_features": covariate_cols,
        "covariate_feature_count": len(covariate_cols),
        "excluded_from_primary": [c for c in df.columns if c not in primary_cols and c not in OUTCOME_COLUMNS],
        "status": "success"
    }
    
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, 'w') as f:
        json.dump(log_report, f, indent=2)
    
    return log_report

def main():
    """Entry point for command-line execution."""
    # Default paths based on project structure
    input_path = "data/processed/cleaned_data.csv"
    output_primary_path = "data/processed/primary_features.csv"
    output_covariate_path = "data/processed/covariate_features.csv"
    output_log_path = "data/processed/covariate_filter_log.json"
    
    # Check if input exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        print("Please ensure T017 (output_cleaned_data.py) has been completed.")
        return 1
    
    try:
        result = run_covariate_filtering(
            input_path=input_path,
            output_primary_path=output_primary_path,
            output_covariate_path=output_covariate_path,
            output_log_path=output_log_path
        )
        
        print(f"Covariate filtering completed successfully.")
        print(f"Primary features saved to: {output_primary_path}")
        print(f"Covariate features saved to: {output_covariate_path}")
        print(f"Log report saved to: {output_log_path}")
        print(f"Primary features count: {result['primary_feature_count']}")
        print(f"Covariate features count: {result['covariate_feature_count']}")
        
        return 0
        
    except Exception as e:
        print(f"Error during covariate filtering: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())