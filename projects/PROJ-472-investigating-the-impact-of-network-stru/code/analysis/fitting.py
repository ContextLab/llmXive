"""
Power-law model fitting and comparison for neural avalanche statistics.

This module implements model fitting for avalanche size distributions using the
`powerlaw` package. It compares Power-law, Exponential, and Log-normal models
to determine the best fit for the observed data, adhering to FR-011.
"""
import os
import numpy as np
import pandas as pd
import powerlaw
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json

# Import existing models and utilities
from data.models import AvalancheRecord, Participant
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for model comparison
MODEL_NAMES = {
    'power_law': 'Power-law',
    'exponential': 'Exponential',
    'lognormal': 'Log-normal'
}

def load_avalanche_sizes_from_store(data_root: Path) -> Dict[str, List[float]]:
    """
    Load avalanche sizes for each subject from the processed data store.

    Expects data to be stored in `data/processed/avalanches/` as per T015.
    Returns a dictionary mapping subject_id to a list of avalanche sizes.
    """
    avalanche_dir = data_root / "processed" / "avalanches"
    if not avalanche_dir.exists():
        logger.error(f"Avalanche directory not found: {avalanche_dir}")
        return {}

    subject_avalanches = {}
    for file_path in avalanche_dir.glob("*.csv"):
        try:
            # Expect filename format: sub-XXX_avalanches.csv
            subject_id = file_path.stem.replace("_avalanches", "")
            df = pd.read_csv(file_path)
            
            # Determine the column name for size (T015 output format)
            size_col = 'size' if 'size' in df.columns else None
            if not size_col:
                logger.warning(f"Could not find 'size' column in {file_path}")
                continue
            
            sizes = df[size_col].dropna().tolist()
            if sizes:
                subject_avalanches[subject_id] = sizes
            else:
                logger.warning(f"No valid sizes found in {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")

    logger.info(f"Loaded avalanche data for {len(subject_avalanches)} subjects.")
    return subject_avalanches

def fit_power_law_model(sizes: List[float]) -> Dict[str, Any]:
    """
    Fit a power-law model to the provided avalanche sizes.

    Returns a dictionary containing fit parameters and comparison results.
    """
    if not sizes or len(sizes) < 2:
        return {"error": "Insufficient data points for fitting"}

    try:
        # Fit the power law
        fit = powerlaw.Fit(sizes, discrete=True, verbose=False)
        
        # Extract parameters
        alpha = fit.power_law.alpha
        xmin = fit.power_law.xmin
        
        # Perform model comparison
        # Compare Power-law vs Exponential
        r_exp, p_exp = fit.distribution_compare('power_law', 'exponential', normalized_ratio=True)
        # Compare Power-law vs Log-normal
        r_ln, p_ln = fit.distribution_compare('power_law', 'lognormal', normalized_ratio=True)
        
        # Determine best fit among the three
        # Note: powerlaw.Fit automatically computes likelihoods for common distributions
        # We use the comparison results to decide
        
        results = {
            'alpha': alpha,
            'xmin': xmin,
            'log_likelihood': fit.power_law.loglikelihood,
            'comparison': {
                'vs_exponential': {
                    'ratio': r_exp,
                    'p_value': p_exp,
                    'preferred': 'power_law' if r_exp > 0 else 'exponential'
                },
                'vs_lognormal': {
                    'ratio': r_ln,
                    'p_value': p_ln,
                    'preferred': 'power_law' if r_ln > 0 else 'lognormal'
                }
            },
            'best_model': 'power_law' if r_exp > 0 and r_ln > 0 else ('exponential' if r_exp < 0 and r_exp > r_ln else 'lognormal'),
            'fit_successful': True
        }
        
        return results
    except Exception as e:
        logger.error(f"Power-law fitting failed: {e}")
        return {
            "error": str(e),
            "fit_successful": False
        }

def run_fitting_for_subject(subject_id: str, sizes: List[float]) -> Dict[str, Any]:
    """
    Run the full fitting pipeline for a single subject.
    """
    logger.info(f"Fitting model for subject {subject_id} with {len(sizes)} avalanches.")
    result = fit_power_law_model(sizes)
    result['subject_id'] = subject_id
    result['n_avalanches'] = len(sizes)
    return result

def generate_fitting_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a summary CSV and JSON report of the fitting results.
    """
    if not results:
        logger.warning("No results to report.")
        return

    # Prepare data for CSV
    rows = []
    for res in results:
        if res.get('fit_successful'):
            row = {
                'subject_id': res['subject_id'],
                'n_avalanches': res['n_avalanches'],
                'alpha': res['alpha'],
                'xmin': res['xmin'],
                'best_model': res['best_model'],
                'p_vs_exponential': res['comparison']['vs_exponential']['p_value'],
                'p_vs_lognormal': res['comparison']['vs_lognormal']['p_value'],
                'preferred_vs_exp': res['comparison']['vs_exponential']['preferred'],
                'preferred_vs_ln': res['comparison']['vs_lognormal']['preferred']
            }
        else:
            row = {
                'subject_id': res['subject_id'],
                'n_avalanches': res.get('n_avalanches', 0),
                'alpha': None,
                'xmin': None,
                'best_model': None,
                'p_vs_exponential': None,
                'p_vs_lognormal': None,
                'preferred_vs_exp': None,
                'preferred_vs_ln': None,
                'error': res.get('error', 'Unknown')
            }
        rows.append(row)

    df = pd.DataFrame(rows)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Fitting report saved to {output_path}")

    # Save detailed JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Detailed fitting results saved to {json_path}")

def run_fitting_pipeline(data_root: Optional[Path] = None) -> Path:
    """
    Main pipeline entry point to run fitting for all available subjects.
    """
    if data_root is None:
        from config import get_data_root
        data_root = get_data_root()

    logger.info("Starting power-law fitting pipeline.")
    
    # Load data
    subject_data = load_avalanche_sizes_from_store(data_root)
    
    if not subject_data:
        logger.error("No data found for fitting. Ensure avalanche data exists in data/processed/avalanches/")
        return data_root / "results" / "fitting_report.csv"

    # Run fitting
    results = []
    for subject_id, sizes in subject_data.items():
        res = run_fitting_for_subject(subject_id, sizes)
        results.append(res)

    # Generate report
    output_file = data_root / "results" / "fitting_report.csv"
    generate_fitting_report(results, output_file)
    
    return output_file

def main():
    """
    CLI entry point.
    """
    from config import get_data_root
    output_file = run_fitting_pipeline(get_data_root())
    print(f"Fitting complete. Report saved to: {output_file}")

if __name__ == "__main__":
    main()
