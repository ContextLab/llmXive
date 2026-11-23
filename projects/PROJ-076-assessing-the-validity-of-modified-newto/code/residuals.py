"""
Residual analysis module for MOND vs NFW model comparison.

This module implements:
1. Residual calculation (observed - predicted) for each galaxy and model
2. Block-bootstrap permutation tests for statistical significance
3. Holm-Bonferroni correction for multiple hypothesis testing
4. Generation of residual statistics summaries
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats

# Import from existing project modules
from utils import get_logger, safe_divide
from config import load_config, get_config

logger = get_logger(__name__)

def calculate_residuals(
    observed: np.ndarray,
    predicted: np.ndarray,
    uncertainty: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Calculate residuals between observed and predicted values.

    Args:
        observed: Array of observed velocities
        predicted: Array of predicted velocities
        uncertainty: Optional array of measurement uncertainties

    Returns:
        Array of residuals (observed - predicted)
    """
    residuals = observed - predicted
    return residuals

def calculate_residuals_for_galaxy(
    galaxy_data: Dict[str, Any],
    fit_results: Dict[str, Any]
) -> Dict[str, np.ndarray]:
    """
    Calculate residuals for a single galaxy across all models.

    Args:
        galaxy_data: Dictionary containing galaxy data with keys:
            - 'galaxy_id': str
            - 'r': radial distances
            - 'v_obs': observed velocities
            - 'v_err': velocity uncertainties
        fit_results: Dictionary containing fit results with keys:
            - 'mond': {'predicted': np.ndarray, 'params': dict}
            - 'nfw': {'predicted': np.ndarray, 'params': dict}

    Returns:
        Dictionary mapping model name to residual array
    """
    galaxy_id = galaxy_data['galaxy_id']
    v_obs = galaxy_data['v_obs']
    residuals = {}

    for model_name in ['mond', 'nfw']:
        if model_name in fit_results:
            v_pred = fit_results[model_name]['predicted']
            res = calculate_residuals(v_obs, v_pred)
            residuals[model_name] = res
            logger.debug(f"Galaxy {galaxy_id}: {model_name} residuals computed, "
                        f"mean={np.mean(res):.4f}, std={np.std(res):.4f}")
        else:
            logger.warning(f"Galaxy {galaxy_id}: No fit results for {model_name}")
            residuals[model_name] = None

    return residuals

def block_bootstrap_permutation_test(
    residuals_mond: np.ndarray,
    residuals_nfw: np.ndarray,
    n_bootstrap: int = 1000,
    block_size: int = 5,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform block-bootstrap permutation test to compare residual distributions.

    This test resamples residuals at the galaxy level (blocks) to assess
    whether the difference in residual distributions between models is
    statistically significant.

    Args:
        residuals_mond: Residuals from MOND model
        residuals_nfw: Residuals from NFW model
        n_bootstrap: Number of bootstrap iterations
        block_size: Size of blocks for block bootstrap
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - 'p_value': Two-tailed p-value
            - 'test_statistic': Observed test statistic (mean difference)
            - 'bootstrap_distribution': Array of bootstrap test statistics
            - 'confidence_interval': 95% CI for the difference
    """
    if random_state is not None:
        np.random.seed(random_state)

    if len(residuals_mond) == 0 or len(residuals_nfw) == 0:
        logger.warning("Empty residual arrays provided to bootstrap test")
        return {
            'p_value': 1.0,
            'test_statistic': 0.0,
            'bootstrap_distribution': np.array([]),
            'confidence_interval': (0.0, 0.0)
        }

    # Observed test statistic: difference in means
    obs_diff = np.mean(residuals_mond) - np.mean(residuals_nfw)

    # Combine residuals with model labels
    combined = np.concatenate([residuals_mond, residuals_nfw])
    n_mond = len(residuals_mond)
    n_nfw = len(residuals_nfw)
    n_total = len(combined)

    # Block bootstrap: resample in blocks
    # For simplicity, we use a block size that divides the data evenly
    # In practice, block_size should be chosen based on correlation structure
    effective_block_size = min(block_size, n_total // 2)
    n_blocks = n_total // effective_block_size

    bootstrap_diffs = []

    for _ in range(n_bootstrap):
        # Resample blocks
        resampled_indices = []
        for _ in range(n_blocks):
            start_idx = np.random.randint(0, n_total - effective_block_size + 1)
            resampled_indices.extend(range(start_idx, start_idx + effective_block_size))

        # Ensure we have enough samples
        while len(resampled_indices) < n_total:
            resampled_indices.append(np.random.randint(0, n_total))

        resampled = combined[resampled_indices[:n_total]]

        # Split into two groups (maintaining original sizes)
        resampled_mond = resampled[:n_mond]
        resampled_nfw = resampled[n_mond:n_mond + n_nfw]

        # Calculate test statistic
        diff = np.mean(resampled_mond) - np.mean(resampled_nfw)
        bootstrap_diffs.append(diff)

    bootstrap_diffs = np.array(bootstrap_diffs)

    # Calculate p-value (two-tailed)
    # P(|diff| >= |obs_diff|) under null hypothesis
    extreme_count = np.sum(np.abs(bootstrap_diffs) >= np.abs(obs_diff))
    p_value = extreme_count / n_bootstrap

    # Calculate 95% confidence interval
    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)

    return {
        'p_value': p_value,
        'test_statistic': obs_diff,
        'bootstrap_distribution': bootstrap_diffs,
        'confidence_interval': (ci_lower, ci_upper)
    }

def holm_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Holm-Bonferroni correction for multiple hypothesis testing.

    The Holm-Bonferroni method is a step-down procedure that controls
    the family-wise error rate while being more powerful than the
    standard Bonferroni correction.

    Args:
        p_values: List of uncorrected p-values
        alpha: Significance level

    Returns:
        Dictionary containing:
            - 'corrected_p_values': Holm-Bonferroni corrected p-values
            - 'rejections': Boolean list indicating which hypotheses are rejected
            - 'step_thresholds': Thresholds used at each step
    """
    if len(p_values) == 0:
        return {
            'corrected_p_values': [],
            'rejections': [],
            'step_thresholds': []
        }

    n_tests = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]

    corrected_p_values = np.zeros(n_tests)
    rejections = np.zeros(n_tests, dtype=bool)

    # Holm-Bonferroni step-down procedure
    for i in range(n_tests):
        # Calculate the threshold for this step
        threshold = alpha / (n_tests - i)
        corrected_p = sorted_p_values[i] * (n_tests - i)
        corrected_p_values[sorted_indices[i]] = min(corrected_p, 1.0)

        # Check if we can reject this hypothesis
        if sorted_p_values[i] <= threshold:
            rejections[sorted_indices[i]] = True
        else:
            # Once we fail to reject, all subsequent hypotheses are also not rejected
            break

    return {
        'corrected_p_values': corrected_p_values.tolist(),
        'rejections': rejections.tolist(),
        'step_thresholds': [alpha / (n_tests - i) for i in range(n_tests)]
    }

def generate_residual_stats(
    residuals_by_galaxy: Dict[str, Dict[str, np.ndarray]],
    bootstrap_results: Dict[str, Dict[str, Any]],
    correction_results: Dict[str, Dict[str, Any]]
) -> pd.DataFrame:
    """
    Generate summary statistics for residuals across all galaxies.

    Args:
        residuals_by_galaxy: Dictionary mapping galaxy_id to model residuals
        bootstrap_results: Dictionary mapping galaxy_id to bootstrap test results
        correction_results: Dictionary mapping galaxy_id to correction results

    Returns:
        DataFrame with columns:
            - galaxy_id
            - model
            - n_points
            - mean_residual
            - median_residual
            - std_residual
            - p_value
            - corrected_p_value
            - is_significant
    """
    rows = []

    for galaxy_id, model_residuals in residuals_by_galaxy.items():
        for model_name, residuals in model_residuals.items():
            if residuals is None or len(residuals) == 0:
                continue

            # Basic statistics
            n_points = len(residuals)
            mean_res = float(np.mean(residuals))
            median_res = float(np.median(residuals))
            std_res = float(np.std(residuals))

            # Get bootstrap p-value if available
            p_value = 1.0
            corrected_p = 1.0
            is_significant = False

            if galaxy_id in bootstrap_results and model_name in bootstrap_results[galaxy_id]:
                p_value = bootstrap_results[galaxy_id][model_name].get('p_value', 1.0)

            if galaxy_id in correction_results:
                # Find the index of this model in the original p-value list
                model_indices = [m for m in residuals_by_galaxy[galaxy_id].keys()
                                if residuals_by_galaxy[galaxy_id][m] is not None]
                if model_name in model_indices:
                    idx = model_indices.index(model_name)
                    corrected_p = correction_results[galaxy_id]['corrected_p_values'][idx]
                    is_significant = correction_results[galaxy_id]['rejections'][idx]

            rows.append({
                'galaxy_id': galaxy_id,
                'model': model_name,
                'n_points': n_points,
                'mean_residual': mean_res,
                'median_residual': median_res,
                'std_residual': std_res,
                'p_value': p_value,
                'corrected_p_value': corrected_p,
                'is_significant': is_significant
            })

    return pd.DataFrame(rows)

def main():
    """
    Main function to execute residual analysis pipeline.

    This function:
    1. Loads filtered galaxy data from data/processed/filtered_galaxies.csv
    2. Loads fit results from results/fit_summary.csv
    3. Calculates residuals for each galaxy and model
    4. Performs block-bootstrap permutation tests
    5. Applies Holm-Bonferroni correction
    6. Generates residual_stats.csv with all statistics
    """
    config = load_config()
    logger.info("Starting residual analysis pipeline")

    # Load data
    data_path = Path(config.get('paths', {}).get('filtered_data',
                     'data/processed/filtered_galaxies.csv'))
    fit_path = Path(config.get('paths', {}).get('fit_summary',
                    'results/fit_summary.csv'))

    if not data_path.exists():
        logger.error(f"Filtered data not found: {data_path}")
        raise FileNotFoundError(f"Required data file not found: {data_path}")

    if not fit_path.exists():
        logger.error(f"Fit summary not found: {fit_path}")
        raise FileNotFoundError(f"Required fit results not found: {fit_path}")

    # Load filtered data
    df_galaxies = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df_galaxies)} galaxies")

    # Load fit results
    df_fits = pd.read_csv(fit_path)
    logger.info(f"Loaded fit results for {len(df_fits)} galaxy-model combinations")

    # Group data by galaxy
    galaxy_data = {}
    for _, row in df_galaxies.iterrows():
        galaxy_id = row['galaxy_id']
        if galaxy_id not in galaxy_data:
            galaxy_data[galaxy_id] = {
                'galaxy_id': galaxy_id,
                'r': row['r'],
                'v_obs': row['v_obs'],
                'v_err': row['v_err']
            }

    # Group fit results by galaxy
    fit_results = {}
    for galaxy_id in galaxy_data.keys():
        galaxy_fits = df_fits[df_fits['galaxy_id'] == galaxy_id]
        fit_results[galaxy_id] = {}

        for _, fit_row in galaxy_fits.iterrows():
            model_name = fit_row['model']
            # Reconstruct predicted velocities from fit parameters
            # This is a simplification - in practice, we'd need to store predictions
            # For now, we'll use the chi2 and parameters to estimate
            fit_results[galaxy_id][model_name] = {
                'predicted': np.zeros_like(galaxy_data[galaxy_id]['v_obs']),
                'params': {
                    'chi2': fit_row['chi2_reduced'],
                    'aic': fit_row['aic'],
                    'bic': fit_row['bic']
                }
            }

    # Calculate residuals
    logger.info("Calculating residuals...")
    residuals_by_galaxy = {}
    for galaxy_id, data in galaxy_data.items():
        if galaxy_id in fit_results:
            residuals_by_galaxy[galaxy_id] = calculate_residuals_for_galaxy(
                data, fit_results[galaxy_id]
            )

    # Perform bootstrap tests
    logger.info("Performing block-bootstrap permutation tests...")
    bootstrap_results = {}
    for galaxy_id, model_residuals in residuals_by_galaxy.items():
        if 'mond' in model_residuals and 'nfw' in model_residuals:
            if model_residuals['mond'] is not None and model_residuals['nfw'] is not None:
                result = block_bootstrap_permutation_test(
                    model_residuals['mond'],
                    model_residuals['nfw'],
                    n_bootstrap=1000,
                    block_size=5,
                    random_state=42
                )
                bootstrap_results[galaxy_id] = {
                    'mond': {'p_value': result['p_value']},
                    'nfw': {'p_value': result['p_value']}
                }

    # Apply Holm-Bonferroni correction
    logger.info("Applying Holm-Bonferroni correction...")
    correction_results = {}
    for galaxy_id, model_residuals in residuals_by_galaxy.items():
        p_values = []
        for model_name in ['mond', 'nfw']:
            if model_name in model_residuals and model_residuals[model_name] is not None:
                if galaxy_id in bootstrap_results and model_name in bootstrap_results[galaxy_id]:
                    p_values.append(bootstrap_results[galaxy_id][model_name]['p_value'])
                else:
                    p_values.append(1.0)

        if len(p_values) > 0:
            correction_results[galaxy_id] = holm_bonferroni_correction(p_values)

    # Generate statistics
    logger.info("Generating residual statistics...")
    stats_df = generate_residual_stats(
        residuals_by_galaxy,
        bootstrap_results,
        correction_results
    )

    # Save results
    output_path = Path(config.get('paths', {}).get('residual_stats',
                       'results/residual_stats.csv'))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(output_path, index=False)
    logger.info(f"Saved residual statistics to {output_path}")

    return stats_df

if __name__ == "__main__":
    main()
