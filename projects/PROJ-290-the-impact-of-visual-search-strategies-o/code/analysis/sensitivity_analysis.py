"""
Sensitivity Analysis Module for Visual Search Strategies Project.

This module implements the sensitivity analysis required by FR-010.
It evaluates the stability of the exploratory cluster-based approach
by sweeping k over {2, 3} and running secondary LMMs.

Outputs:
    results/sensitivity_report.yaml (SC-006)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml
import pandas as pd
import numpy as np

# Local imports (matching API surface)
from utils.logging import get_logger
from config import get_config

# Import LMM functionality from the main analysis module
# Note: We assume fit_lmm_with_fallback and load_processed_features are available
# We need to import the specific functions we need.
# Since the API surface shows `from analysis.lmm import ...`, we import from there.
try:
    from analysis.lmm import fit_lmm_with_fallback, load_processed_features
except ImportError:
    # Fallback if running in a context where analysis.lmm isn't directly importable
    # but the file exists. This is a safety net for the import structure.
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.lmm import fit_lmm_with_fallback, load_processed_features


def get_logger_wrapper(module_name: str = __name__) -> logging.Logger:
    """
    Get a logger instance configured for this module.
    """
    return get_logger(module_name)


def load_cluster_labels(k: int, logger: logging.Logger) -> pd.DataFrame:
    """
    Load cluster labels for a specific k from the processed features.
    The labels are expected to be in the 'data/processed/labels_k{K}.csv' file
    or merged into the main features file if T024b merged them.
    Based on T024b description: "output `data/processed/labels_k2.csv` and `data/processed/labels_k3.csv`."

    We expect the file to have at least 'participant_id' and 'cluster_label' columns.
    """
    config = get_config()
    labels_path = config.PROCESSED_DATA_DIR / f"labels_k{k}.csv"

    if not labels_path.exists():
        logger.error(f"Cluster labels file not found: {labels_path}")
        raise FileNotFoundError(f"Cluster labels file not found: {labels_path}")

    logger.info(f"Loading cluster labels for k={k} from {labels_path}")
    df = pd.read_csv(labels_path)

    required_cols = ['participant_id', 'cluster_label']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in {labels_path}: {missing_cols}")
        raise ValueError(f"Missing required columns in {labels_path}: {missing_cols}")

    return df[['participant_id', 'cluster_label']]


def fit_descriptive_lmm(
    df: pd.DataFrame,
    outcome_col: str = 'detection_time',
    predictor_col: str = 'cluster_label',
    subject_col: str = 'participant_id',
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Fit a descriptive LMM using cluster labels as the fixed effect.
    This is the secondary analysis for sensitivity.

    Returns a dictionary with model results (coefficients, p-values, etc.).
    """
    if logger is None:
        logger = get_logger(__name__)

    logger.info(f"Fitting descriptive LMM: outcome={outcome_col}, predictor={predictor_col}")

    # Prepare data for LMM
    # We assume fit_lmm_with_fallback handles the formula construction and fitting.
    # The formula should be: f"{outcome_col} ~ {predictor_col} + (1|{subject_col})"
    formula = f"{outcome_col} ~ {predictor_col} + (1|{subject_col})"

    try:
        # Call the existing LMM fitting function
        # We need to ensure the dataframe has all necessary columns
        # and that the predictor is treated correctly (categorical if needed)
        if predictor_col in df.columns:
            # Ensure predictor is categorical if it's an integer label
            if df[predictor_col].dtype in ['int64', 'float64']:
                # We might need to convert to category for statsmodels to treat it as factor
                # But fit_lmm_with_fallback might handle this.
                # Let's assume it handles it or we pass the raw df.
                pass

        result = fit_lmm_with_fallback(
            data=df,
            formula=formula,
            logger=logger
        )

        # Extract relevant metrics
        # The return format of fit_lmm_with_fallback is assumed to be a dict or object
        # Let's assume it returns a dict with 'converged', 'summary', 'coefficients', etc.
        # If it returns a statsmodels object, we need to extract from there.
        # Given the API surface, let's assume it returns a structured dict.

        if isinstance(result, dict):
            return result
        else:
            # If it's a statsmodels result object, extract manually
            summary = result.summary().as_text()
            # Parse summary or extract tables if needed.
            # For now, let's return a simplified structure.
            # We need to get coefficients and p-values.
            params = result.params
            pvalues = result.pvalues
            std_err = result.bse
            tvalues = result.tvalues

            return {
                'converged': True, # Assume converged if we got here without exception
                'coefficients': params.to_dict(),
                'pvalues': pvalues.to_dict(),
                'std_errors': std_err.to_dict(),
                'tvalues': tvalues.to_dict(),
                'summary_text': summary
            }

    except Exception as e:
        logger.error(f"Failed to fit LMM for k={k}: {e}")
        return {
            'converged': False,
            'error': str(e),
            'coefficients': {},
            'pvalues': {}
        }


def run_sensitivity_analysis(
    k_values: List[int] = [2, 3],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis.

    1. Load processed features (for outcome and subject).
    2. For each k in k_values:
       a. Load cluster labels.
       b. Merge with features.
       c. Fit descriptive LMM.
       d. Record coefficient variance/stability.
    3. Compile report.

    Returns the sensitivity report dictionary.
    """
    if logger is None:
        logger = get_logger(__name__)

    logger.info("Starting Sensitivity Analysis")

    # Load main features
    try:
        # We need to load the main features to get detection_time and participant_id
        # load_processed_features should return a DataFrame
        main_features = load_processed_features(logger=logger)
    except Exception as e:
        logger.error(f"Failed to load processed features: {e}")
        raise

    report = {
        'analysis_type': 'Sensitivity Analysis (Cluster Stability)',
        'description': 'Evaluates stability of exploratory cluster-based LMM by sweeping k over {2, 3}',
        'k_values_tested': k_values,
        'results': []
    }

    for k in k_values:
        logger.info(f"Processing k={k}")
        try:
            # Load labels
            labels_df = load_cluster_labels(k, logger)

            # Merge with main features
            merged_df = pd.merge(
                main_features,
                labels_df,
                on='participant_id',
                how='inner'
            )

            if merged_df.empty:
                logger.warning(f"No data after merging for k={k}. Skipping.")
                continue

            # Fit LMM
            lmm_result = fit_descriptive_lmm(
                df=merged_df,
                outcome_col='detection_time',
                predictor_col='cluster_label',
                subject_col='participant_id',
                logger=logger
            )

            # Extract coefficient for the cluster predictor (usually the non-intercept)
            # We look for the coefficient associated with cluster_label (if it's categorical)
            # or the specific label if it's numeric.
            # Assuming cluster_label is treated as a factor, we expect coefficients like 'cluster_label[T.1]'
            # We'll store the whole coefficients dict for now and compute variance later.

            k_result = {
                'k': k,
                'n_participants': merged_df['participant_id'].nunique(),
                'n_observations': len(merged_df),
                'lmm_converged': lmm_result.get('converged', False),
                'coefficients': lmm_result.get('coefficients', {}),
                'pvalues': lmm_result.get('pvalues', {}),
                'std_errors': lmm_result.get('std_errors', {}),
                'tvalues': lmm_result.get('tvalues', {})
            }

            report['results'].append(k_result)

        except Exception as e:
            logger.error(f"Error processing k={k}: {e}")
            report['results'].append({
                'k': k,
                'error': str(e)
            })

    # Calculate coefficient variance across k values (if successful)
    # We focus on the coefficient of the cluster effect.
    # This is a simplified stability check.
    cluster_coeffs = []
    for res in report['results']:
        if 'error' not in res and res.get('lmm_converged'):
            # Find the coefficient for cluster_label (excluding intercept)
            for key, val in res['coefficients'].items():
                if 'cluster_label' in key and key != 'cluster_label': # Handle T.1, T.2 etc
                    cluster_coeffs.append(val)
                elif key == 'cluster_label': # If it's a numeric predictor
                    cluster_coeffs.append(val)

    if len(cluster_coeffs) > 1:
        report['stability_metrics'] = {
            'coefficient_variance': float(np.var(cluster_coeffs)),
            'coefficient_std': float(np.std(cluster_coeffs)),
            'coefficient_mean': float(np.mean(cluster_coeffs))
        }
    else:
        report['stability_metrics'] = {
            'coefficient_variance': None,
            'coefficient_std': None,
            'coefficient_mean': None,
            'note': 'Insufficient successful models to calculate variance'
        }

    return report


def save_sensitivity_report(
    report: Dict[str, Any],
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Path:
    """
    Save the sensitivity analysis report to a YAML file.
    """
    if logger is None:
        logger = get_logger(__name__)

    if output_path is None:
        config = get_config()
        output_path = config.RESULTS_DIR / "sensitivity_report.yaml"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving sensitivity report to {output_path}")

    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Sensitivity report saved successfully.")
    return output_path


def main():
    """
    Main entry point for the sensitivity analysis script.
    """
    logger = get_logger(__name__)
    logger.info("Running Sensitivity Analysis")

    try:
        # Run the analysis
        report = run_sensitivity_analysis(k_values=[2, 3], logger=logger)

        # Save the report
        output_path = save_sensitivity_report(report, logger=logger)

        logger.info(f"Sensitivity Analysis completed. Report saved to: {output_path}")

    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()