"""
Sensitivity analysis module for p-value threshold sensitivity.

This module implements FR-009: p-value threshold sensitivity analysis.
It evaluates how the correlation results change across different significance
thresholds (0.01, 0.05, 0.1) to assess the robustness of findings.

The analysis is stratified by perovskite chemistry class (oxide, halide, nitride)
as established in the stratify module.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

from src.analysis.correlation import compute_correlation_matrix, apply_benjamini_hochberg
from src.analysis.stratify import stratify_dataframe, classify_chemistry


def setup_logger_module(name: str = __name__) -> logging.Logger:
    """Setup a logger for this module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def run_sensitivity_analysis(
    df: pd.DataFrame,
    descriptors: List[str],
    target: str = 'thermal_conductivity_normalized',
    thresholds: Optional[List[float]] = None,
    stratify_by: Optional[str] = 'chemistry_class',
    method: str = 'spearman'
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different p-value thresholds.

    This function evaluates the stability of correlation results by testing
    multiple significance thresholds. It returns a comprehensive report showing
    which correlations remain significant across thresholds.

    Args:
        df: Input dataframe with descriptors and target variable.
        descriptors: List of descriptor column names to analyze.
        target: Name of the target variable column.
        thresholds: List of p-value thresholds to test. Defaults to [0.01, 0.05, 0.1].
        stratify_by: Column name for stratification. If None, analyzes entire dataset.
        method: Correlation method ('pearson' or 'spearman').

    Returns:
        Dictionary containing:
            - 'thresholds': List of thresholds tested
            - 'results': Dict mapping each threshold to correlation results
            - 'summary': Summary of stable correlations across thresholds
            - 'metadata': Analysis metadata
    """
    logger = setup_logger_module()
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")

    if thresholds is None:
        thresholds = [0.01, 0.05, 0.1]

    # Validate inputs
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataframe")

    missing_descriptors = [d for d in descriptors if d not in df.columns]
    if missing_descriptors:
        raise ValueError(f"Missing descriptor columns: {missing_descriptors}")

    # Prepare data
    valid_cols = [target] + descriptors
    analysis_df = df[valid_cols].dropna()

    if len(analysis_df) < 3:
        raise ValueError("Insufficient samples for correlation analysis after dropping NaNs")

    results = {}

    # Stratify if requested
    if stratify_by and stratify_by in analysis_df.columns:
        logger.info(f"Stratifying by {stratify_by}")
        groups = analysis_df[stratify_by].unique()
        stratified_results = {}

        for group in groups:
            group_df = analysis_df[analysis_df[stratify_by] == group]
            logger.info(f"  Processing group: {group} (n={len(group_df)})")

            if len(group_df) < 3:
                logger.warning(f"  Skipping group {group}: insufficient samples")
                continue

            group_results = {}
            for threshold in thresholds:
                corr_results = _compute_thresholded_correlations(
                    group_df, descriptors, target, threshold, method
                )
                group_results[threshold] = corr_results

            stratified_results[group] = group_results

        results = {'stratified': stratified_results}

    else:
        # Global analysis
        logger.info("Performing global analysis (no stratification)")
        for threshold in thresholds:
            corr_results = _compute_thresholded_correlations(
                analysis_df, descriptors, target, threshold, method
            )
            results[threshold] = corr_results

    # Generate summary
    summary = _generate_sensitivity_summary(results, thresholds)

    return {
        'thresholds': thresholds,
        'results': results,
        'summary': summary,
        'metadata': {
            'n_samples': len(analysis_df),
            'n_descriptors': len(descriptors),
            'method': method,
            'stratified': stratify_by is not None,
            'stratify_column': stratify_by
        }
    }


def _compute_thresholded_correlations(
    df: pd.DataFrame,
    descriptors: List[str],
    target: str,
    threshold: float,
    method: str = 'spearman'
) -> Dict[str, Any]:
    """
    Compute correlations with a specific p-value threshold.

    Args:
        df: Input dataframe.
        descriptors: List of descriptor columns.
        target: Target variable column.
        threshold: P-value threshold for significance.
        method: Correlation method.

    Returns:
        Dictionary with correlation results at this threshold.
    """
    # Compute full correlation matrix
    corr_matrix, p_matrix = compute_correlation_matrix(
        df, descriptors + [target], method=method
    )

    # Apply Benjamini-Hochberg correction
    corrected_p_matrix = apply_benjamini_hochberg(p_matrix)

    # Extract correlations with target
    target_idx = len(descriptors)  # target is last column
    correlations = {}

    significant_pairs = []
    non_significant_pairs = []

    for i, desc in enumerate(descriptors):
        corr_val = corr_matrix.iloc[i, target_idx]
        p_val = corrected_p_matrix.iloc[i, target_idx]
        is_significant = p_val < threshold

        correlations[desc] = {
            'correlation': float(corr_val),
            'p_value': float(p_val),
            'significant': is_significant,
            'threshold': threshold
        }

        if is_significant:
            significant_pairs.append({
                'descriptor': desc,
                'correlation': float(corr_val),
                'p_value': float(p_val)
            })
        else:
            non_significant_pairs.append({
                'descriptor': desc,
                'correlation': float(corr_val),
                'p_value': float(p_val)
            })

    return {
        'threshold': threshold,
        'correlations': correlations,
        'significant_count': len(significant_pairs),
        'non_significant_count': len(non_significant_pairs),
        'significant_pairs': significant_pairs,
        'non_significant_pairs': non_significant_pairs,
        'full_corr_matrix': corr_matrix,
        'full_p_matrix': corrected_p_matrix
    }


def _generate_sensitivity_summary(
    results: Dict[str, Any],
    thresholds: List[float]
) -> Dict[str, Any]:
    """
    Generate a summary of stability across thresholds.

    Identifies correlations that remain significant across multiple thresholds
    and those that are threshold-sensitive.
    """
    summary = {
        'stable_significant': [],  # Significant at all thresholds
        'threshold_sensitive': [],  # Significant at some but not all
        'always_non_significant': [],  # Never significant
        'stability_scores': {}  # Fraction of thresholds where significant
    }

    # Get descriptors from first threshold result
    first_threshold = thresholds[0]
    if 'stratified' in results:
        # Handle stratified results
        for group, group_results in results['stratified'].items():
            if not group_results:
                continue

            # Get descriptors from first available threshold
            available_thresholds = [t for t in thresholds if t in group_results]
            if not available_thresholds:
                continue

            first_t = available_thresholds[0]
            descriptors = list(group_results[first_t]['correlations'].keys())

            group_summary = {
                'stable_significant': [],
                'threshold_sensitive': [],
                'always_non_significant': [],
                'stability_scores': {}
            }

            for desc in descriptors:
                significant_at = []
                for t in thresholds:
                    if t in group_results:
                        if desc in group_results[t]['correlations']:
                            if group_results[t]['correlations'][desc]['significant']:
                                significant_at.append(t)

                stability = len(significant_at) / len(thresholds)
                group_summary['stability_scores'][desc] = stability

                if len(significant_at) == len(thresholds):
                    group_summary['stable_significant'].append(desc)
                elif len(significant_at) > 0:
                    group_summary['threshold_sensitive'].append(desc)
                else:
                    group_summary['always_non_significant'].append(desc)

            summary[f'stratum_{group}'] = group_summary

    else:
        # Handle global results
        if not results:
            return summary

        available_thresholds = [t for t in thresholds if t in results]
        if not available_thresholds:
            return summary

        first_t = available_thresholds[0]
        descriptors = list(results[first_t]['correlations'].keys())

        for desc in descriptors:
            significant_at = []
            for t in thresholds:
                if t in results:
                    if desc in results[t]['correlations']:
                        if results[t]['correlations'][desc]['significant']:
                            significant_at.append(t)

            stability = len(significant_at) / len(thresholds)
            summary['stability_scores'][desc] = stability

            if len(significant_at) == len(thresholds):
                summary['stable_significant'].append(desc)
            elif len(significant_at) > 0:
                summary['threshold_sensitive'].append(desc)
            else:
                summary['always_non_significant'].append(desc)

    return summary


def save_sensitivity_report(
    sensitivity_results: Dict[str, Any],
    output_path: Union[str, Path]
) -> Path:
    """
    Save sensitivity analysis results to a JSON file.

    Args:
        sensitivity_results: Results from run_sensitivity_analysis.
        output_path: Path to save the JSON report.

    Returns:
        Path to the saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj

    serializable_results = convert_numpy(sensitivity_results)

    import json
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)

    logging.getLogger(__name__).info(f"Saved sensitivity report to {output_path}")
    return output_path


def main():
    """
    Main entry point for sensitivity analysis.

    This function:
    1. Loads cleaned data from data/cleaned/merged_perovskite.csv
    2. Computes descriptors if not already present
    3. Stratifies by chemistry class
    4. Runs sensitivity analysis across p-value thresholds
    5. Saves results to data/results/sensitivity_analysis.json
    """
    logger = setup_logger_module()
    logger.info("Starting sensitivity analysis pipeline")

    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    cleaned_data_path = project_root / 'data' / 'cleaned' / 'merged_perovskite.csv'
    output_path = project_root / 'data' / 'results' / 'sensitivity_analysis.json'

    # Load data
    if not cleaned_data_path.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {cleaned_data_path}. "
            "Please run the data ingestion pipeline first."
        )

    logger.info(f"Loading data from {cleaned_data_path}")
    df = pd.read_csv(cleaned_data_path)

    # Ensure normalized thermal conductivity exists
    if 'thermal_conductivity_normalized' not in df.columns:
        if 'thermal_conductivity' in df.columns:
            df['thermal_conductivity_normalized'] = df['thermal_conductivity']
            logger.warning("Using raw thermal conductivity as normalized (no normalization applied)")
        else:
            raise ValueError("Neither 'thermal_conductivity_normalized' nor 'thermal_conductivity' found in data")

    # Ensure chemistry class exists (from stratify step)
    if 'chemistry_class' not in df.columns:
        logger.info("Adding chemistry_class column via classification")
        df['chemistry_class'] = df.apply(
            lambda row: classify_chemistry(row), axis=1
        )

    # Define descriptors (from compute_descriptors step)
    descriptors = [
        'tolerance_factor',
        'octahedral_tilting_angle',
        'bond_length_variance',
        'unit_cell_volume'
    ]

    # Verify descriptors exist
    missing = [d for d in descriptors if d not in df.columns]
    if missing:
        logger.warning(f"Missing descriptors: {missing}. Attempting to compute...")
        # In a full pipeline, we would compute these here
        # For now, we raise an error if they're missing
        raise ValueError(
            f"Required descriptors not found: {missing}. "
            "Please run the descriptor computation pipeline first."
        )

    # Run sensitivity analysis
    logger.info("Running sensitivity analysis")
    results = run_sensitivity_analysis(
        df=df,
        descriptors=descriptors,
        target='thermal_conductivity_normalized',
        thresholds=[0.01, 0.05, 0.1],
        stratify_by='chemistry_class',
        method='spearman'
    )

    # Save results
    logger.info(f"Saving results to {output_path}")
    save_sensitivity_report(results, output_path)

    # Print summary
    logger.info("Sensitivity Analysis Summary:")
    logger.info(f"  Samples analyzed: {results['metadata']['n_samples']}")
    logger.info(f"  Descriptors: {results['metadata']['n_descriptors']}")

    if 'stratum_oxide' in results['summary']:
        ox_summary = results['summary']['stratum_oxide']
        logger.info(f"  Oxide class - Stable significant: {ox_summary['stable_significant']}")

    if 'stratum_halide' in results['summary']:
        hal_summary = results['summary']['stratum_halide']
        logger.info(f"  Halide class - Stable significant: {hal_summary['stable_significant']}")

    logger.info("Sensitivity analysis complete")

    return results


if __name__ == '__main__':
    main()
