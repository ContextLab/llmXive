"""
Covariate filtering logic for T018.

Implements validation logic to exclude trait/personality measures from primary regression,
allowing them only as covariates in secondary checks.
"""
import os
import pandas as pd
import json
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any

# List of known trait/personality measure column names (case-insensitive matching)
# These are excluded from primary regression features per FR-002 and T018 requirements.
TRAIT_MEASURE_KEYWORDS = {
    'personality', 'trait', 'big_five', 'neuroticism', 'extraversion', 
    'openness', 'agreeableness', 'conscientiousness', 'iip', 'bfi',
    'temperament', 'character', 'disposition', 'self_report', 'rating_scale',
    'post_task_rating', 'survey_score', 'personality_score', 'trait_anxiety',
    'trait_aggression', 'social_desirability'
}

# Columns that are ALWAYS allowed in primary regression (motion features)
MOTION_FEATURES = {
    'latency', 'smoothness', 'jerk', 'lead_time', 'velocity', 'acceleration',
    'motion_energy', 'trajectory_deviation', 'reaction_time', 'response_trigger'
}

# Target variable (never a feature)
TARGET_COLUMN = 'agency_score'


def is_trait_measure(column_name: str) -> bool:
    """
    Check if a column name represents a trait/personality measure.
    
    Args:
        column_name: The name of the dataframe column to check.
        
    Returns:
        True if the column appears to be a trait/personality measure, False otherwise.
    """
    name_lower = column_name.lower()
    
    # Direct match with known motion features (allowed in primary)
    if name_lower in MOTION_FEATURES:
        return False
        
    # Check against trait keywords
    for keyword in TRAIT_MEASURE_KEYWORDS:
        if keyword in name_lower:
            return True
            
    return False


def filter_features_for_primary_regression(
    df: pd.DataFrame, 
    target_col: str = TARGET_COLUMN
) -> Tuple[List[str], List[str]]:
    """
    Separate features into primary regression features and trait covariates.
    
    Args:
        df: The dataframe containing all potential features.
        target_col: The name of the target variable column.
        
    Returns:
        A tuple (primary_features, trait_covariates) where:
        - primary_features: List of column names safe for primary regression
        - trait_covariates: List of column names that are trait measures (for secondary checks only)
    """
    primary_features = []
    trait_covariates = []
    
    for col in df.columns:
        if col == target_col:
            continue
            
        if is_trait_measure(col):
            trait_covariates.append(col)
        else:
            primary_features.append(col)
            
    return primary_features, trait_covariates


def run_covariate_filtering(
    input_path: str,
    output_primary_path: str,
    output_covariate_path: str,
    config_path: str = "data/processed/modeling_config.json"
) -> Dict[str, Any]:
    """
    Main function to run covariate filtering on the cleaned dataset.
    
    Reads the cleaned data, separates features into primary regression features
    and trait covariates, and writes the resulting subsets to disk.
    
    Args:
        input_path: Path to the cleaned data CSV.
        output_primary_path: Path to write the primary regression dataset.
        output_covariate_path: Path to write the trait covariates dataset.
        config_path: Path to the modeling config JSON for metadata.
        
    Returns:
        A dictionary with filtering statistics and file paths.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Load data
    df = pd.read_csv(input_file)
    
    # Filter features
    primary_features, trait_covariates = filter_features_for_primary_regression(df)
    
    # Create primary dataset (target + primary features)
    primary_cols = [TARGET_COLUMN] + primary_features
    df_primary = df[primary_cols]
    
    # Create covariate dataset (target + trait measures)
    if trait_covariates:
        covariate_cols = [TARGET_COLUMN] + trait_covariates
        df_covariates = df[covariate_cols]
    else:
        df_covariates = df[[TARGET_COLUMN]]  # Only target if no traits found
        
    # Ensure output directories exist
    Path(output_primary_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_covariate_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write outputs
    df_primary.to_csv(output_primary_path, index=False)
    df_covariates.to_csv(output_covariate_path, index=False)
    
    # Update config with filtering metadata
    config = {}
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            
    config['covariate_filtering'] = {
        'primary_features': primary_features,
        'trait_covariates': trait_covariates,
        'n_primary_features': len(primary_features),
        'n_trait_covariates': len(trait_covariates),
        'primary_data_path': output_primary_path,
        'covariate_data_path': output_covariate_path,
        'filtering_applied': True
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    return {
        'status': 'success',
        'primary_features': primary_features,
        'trait_covariates': trait_covariates,
        'primary_data_path': output_primary_path,
        'covariate_data_path': output_covariate_path,
        'n_samples': len(df)
    }


def main():
    """Entry point for the covariate filtering script."""
    # Default paths
    input_data = "data/processed/cleaned_data.csv"
    output_primary = "data/processed/primary_regression_data.csv"
    output_covariates = "data/processed/trait_covariates_data.csv"
    config_file = "data/processed/modeling_config.json"
    
    try:
        result = run_covariate_filtering(
            input_path=input_data,
            output_primary_path=output_primary,
            output_covariate_path=output_covariates,
            config_path=config_file
        )
        
        print(f"Covariate filtering completed successfully.")
        print(f"Primary features ({len(result['primary_features'])}): {', '.join(result['primary_features'])}")
        print(f"Trait covariates ({len(result['trait_covariates'])}): {', '.join(result['trait_covariates']) if result['trait_covariates'] else 'None'}")
        print(f"Primary data saved to: {result['primary_data_path']}")
        print(f"Covariate data saved to: {result['covariate_data_path']}")
        
    except Exception as e:
        print(f"Error during covariate filtering: {e}")
        raise


if __name__ == "__main__":
    main()