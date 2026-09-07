"""
Covariate Filtering Module for T018.

Implements validation logic to exclude trait/personality measures from
primary regression analysis, allowing them only as covariates in secondary checks.

This enforces the project scope (synthetic data stress-test) and prevents
conflation of motion features with personality constructs in primary hypotheses.
"""
import os
import pandas as pd
import json
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any

# List of known trait/personality measures that must be excluded from primary regression
# Based on standard psychometric constructs often confused with motion agency
TRAIT_MEASURES: Set[str] = {
    # Personality Traits (Big Five)
    'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism',
    'ocean_openness', 'ocean_conscientiousness', 'ocean_extraversion', 'ocean_agreeableness', 'ocean_neuroticism',
    'big5_openness', 'big5_conscientiousness', 'big5_extraversion', 'big5_agreeableness', 'big5_neuroticism',
    
    # Social/Interpersonal Traits
    'social_anxiety', 'trait_anxiety', 'state_anxiety', 'trait_aggression',
    'empathy_score', 'perspective_taking', 'fantasy_scale', 'empathic_concern',
    'personal_distress', 'interpersonal_reactivity',
    
    # Self-Report/Post-Task Ratings (Explicitly excluded per task assumption)
    'post_task_rating', 'post_task_agency', 'post_task_smoothness', 'post_task_latency',
    'self_report_agency', 'self_report_smoothness', 'self_report_latency',
    'subjective_agency', 'subjective_smoothness', 'subjective_latency',
    'perceived_control', 'sense_of_agency', 'agency_feeling',
    
    # Demographic/Static Traits (Not motion-based)
    'age', 'gender', 'sex', 'education', 'income', 'occupation',
    'tech_experience', 'gaming_experience', 'vr_experience',
    'baseline_agency', 'baseline_smoothness', 'baseline_latency',
    
    # Composite/Aggregate Trait Scores
    'trait_score', 'personality_score', 'disposition_score',
    'characteristic_agency', 'stable_agency', 'trait_agency'
}

# Motion features that ARE valid for primary regression
VALID_MOTION_FEATURES: Set[str] = {
    'latency', 'smoothness', 'lead_time', 'jerk', 'velocity', 'acceleration',
    'trajectory_deviation', 'motion_entropy', 'response_time', 'reaction_time',
    'movement_duration', 'peak_velocity', 'mean_velocity', 'velocity_variance'
}

def is_trait_measure(column_name: str) -> bool:
    """
    Determine if a column represents a trait/personality measure.
    
    Args:
        column_name: The name of the dataframe column to check.
        
    Returns:
        True if the column matches a known trait measure, False otherwise.
    """
    col_lower = column_name.lower().strip()
    
    # Direct match
    if col_lower in TRAIT_MEASURES:
        return True
        
    # Partial match for compound names (e.g., 'big5_openness_score')
    for trait in TRAIT_MEASURES:
        if trait in col_lower or col_lower in trait:
            # Check if it's a valid motion feature disguised as a trait
            if col_lower in VALID_MOTION_FEATURES:
                continue
            return True
            
    return False

def filter_features_for_primary_regression(
    df: pd.DataFrame, 
    target_col: str = 'agency_score'
) -> Tuple[List[str], List[str]]:
    """
    Separate features into primary regression candidates and covariates.
    
    Primary regression candidates must be motion-based features.
    Trait/personality measures are excluded from primary regression but
    retained for secondary covariate checks.
    
    Args:
        df: The dataframe containing all features.
        target_col: The name of the target variable (default: 'agency_score').
        
    Returns:
        A tuple (primary_features, covariate_features):
        - primary_features: List of columns suitable for primary regression
        - covariate_features: List of trait measures to be used only in secondary checks
        
    Raises:
        ValueError: If no valid motion features are found for primary regression.
    """
    columns = [col for col in df.columns if col != target_col]
    
    primary_features = []
    covariate_features = []
    
    for col in columns:
        if is_trait_measure(col):
            covariate_features.append(col)
        else:
            primary_features.append(col)
    
    if not primary_features:
        raise ValueError(
            f"No valid motion features found for primary regression. "
            f"All columns were identified as trait measures: {columns}"
        )
    
    return primary_features, covariate_features

def run_covariate_filtering(
    input_path: str,
    output_primary_path: str,
    output_covariate_path: str,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for filtering covariates from the dataset.
    
    Reads the cleaned data, separates features, and writes two outputs:
    1. A dataset with only primary regression features
    2. A dataset with only covariate features (for secondary checks)
    
    Args:
        input_path: Path to the input cleaned data CSV.
        output_primary_path: Path to write the primary regression dataset.
        output_covariate_path: Path to write the covariate dataset.
        config_path: Optional path to a configuration file for custom trait lists.
        
    Returns:
        A dictionary with filtering statistics and paths.
        
    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If filtering results in no primary features.
    """
    input_path = Path(input_path)
    output_primary_path = Path(output_primary_path)
    output_covariate_path = Path(output_covariate_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # Determine target column (usually 'agency_score' or the last column)
    target_col = 'agency_score'
    if target_col not in df.columns:
        # Fallback to the last column if agency_score isn't found
        target_col = df.columns[-1]
    
    # Filter features
    primary_features, covariate_features = filter_features_for_primary_regression(
        df, target_col=target_col
    )
    
    # Create primary dataset (features + target)
    primary_df = df[primary_features + [target_col]]
    
    # Create covariate dataset (covariates + target)
    if covariate_features:
        covariate_df = df[covariate_features + [target_col]]
    else:
        # If no covariates, create empty dataframe with correct structure
        covariate_df = pd.DataFrame(columns=[target_col])
    
    # Ensure output directories exist
    output_primary_path.parent.mkdir(parents=True, exist_ok=True)
    output_covariate_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write outputs
    primary_df.to_csv(output_primary_path, index=False)
    covariate_df.to_csv(output_covariate_path, index=False)
    
    # Generate summary report
    report = {
        'input_file': str(input_path),
        'total_columns': len(df.columns),
        'primary_features_count': len(primary_features),
        'primary_features': primary_features,
        'covariate_features_count': len(covariate_features),
        'covariate_features': covariate_features,
        'target_column': target_col,
        'output_primary_file': str(output_primary_path),
        'output_covariate_file': str(output_covariate_path),
        'filtering_logic': 'Excluded trait/personality measures from primary regression'
    }
    
    # Write report to JSON
    report_path = output_primary_path.parent / 'filtering_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """
    Command-line entry point for T018 covariate filtering.
    
    Reads from data/processed/cleaned_data.csv and produces:
    - data/processed/primary_regression_data.csv
    - data/processed/covariate_data.csv
    - data/processed/filtering_report.json
    """
    # Default paths
    input_path = 'data/processed/cleaned_data.csv'
    output_primary = 'data/processed/primary_regression_data.csv'
    output_covariate = 'data/processed/covariate_data.csv'
    
    # Check for command-line arguments
    if len(__import__('sys').argv) > 1:
        input_path = __import__('sys').argv[1]
    if len(__import__('sys').argv) > 2:
        output_primary = __import__('sys').argv[2]
    if len(__import__('sys').argv) > 3:
        output_covariate = __import__('sys').argv[3]
    
    try:
        report = run_covariate_filtering(
            input_path=input_path,
            output_primary_path=output_primary,
            output_covariate_path=output_covariate
        )
        
        print(f"T018 Covariate Filtering Complete:")
        print(f"  Primary features: {report['primary_features_count']}")
        print(f"  Covariates: {report['covariate_features_count']}")
        print(f"  Primary data: {report['output_primary_file']}")
        print(f"  Covariate data: {report['output_covariate_file']}")
        print(f"  Report: {input_path.parent}/filtering_report.json")
        
    except Exception as e:
        print(f"Error during T018 filtering: {str(e)}")
        __import__('sys').exit(1)

if __name__ == '__main__':
    main()
