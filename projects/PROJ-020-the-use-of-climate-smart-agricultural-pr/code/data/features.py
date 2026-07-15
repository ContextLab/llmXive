"""
Feature engineering for Climate-Smart Agriculture (CSA) analysis.

This module constructs the CSA Index as a weighted composite score based on:
- Conservation tillage
- Crop diversification
- Irrigation efficiency

It explicitly EXCLUDES digital-technology access and finance access variables
to maintain independence from moderation terms used in the statistical models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the components of the CSA Index
# These must be present in the processed dataset
CSA_COMPONENTS = {
    'conservation_tillage_score': 0.40,  # Weight: 40%
    'crop_diversity_index': 0.35,        # Weight: 35%
    'irrigation_efficiency_score': 0.25  # Weight: 25%
}

# Variables to explicitly EXCLUDE from the index (used as moderators/mediators later)
EXCLUDED_VARIABLES = [
    'digital_technology_access',
    'finance_access_score',
    'mobile_phone_ownership',
    'internet_access',
    'credit_access',
    'savings_account'
]

def construct_csa_index(
    df: pd.DataFrame,
    components: Optional[Dict[str, float]] = None,
    normalize: bool = True
) -> pd.DataFrame:
    """
    Construct the CSA Index as a weighted composite score.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with CSA component columns.
    components : Dict[str, float], optional
        Dictionary mapping component column names to weights.
        Defaults to CSA_COMPONENTS.
    normalize : bool, default True
        If True, normalize the index to [0, 1] range.
        
    Returns
    -------
    pd.DataFrame
        Input dataframe with new 'csa_index' column.
        
    Raises
    ------
    ValueError
        If required component columns are missing from the dataframe.
    """
    if components is None:
        components = CSA_COMPONENTS
    
    # Validate that all required components exist
    missing_cols = [col for col in components.keys() if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required CSA component columns: {missing_cols}. "
            f"Available columns: {list(df.columns)[:20]}..."
        )
    
    # Verify no excluded variables are accidentally included in components
    overlap = set(components.keys()) & set(EXCLUDED_VARIABLES)
    if overlap:
        raise ValueError(
            f"Excluded variables found in CSA components: {overlap}. "
            "Digital and finance access variables must be excluded from the CSA Index."
        )
    
    # Calculate weighted sum
    csa_scores = pd.Series(index=df.index, dtype=float)
    total_weight = sum(components.values())
    
    for col, weight in components.items():
        # Handle missing values by filling with 0 for calculation (or could use mean)
        # TODO: Consider if missing values should be handled differently
        col_data = df[col].fillna(0)
        csa_scores += col_data * weight
    
    # Normalize by total weight if weights don't sum to 1
    if abs(total_weight - 1.0) > 1e-6:
        csa_scores = csa_scores / total_weight
    
    # Normalize to [0, 1] range if requested
    if normalize:
        min_val = csa_scores.min()
        max_val = csa_scores.max()
        
        if max_val - min_val > 1e-10:  # Avoid division by zero
            csa_scores = (csa_scores - min_val) / (max_val - min_val)
        else:
            # All values are the same
            csa_scores = pd.Series(0.5, index=df.index)
    
    df = df.copy()
    df['csa_index'] = csa_scores
    
    logger.info(f"Constructed CSA Index with range [{df['csa_index'].min():.3f}, "
               f"{df['csa_index'].max():.3f}], mean={df['csa_index'].mean():.3f}")
    
    return df

def calculate_component_statistics(
    df: pd.DataFrame,
    components: Optional[Dict[str, float]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate summary statistics for each CSA component.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with CSA component columns.
    components : Dict[str, float], optional
        Dictionary of component weights.
        
    Returns
    -------
    Dict[str, Dict[str, float]]
        Statistics for each component.
    """
    if components is None:
        components = CSA_COMPONENTS
    
    stats = {}
    for col in components.keys():
        if col in df.columns:
            stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median()),
                'missing_count': int(df[col].isna().sum()),
                'missing_pct': float(df[col].isna().mean() * 100)
            }
        else:
            stats[col] = {
                'error': f"Column '{col}' not found in dataframe"
            }
    
    return stats

def validate_csa_components(
    df: pd.DataFrame,
    components: Optional[Dict[str, float]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that all required CSA components are present and valid.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    components : Dict[str, float], optional
        Component definitions.
        
    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    if components is None:
        components = CSA_COMPONENTS
    
    errors = []
    
    # Check for required columns
    missing = [col for col in components.keys() if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    
    # Check for excluded variables in components
    overlap = set(components.keys()) & set(EXCLUDED_VARIABLES)
    if overlap:
        errors.append(f"Excluded variables in components: {overlap}")
    
    # Check for reasonable value ranges (assuming components are 0-1 or 0-100)
    for col in components.keys():
        if col in df.columns:
            if df[col].min() < -1 or df[col].max() > 101:
                errors.append(
                    f"Column '{col}' has unexpected range "
                    f"[{df[col].min():.2f}, {df[col].max():.2f}]"
                )
    
    return len(errors) == 0, errors

def main():
    """
    Main function to demonstrate CSA Index construction.
    
    This function is intended for testing and validation purposes.
    In production, this would be called from the main pipeline.
    """
    import json
    
    # Create a sample dataset for demonstration
    # In production, this would load from data/processed/merged_sample.parquet
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = pd.DataFrame({
        'household_id': range(n_samples),
        'country': np.random.choice(['KEN', 'IND', 'VNM'], n_samples),
        'year': np.random.choice([2015, 2016, 2017, 2018], n_samples),
        'conservation_tillage_score': np.random.beta(2, 2, n_samples),
        'crop_diversity_index': np.random.beta(3, 2, n_samples),
        'irrigation_efficiency_score': np.random.beta(2, 3, n_samples),
        # Excluded variables (not used in index)
        'digital_technology_access': np.random.beta(2, 2, n_samples),
        'finance_access_score': np.random.beta(3, 2, n_samples)
    })
    
    # Validate components
    is_valid, errors = validate_csa_components(sample_data)
    if not is_valid:
        logger.error("Validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("All CSA components validated successfully")
    
    # Construct the index
    result_df = construct_csa_index(sample_data)
    
    # Calculate statistics
    stats = calculate_component_statistics(sample_data)
    
    # Output results
    print("\nCSA Index Construction Results:")
    print("=" * 50)
    print(f"Sample size: {len(result_df)}")
    print(f"CSA Index range: [{result_df['csa_index'].min():.3f}, "
          f"{result_df['csa_index'].max():.3f}]")
    print(f"CSA Index mean: {result_df['csa_index'].mean():.3f}")
    print(f"CSA Index std: {result_df['csa_index'].std():.3f}")
    
    print("\nComponent Statistics:")
    print("-" * 50)
    for col, stat in stats.items():
        print(f"{col}:")
        for key, value in stat.items():
            print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
    
    # Save sample output for verification
    output_path = Path('data/processed/csa_index_sample.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_parquet(output_path, index=False)
    logger.info(f"Sample output saved to {output_path}")
    
    # Save component statistics
    stats_path = Path('data/processed/csa_component_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Component statistics saved to {stats_path}")
    
    return True

if __name__ == '__main__':
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = main()
    sys.exit(0 if success else 1)
