"""
Correlation Analysis Module for US3.

Implements correlation analysis between years of musical training and functional
connectivity strength for musicians, including confidence interval calculations.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from scipy import stats

from utils.logging import get_logger
from data.models import ConnectivityMatrix

logger = get_logger(__name__)

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_FILE = PROCESSED_DIR / "correlation_results.csv"

# Default confidence level
CONFIDENCE_LEVEL = 0.95


def load_musicians_connectivity_data(
    connectivity_file: Optional[Path] = None,
    subjects_file: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load connectivity data for musicians only.
    
    Args:
        connectivity_file: Path to connectivity results CSV (default: data/processed/connectivity_results.csv)
        subjects_file: Path to cleaned subjects CSV (default: data/processed/subjects_cleaned.csv)
        
    Returns:
        DataFrame with connectivity data filtered to musicians only
        
    Raises:
        FileNotFoundError: If required files don't exist
        ValueError: If no musicians found in data
    """
    if connectivity_file is None:
        connectivity_file = PROCESSED_DIR / "connectivity_results.csv"
    if subjects_file is None:
        subjects_file = PROCESSED_DIR / "subjects_cleaned.csv"
        
    if not connectivity_file.exists():
        raise FileNotFoundError(f"Connectivity results file not found: {connectivity_file}")
    if not subjects_file.exists():
        raise FileNotFoundError(f"Subjects file not found: {subjects_file}")
        
    # Load subjects to identify musicians
    subjects_df = pd.read_csv(subjects_file)
    musician_subjects = subjects_df[subjects_df['group'] == 'musician']['subject_id'].tolist()
    
    if len(musician_subjects) == 0:
        raise ValueError("No musicians found in subjects data")
        
    logger.info(f"Found {len(musician_subjects)} musicians for correlation analysis")
    
    # Load connectivity data
    connectivity_df = pd.read_csv(connectivity_file)
    
    # Filter to musicians only
    musician_data = connectivity_df[connectivity_df['subject_id'].isin(musician_subjects)]
    
    if len(musician_data) == 0:
        raise ValueError("No connectivity data found for musicians")
        
    return musician_data


def compute_connectivity_strength(
    connectivity_df: pd.DataFrame,
    connection_id_col: str = 'connection_id',
    subject_id_col: str = 'subject_id'
) -> pd.DataFrame:
    """
    Compute overall connectivity strength per subject.
    
    Args:
        connectivity_df: DataFrame with connectivity data
        connection_id_col: Column name for connection identifier
        subject_id_col: Column name for subject identifier
        
    Returns:
        DataFrame with subject_id and mean connectivity strength
    """
    # Group by subject and compute mean connectivity strength
    # Assuming connectivity_df has columns: subject_id, connection_id, t_stat, p_value, etc.
    # We'll use the absolute value of t_stat as a proxy for strength
    if 't_stat' in connectivity_df.columns:
        strength_col = 't_stat'
    elif 'r_value' in connectivity_df.columns:
        strength_col = 'r_value'
    else:
        # Default to first numeric column that isn't subject_id
        numeric_cols = connectivity_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c != subject_id_col]
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found for computing strength")
        strength_col = numeric_cols[0]
        
    subject_strength = connectivity_df.groupby(subject_id_col)[strength_col].mean().reset_index()
    subject_strength.columns = [subject_id_col, 'connectivity_strength']
    
    return subject_strength


def compute_correlation_with_training(
    subject_strength_df: pd.DataFrame,
    years_col: str = 'years_of_training'
) -> Tuple[float, float]:
    """
    Compute correlation between connectivity strength and years of training.
    
    Args:
        subject_strength_df: DataFrame with subject_id, connectivity_strength, and years_of_training
        years_col: Column name for years of training
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    # Filter out rows with missing data
    valid_data = subject_strength_df.dropna(subset=['connectivity_strength', years_col])
    
    if len(valid_data) < 3:
        logger.warning("Insufficient data for correlation (need at least 3 subjects)")
        return 0.0, 1.0
        
    x = valid_data[years_col].values
    y = valid_data['connectivity_strength'].values
    
    # Compute Pearson correlation
    r, p_value = stats.pearsonr(x, y)
    
    logger.info(f"Correlation coefficient: {r:.4f}, p-value: {p_value:.4f}")
    
    return r, p_value


def calculate_correlation_ci(
    r: float,
    n: int,
    confidence_level: float = CONFIDENCE_LEVEL
) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for correlation coefficient using Fisher's z-transform.
    
    This method transforms the correlation coefficient to a normally distributed variable,
    computes the confidence interval, and then transforms back.
    
    Args:
        r: Pearson correlation coefficient (-1 to 1)
        n: Sample size (number of subjects)
        confidence_level: Confidence level (default: 0.95 for 95% CI)
        
    Returns:
        Tuple of (ci_lower, ci_upper)
        
    Raises:
        ValueError: If r is outside valid range or n is too small
    """
    if not (-1.0 <= r <= 1.0):
        raise ValueError(f"Correlation coefficient must be between -1 and 1, got {r}")
        
    if n < 3:
        raise ValueError(f"Sample size must be at least 3, got {n}")
        
    # Fisher's z-transform
    # z = 0.5 * ln((1 + r) / (1 - r))
    # Handle edge cases where r is exactly -1 or 1
    if abs(r) >= 1.0:
        # For perfect correlation, CI is effectively the point estimate
        # but we'll use a small epsilon to avoid division by zero
        r_adjusted = np.sign(r) * (1.0 - 1e-10)
        z = 0.5 * np.log((1 + r_adjusted) / (1 - r_adjusted))
    else:
        z = 0.5 * np.log((1 + r) / (1 - r))
        
    # Standard error of z
    se_z = 1.0 / np.sqrt(n - 3)
    
    # Critical value for confidence level
    alpha = 1.0 - confidence_level
    z_critical = stats.norm.ppf(1 - alpha / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_critical * se_z
    z_upper = z + z_critical * se_z
    
    # Transform back to r-space
    # r = (exp(2z) - 1) / (exp(2z) + 1)
    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    logger.debug(f"95% CI for r={r:.4f}: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return ci_lower, ci_upper


def process_correlation_analysis(
    connectivity_file: Optional[Path] = None,
    subjects_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    confidence_level: float = CONFIDENCE_LEVEL
) -> pd.DataFrame:
    """
    Perform full correlation analysis pipeline.
    
    Args:
        connectivity_file: Path to connectivity results CSV
        subjects_file: Path to cleaned subjects CSV
        output_file: Path for output CSV (default: data/processed/correlation_results.csv)
        confidence_level: Confidence level for CI calculation
        
    Returns:
        DataFrame with correlation results including confidence intervals
    """
    if output_file is None:
        output_file = RESULTS_FILE
        
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting correlation analysis for musicians...")
    
    # Load data
    musician_data = load_musicians_connectivity_data(connectivity_file, subjects_file)
    
    # Compute connectivity strength per subject
    subject_strength = compute_connectivity_strength(musician_data)
    
    # Merge with subjects data to get years of training
    subjects_df = pd.read_csv(subjects_file)
    musician_subjects = subjects_df[subjects_df['group'] == 'musician']
    
    # Merge strength with years of training
    analysis_df = pd.merge(
        subject_strength,
        musician_subjects[['subject_id', 'years_of_training']],
        on='subject_id'
    )
    
    # Compute correlation
    r, p_value = compute_correlation_with_training(analysis_df)
    n = len(analysis_df)
    
    # Calculate confidence interval
    ci_lower, ci_upper = calculate_correlation_ci(r, n, confidence_level)
    
    # Calculate effect size (Cohen's q for correlation)
    # Cohen's q = |r1 - r2|, but for single correlation we can use the correlation itself
    # or compute based on r^2 (coefficient of determination)
    effect_size = abs(r)  # Simple effect size measure
    
    # Create results DataFrame
    results = pd.DataFrame({
        'connection_id': ['overall_strength'],  # Using 'overall_strength' as the connection metric
        'r_value': [r],
        'p_value': [p_value],
        'effect_size': [effect_size],
        'ci_95_lower': [ci_lower],
        'ci_95_upper': [ci_upper],
        'n_subjects': [n],
        'confidence_level': [confidence_level]
    })
    
    # Determine stability flag
    # Low stability if CI includes zero
    if ci_lower <= 0 <= ci_upper:
        stability_flag = 'low'
    else:
        stability_flag = 'high'
        
    results['stability_flag'] = stability_flag
    
    # Save results
    results.to_csv(output_file, index=False)
    logger.info(f"Correlation results saved to {output_file}")
    
    return results


def main():
    """Main entry point for correlation analysis."""
    logger.info("Running correlation analysis (T036: CI calculation)")
    
    try:
        results = process_correlation_analysis()
        
        # Print summary
        print("\n" + "="*60)
        print("CORRELATION ANALYSIS RESULTS (MUSICIANS ONLY)")
        print("="*60)
        print(f"Number of subjects: {results['n_subjects'].iloc[0]}")
        print(f"Correlation coefficient (r): {results['r_value'].iloc[0]:.4f}")
        print(f"P-value: {results['p_value'].iloc[0]:.4f}")
        print(f"Effect size: {results['effect_size'].iloc[0]:.4f}")
        print(f"95% CI: [{results['ci_95_lower'].iloc[0]:.4f}, {results['ci_95_upper'].iloc[0]:.4f}]")
        print(f"Stability: {results['stability_flag'].iloc[0]}")
        print("="*60)
        
        return results
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during correlation analysis: {e}")
        raise


if __name__ == "__main__":
    main()