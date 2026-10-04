import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
from statsmodels.stats.power import tt_ind_solve_power
from code.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_cleaned_dataset() -> pd.DataFrame:
    """Load the final cleaned dataset."""
    config = get_config()
    path = config.get('paths', {}).get('cleaned_dataset', 'data/processed/final_cleaned_dataset.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned dataset not found at {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Cleaned dataset is empty")
    return df

def load_statistical_report() -> Dict[str, Any]:
    """Load the existing statistical report."""
    path = "data/results/statistical_report.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Statistical report not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def save_statistical_report(report: Dict[str, Any]) -> None:
    """Save the updated statistical report."""
    path = "data/results/statistical_report.json"
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Updated statistical report saved to {path}")

def calculate_power_and_mdes(
    mean1: float, mean2: float, std1: float, std2: float,
    n1: int, n2: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Returns:
        Tuple of (statistical_power, minimum_detectable_effect_size)
    """
    # Calculate Cohen's d
    # Pooled standard deviation for unequal variances (approximation)
    # Using the formula: sqrt((std1^2 + std2^2) / 2) for simplicity in MDES context
    # Or use the exact pooled SD for power calculation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    effect_size = abs(mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0

    # Calculate power using statsmodels
    # tt_ind_solve_power(effect_size, nobs1, alpha, power=None, ratio, alternative='two-sided')
    # nobs1 is the sample size of the first group
    # ratio is n2/n1
    ratio = n2 / n1 if n1 > 0 else 1.0
    
    try:
        # Calculate power given the observed effect size
        power = tt_ind_solve_power(
            effect_size=effect_size,
            nobs1=n1,
            alpha=alpha,
            power=None,
            ratio=ratio,
            alternative='two-sided'
        )
    except Exception as e:
        logger.warning(f"Power calculation failed for observed effect: {e}")
        power = 0.0

    # Calculate MDES (Minimum Detectable Effect Size)
    # Solve for effect_size given desired power (usually 0.8)
    try:
        mdes = tt_ind_solve_power(
            effect_size=None,
            nobs1=n1,
            alpha=alpha,
            power=0.80,
            ratio=ratio,
            alternative='two-sided'
        )
    except Exception as e:
        logger.warning(f"MDES calculation failed: {e}")
        mdes = 0.0

    return power, mdes

def run_power_analysis(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run power analysis for each comparison in the report and update it.
    
    Args:
        report: The statistical report dictionary.
        
    Returns:
        Updated report with power and MDES values.
    """
    df = load_cleaned_dataset()
    
    # Ensure we have the necessary columns
    required_cols = ['stimulus_type', 'perseverative_errors', 'categories_completed', 'age']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Group by stimulus_type
    groups = df.groupby('stimulus_type')
    
    # We need to identify which groups correspond to 'nostalgia' and 'control'
    # Assuming 'stimulus_type' contains these values
    nostalgia_group = None
    control_group = None
    
    for name, group in groups:
        if 'nostalgia' in str(name).lower():
            nostalgia_group = group
        elif 'control' in str(name).lower():
            control_group = group
    
    if nostalgia_group is None or control_group is None:
        raise ValueError("Could not identify 'nostalgia' and 'control' groups in stimulus_type")
    
    # Process each comparison in the report
    comparisons = report.get('comparisons', [])
    for comp in comparisons:
        metric = comp.get('metric')
        if metric not in ['perseverative_errors', 'categories_completed']:
            continue
        
        # Get group statistics
        nostalgia_data = nostalgia_group[metric].dropna()
        control_data = control_group[metric].dropna()
        
        n_nostalgia = len(nostalgia_data)
        n_control = len(control_data)
        mean_nostalgia = nostalgia_data.mean()
        mean_control = control_data.mean()
        std_nostalgia = nostalgia_data.std()
        std_control = control_data.std()
        
        # Handle case where std is NaN (e.g., single observation)
        if np.isnan(std_nostalgia): std_nostalgia = 0.0
        if np.isnan(std_control): std_control = 0.0
        
        # Calculate power and MDES
        power, mdes = calculate_power_and_mdes(
            mean_nostalgia, mean_control,
            std_nostalgia, std_control,
            n_nostalgia, n_control
        )
        
        # Update the comparison in the report
        if 'power_analysis' not in comp:
            comp['power_analysis'] = {}
        
        comp['power_analysis'].update({
            'statistical_power': round(power, 4),
            'minimum_detectable_effect_size': round(mdes, 4),
            'alpha': 0.05,
            'sample_size_nostalgia': n_nostalgia,
            'sample_size_control': n_control
        })
        
        logger.info(f"Updated power analysis for {metric}: Power={power:.4f}, MDES={mdes:.4f}")
    
    # Update summary
    summary = report.get('summary', {})
    powers = [c['power_analysis']['statistical_power'] for c in comparisons if 'power_analysis' in c]
    mdes_values = [c['power_analysis']['minimum_detectable_effect_size'] for c in comparisons if 'power_analysis' in c]
    
    if powers:
        summary['average_power'] = round(np.mean(powers), 4)
    if mdes_values:
        summary['average_mdes'] = round(np.mean(mdes_values), 4)
        
    report['summary'] = summary
    
    return report

def main():
    """Main entry point for T021."""
    logger.info("Starting T021: Power Analysis")
    
    try:
        # Load existing report
        report = load_statistical_report()
        
        # Run power analysis
        updated_report = run_power_analysis(report)
        
        # Save updated report
        save_statistical_report(updated_report)
        
        logger.info("T021 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T021: {e}")
        raise

if __name__ == "__main__":
    main()