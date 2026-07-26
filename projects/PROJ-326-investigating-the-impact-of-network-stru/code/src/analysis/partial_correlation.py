"""
Partial Correlation Analysis Module.

Implements partial correlation analysis to isolate the effect of individual
network metrics on diffusion rates while controlling for confounding variables.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from code.src.utils.config import get_global_config

logger = logging.getLogger(__name__)


class PartialCorrelationError(Exception):
    """Custom exception for partial correlation analysis errors."""
    pass


def load_simulation_results(filepath: str) -> pd.DataFrame:
    """
    Load simulation results from JSON file into a DataFrame.

    Args:
        filepath: Path to the simulation results JSON file.

    Returns:
        DataFrame containing simulation results.

    Raises:
        PartialCorrelationError: If file not found or invalid format.
    """
    path = Path(filepath)
    if not path.exists():
        raise PartialCorrelationError(f"Simulation results file not found: {filepath}")

    try:
        with open(path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise PartialCorrelationError("Simulation results must be a list of records")

        df = pd.DataFrame(data)

        # Ensure required columns exist
        required_cols = ['diffusion_rate', 'clustering_coefficient', 'average_path_length']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise PartialCorrelationError(f"Missing required columns: {missing_cols}")

        return df

    except json.JSONDecodeError as e:
        raise PartialCorrelationError(f"Invalid JSON format: {e}")


def calculate_partial_correlation(
    df: pd.DataFrame,
    target: str,
    predictor: str,
    controls: List[str]
) -> Tuple[float, float, float]:
    """
    Calculate partial correlation between target and predictor, controlling for variables.

    Args:
        df: DataFrame containing the data.
        target: Name of the target variable.
        predictor: Name of the predictor variable.
        controls: List of control variable names.

    Returns:
        Tuple of (correlation coefficient, p-value, confidence interval lower bound).

    Raises:
        PartialCorrelationError: If calculation fails.
    """
    # Check for sufficient data
    if len(df) < 3:
        raise PartialCorrelationError("Insufficient data for partial correlation (need at least 3 samples)")

    # Check for NaN values
    cols_to_check = [target, predictor] + controls
    df_clean = df[cols_to_check].dropna()

    if len(df_clean) < 3:
        raise PartialCorrelationError("Insufficient valid data after removing NaN values")

    try:
        if len(controls) == 0:
            # Standard Pearson correlation if no controls
            corr, p_value = stats.pearsonr(df_clean[target], df_clean[predictor])
            ci_lower = corr - 1.96 * np.sqrt((1 - corr**2) / (len(df_clean) - 2))
            return corr, p_value, ci_lower

        # Residualize target and predictor against controls
        control_matrix = df_clean[controls].values
        target_vec = df_clean[target].values
        predictor_vec = df_clean[predictor].values

        # Fit linear models to get residuals
        # Residuals = actual - predicted
        try:
            target_residuals = stats.resid(target_vec, control_matrix)
            predictor_residuals = stats.resid(predictor_vec, control_matrix)
        except Exception as e:
            # Fallback to manual residual calculation if scipy.stats.resid fails
            logger.warning(f"Using fallback residual calculation: {e}")
            from sklearn.linear_model import LinearRegression

            reg_target = LinearRegression().fit(control_matrix, target_vec)
            reg_predictor = LinearRegression().fit(control_matrix, predictor_vec)

            target_residuals = target_vec - reg_target.predict(control_matrix)
            predictor_residuals = predictor_vec - reg_predictor.predict(control_matrix)

        # Calculate correlation of residuals
        corr, p_value = stats.pearsonr(target_residuals, predictor_residuals)

        # Calculate confidence interval (Fisher z-transformation)
        if abs(corr) >= 1.0:
            # Handle edge case where correlation is exactly +/- 1
            z = np.sign(corr) * 3.0  # Cap at reasonable value
        else:
            z = np.arctanh(corr)

        z_se = 1.0 / np.sqrt(len(df_clean) - 3)
        z_lower = z - 1.96 * z_se
        z_upper = z + 1.96 * z_se

        ci_lower = np.tanh(z_lower)
        ci_upper = np.tanh(z_upper)

        return corr, p_value, ci_lower

    except Exception as e:
        raise PartialCorrelationError(f"Partial correlation calculation failed: {e}")


def run_partial_correlation_analysis(
    df: pd.DataFrame,
    target: str = 'diffusion_rate',
    predictors: List[str] = None,
    controls: List[str] = None
) -> Dict[str, Any]:
    """
    Run partial correlation analysis for multiple predictor variables.

    Args:
        df: DataFrame containing the data.
        target: Name of the target variable (default: 'diffusion_rate').
        predictors: List of predictor variable names. Defaults to common network metrics.
        controls: List of control variable names. Defaults to ['average_path_length'].

    Returns:
        Dictionary containing analysis results for each predictor.
    """
    if predictors is None:
        predictors = ['clustering_coefficient', 'average_path_length', 'degree', 'density']

    if controls is None:
        controls = ['average_path_length']

    results = {}

    for predictor in predictors:
        if predictor not in df.columns:
            logger.warning(f"Predictor '{predictor}' not found in data, skipping")
            continue

        # Exclude predictor from controls if it appears there
        active_controls = [c for c in controls if c != predictor]

        try:
            corr, p_value, ci_lower = calculate_partial_correlation(
                df, target, predictor, active_controls
            )

            results[predictor] = {
                'correlation_coefficient': float(corr),
                'p_value': float(p_value),
                'confidence_interval_lower': float(ci_lower),
                'confidence_interval_upper': float(np.tanh(np.arctanh(corr) + 1.96 * 1.0 / np.sqrt(len(df) - 3))),
                'sample_size': len(df),
                'status': 'success'
            }
            logger.info(f"Partial correlation for {predictor}: r={corr:.4f}, p={p_value:.4f}")

        except PartialCorrelationError as e:
            results[predictor] = {
                'error': str(e),
                'status': 'failed'
            }
            logger.error(f"Failed to calculate partial correlation for {predictor}: {e}")

    return results


def aggregate_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate partial correlation results into a summary format.

    Args:
        results: Dictionary of results from run_partial_correlation_analysis.

    Returns:
        Aggregated results dictionary.
    """
    successful = {k: v for k, v in results.items() if v.get('status') == 'success'}

    summary = {
        'total_predictors': len(results),
        'successful_analyses': len(successful),
        'failed_analyses': len(results) - len(successful),
        'results': results,
        'significant_findings': [
            predictor for predictor, data in successful.items()
            if data['p_value'] < 0.05
        ]
    }

    return summary


def main():
    """
    Main entry point for partial correlation analysis.
    Loads simulation results, runs analysis, and saves output.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get paths from config or defaults
    config = get_global_config()
    simulation_results_path = config.get('paths', {}).get(
        'simulation_results',
        'data/analysis/simulation_results.json'
    )
    output_path = config.get('paths', {}).get(
        'partial_correlation_results',
        'data/analysis/partial_correlation_results.json'
    )

    logger.info(f"Loading simulation results from: {simulation_results_path}")

    try:
        # Load data
        df = load_simulation_results(simulation_results_path)
        logger.info(f"Loaded {len(df)} simulation records")

        # Run analysis
        logger.info("Running partial correlation analysis...")
        results = run_partial_correlation_analysis(df)

        # Aggregate and save
        summary = aggregate_results(results)
        summary['metadata'] = {
            'target_variable': 'diffusion_rate',
            'analysis_type': 'partial_correlation',
            'control_variables': ['average_path_length'],
            'timestamp': str(pd.Timestamp.now())
        }

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Partial correlation results saved to: {output_path}")
        logger.info(f"Significant findings: {summary['significant_findings']}")

        return summary

    except PartialCorrelationError as e:
        logger.error(f"Partial correlation analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


if __name__ == '__main__':
    main()
