"""
Linear Mixed-Effects Model (LMM) Analysis for Topology-Conductivity Correlation.

This module implements the LMM analysis as specified in the Plan Summary.
It analyzes the relationship between topological metric variance and global
thermal conductivity for the available samples (N=2 proof-of-concept).

Due to the small sample size (N=2), the LMM will be fit with a fixed-effects
only model (equivalent to OLS) as random effects require sufficient groups.
The implementation uses statsmodels to ensure compatibility with the project's
dependency stack.
"""

import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Project imports
from config import get_config, get_paths
from metrics.topology_extractor import extract_topology_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_conductivity_samples(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load thermal samples from the processed conductivities directory.

    Args:
        data_dir: Path to data/processed/conductivities/

    Returns:
        List of sample dictionaries containing graph metrics and conductivity.
    """
    samples = []
    conductivities_dir = data_dir / "conductivities"

    if not conductivities_dir.exists():
        logger.error(f"Conductivities directory not found: {conductivities_dir}")
        return samples

    # Look for pickle files (ThermalSample objects saved by T025)
    for sample_file in conductivities_dir.glob("*.pkl"):
        try:
            with open(sample_file, 'rb') as f:
                sample = pickle.load(f)
            
            # Extract relevant data
            sample_data = {
                'sample_id': sample_file.stem,
                'conductivity': sample.get('conductivity'),  # W/mK
                'metadata': sample.get('metadata', {}),
                'graph_metrics': sample.get('graph_metrics', {})
            }
            
            # Validate conductivity is present and numeric
            if sample_data['conductivity'] is not None:
                samples.append(sample_data)
            else:
                logger.warning(f"Skipping {sample_file}: missing conductivity value")
                
        except Exception as e:
            logger.error(f"Error loading {sample_file}: {e}")
            continue

    logger.info(f"Loaded {len(samples)} valid thermal samples")
    return samples


def extract_topological_features(samples: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extract topological features from samples for LMM analysis.

    For the N=2 proof-of-concept, we extract:
    - Mean node degree
    - Mean clustering coefficient
    - Mean shortest path length
    - Variance of node degrees (topological heterogeneity)

    Args:
        samples: List of thermal sample dictionaries

    Returns:
        DataFrame with sample_id, topological features, and conductivity
    """
    if not samples:
        raise ValueError("No samples provided for analysis")

    rows = []
    for sample in samples:
        metrics = sample.get('graph_metrics', {})
        
        # Extract available metrics (with defaults if missing)
        row = {
            'sample_id': sample['sample_id'],
            'conductivity': sample['conductivity'],
            'mean_degree': metrics.get('mean_degree', 0.0),
            'mean_clustering': metrics.get('mean_clustering', 0.0),
            'mean_shortest_path': metrics.get('mean_shortest_path', 0.0),
            'degree_variance': metrics.get('degree_variance', 0.0),
            'node_count': metrics.get('node_count', 0)
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    logger.info(f"Extracted features for {len(df)} samples")
    return df


def run_lmm_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Linear Mixed-Effects Model analysis.

    For N=2, we fit a fixed-effects model (no random effects possible).
    We analyze the relationship between topological variance and conductivity.

    Args:
        df: DataFrame with features and conductivity

    Returns:
        Dictionary containing LMM results and statistics
    """
    results = {
        'model_type': 'LMM (Fixed-Effects Only for N=2)',
        'sample_size': len(df),
        'status': 'completed',
        'warnings': [],
        'coefficients': {},
        'statistics': {}
    }

    if len(df) < 2:
        results['status'] = 'insufficient_data'
        results['warnings'].append("Less than 2 samples; cannot fit model")
        return results

    # For N=2, we can only fit a simple regression (OLS) as LMM requires
    # multiple groups for random effects. We treat this as a fixed-effects model.
    # Primary analysis: conductivity ~ degree_variance (topological heterogeneity)
    
    # Prepare data
    y = df['conductivity'].values
    
    # Independent variables (add constant for intercept)
    # We focus on degree_variance as the key topological metric per Plan
    X = df[['degree_variance']].values
    X = sm.add_constant(X)
    
    # Fit OLS (equivalent to LMM fixed effects for N=2)
    try:
        model = sm.OLS(y, X)
        fitted = model.fit()
        
        results['coefficients'] = {
            'intercept': float(fitted.params[0]),
            'degree_variance_coef': float(fitted.params[1]),
            'p_value_intercept': float(fitted.pvalues[0]),
            'p_value_degree_variance': float(fitted.pvalues[1]),
            'r_squared': float(fitted.rsquared),
            'adj_r_squared': float(fitted.rsquared_adj),
            'std_err_intercept': float(fitted.bse[0]),
            'std_err_degree_variance': float(fitted.bse[1])
        }
        
        results['statistics'] = {
            'f_statistic': float(fitted.f_pvalue),
            'f_pvalue': float(fitted.f_pvalue),
            'aic': float(fitted.aic),
            'bic': float(fitted.bic),
            'nobs': int(fitted.nobs),
            'df_model': int(fitted.df_model),
            'df_resid': int(fitted.df_resid)
        }
        
        logger.info(f"LMM analysis completed: R²={results['coefficients']['r_squared']:.4f}")
        
    except Exception as e:
        results['status'] = 'error'
        results['warnings'].append(f"Model fitting failed: {str(e)}")
        logger.error(f"Error during LMM fitting: {e}")

    return results


def interpret_results(results: Dict[str, Any]) -> str:
    """
    Generate interpretation of LMM results.

    Args:
        results: Dictionary from run_lmm_analysis

    Returns:
        Human-readable interpretation string
    """
    if results['status'] != 'completed':
        return f"Analysis incomplete: {results.get('status', 'unknown')}"

    coeffs = results['coefficients']
    r2 = coeffs['r_squared']
    p_val = coeffs['p_value_degree_variance']
    coef = coeffs['degree_variance_coef']

    # Interpretation logic
    interpretation = []
    interpretation.append(f"Model R²: {r2:.4f} (variance explained)")
    
    if p_val < 0.05:
        direction = "positive" if coef > 0 else "negative"
        interpretation.append(
            f"Significant {direction} relationship between topological variance "
            f"and thermal conductivity (p={p_val:.4f}, coef={coef:.4f})."
        )
    else:
        interpretation.append(
            f"No statistically significant relationship found "
            f"(p={p_val:.4f}). Note: Sample size N=2 limits statistical power."
        )

    if r2 < 0.1:
        interpretation.append(
            "Low R² suggests topological variance alone may not be a strong "
            "predictor of conductivity in this dataset."
        )

    return " ".join(interpretation)


def save_results(
    results: Dict[str, Any],
    interpretation: str,
    output_dir: Path
) -> Path:
    """
    Save LMM analysis results to JSON.

    Args:
        results: LMM results dictionary
        interpretation: Human-readable interpretation
        output_dir: Output directory for results

    Returns:
        Path to saved results file
    """
    output_path = output_dir / "lmm_analysis_results.json"
    
    final_report = {
        'analysis_type': 'Linear Mixed-Effects Model (LMM)',
        'description': 'Correlation between topological metric variance and thermal conductivity',
        'interpretation': interpretation,
        'results': results
    }

    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    return output_path


def main():
    """Main entry point for LMM analysis."""
    logger.info("Starting LMM Analysis (Task T033)")
    
    # Get paths from config
    config = get_config()
    paths = get_paths()
    
    data_dir = paths['data']
    output_dir = paths['model_outputs']
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load samples
    samples = load_conductivity_samples(data_dir)
    
    if len(samples) < 2:
        logger.error(f"Insufficient samples for analysis (N={len(samples)}). "
                    "At least 2 samples are required.")
        # Write empty result with status
        error_result = {
            'status': 'insufficient_data',
            'sample_count': len(samples),
            'message': 'Cannot perform LMM analysis with fewer than 2 samples'
        }
        save_results(error_result, "Analysis failed: insufficient data", output_dir)
        sys.exit(1)
    
    # Extract features
    df = extract_topological_features(samples)
    
    # Run LMM analysis
    results = run_lmm_analysis(df)
    
    # Interpret results
    interpretation = interpret_results(results)
    logger.info(f"Interpretation: {interpretation}")
    
    # Save results
    save_results(results, interpretation, output_dir)
    
    logger.info("LMM Analysis completed successfully")
    return results


if __name__ == "__main__":
    main()
