"""
Robustness analysis for User Story 3: Modality-Specific Correlation Analysis.

This module runs the Phase 3 correlation pipeline on each modality subset
(visual and auditory) independently to test modality-specificity of the
relationship between metacognitive awareness and reality testing accuracy.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# Import from local modules
from code.config.env_config import load_config, setup_logging, get_seed
from code.src.analysis.correlation import compute_hold_out_metrics
from code.src.analysis.bootstrap import run_bootstrap_analysis

logger = logging.getLogger(__name__)

def load_filtered_data(modality: str, base_dir: Path) -> pd.DataFrame:
    """
    Load filtered trial data for a specific modality.

    Args:
        modality: The modality to filter by ('visual' or 'auditory')
        base_dir: Base directory for data files

    Returns:
        DataFrame containing filtered trial data
    """
    input_file = base_dir / f"{modality}_trials.csv"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Filtered data file not found: {input_file}. "
            f"Ensure T026 (filter.py) has completed successfully."
        )

    logger.info(f"Loading {modality} trials from {input_file}")
    df = pd.read_csv(input_file)

    # Validate required columns
    required_cols = [
        'participant_id', 'trial_id', 'stimulus_modality',
        'source_label', 'participant_response', 'confidence_rating'
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {modality}_trials.csv: {missing_cols}"
        )

    logger.info(f"Loaded {len(df)} trials for {modality} modality")
    return df

def compute_hold_out_metrics_for_modality(
    df: pd.DataFrame,
    train_ratio: float = 0.7
) -> Dict[str, Any]:
    """
    Compute hold-out metrics for a single modality subset.

    Args:
        df: DataFrame with trial data for one modality
        train_ratio: Ratio of data to use for training (metacognitive score)

    Returns:
        Dictionary with d_prime, criterion, type2_auc, and other metrics
    """
    logger.info(f"Computing hold-out metrics for modality with {len(df)} trials")

    if len(df) < 10:
        logger.warning(f"Insufficient trials ({len(df)}) for reliable analysis")
        return {
            'd_prime': np.nan,
            'criterion': np.nan,
            'type2_auc': np.nan,
            'n_trials': len(df),
            'n_participants': df['participant_id'].nunique() if 'participant_id' in df.columns else 0
        }

    # Use the existing hold-out metrics computation
    results = compute_hold_out_metrics(df, train_ratio=train_ratio)
    return results

def run_bootstrap_correlation(
    modality_results: Dict[str, Dict[str, Any]],
    n_resamples: int = 1000,
    timeout_hours: float = 5.5
) -> Dict[str, Any]:
    """
    Run bootstrap correlation analysis for each modality.

    Args:
        modality_results: Dictionary with results for each modality
        n_resamples: Number of bootstrap resamples
        timeout_hours: Maximum runtime in hours before reducing resamples

    Returns:
        Dictionary with bootstrap results for each modality
    """
    start_time = time.time()
    logger.info(f"Starting bootstrap correlation with {n_resamples} resamples")

    bootstrap_results = {}

    for modality, results in modality_results.items():
        logger.info(f"Running bootstrap for {modality} modality...")

        # Check runtime
        elapsed = time.time() - start_time
        if elapsed > timeout_hours * 3600:
            logger.warning(
                f"Runtime limit detected ({elapsed/3600:.1f}h > {timeout_hours}h). "
                f"Reducing bootstrap count to 500 for remaining modalities."
            )
            current_resamples = 500
        else:
            current_resamples = n_resamples

        # Prepare data for bootstrap
        # We need to create a dataset where we can resample participants
        participant_ids = results.get('participant_ids', [])
        if not participant_ids:
            # Fallback: create synthetic participant data from trial-level metrics
            participant_ids = list(set(results.get('participant_id', [])))

        # Run bootstrap analysis
        try:
            bootstrap_output = run_bootstrap_analysis(
                results=results,
                n_resamples=current_resamples
            )
            bootstrap_results[modality] = bootstrap_output
        except Exception as e:
            logger.error(f"Bootstrap failed for {modality}: {e}")
            bootstrap_results[modality] = {
                'error': str(e),
                'correlation': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'p_value': np.nan
            }

        # Check runtime again
        elapsed = time.time() - start_time
        if elapsed > timeout_hours * 3600 and current_resamples == n_resamples:
            logger.warning(
                f"Runtime limit exceeded during {modality} bootstrap. "
                f"Will use reduced count for subsequent modalities."
            )

    return bootstrap_results

def write_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write robustness analysis results to JSON file.

    Args:
        results: Dictionary containing analysis results
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results written to {output_path}")

def run_robustness_analysis(
    config: Any = None,
    base_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run the robustness analysis pipeline.

    Args:
        config: Configuration object (optional)
        base_dir: Base directory for data files (optional)
        output_dir: Output directory for results (optional)

    Returns:
        Dictionary with complete analysis results
    """
    # Load configuration
    if config is None:
        config = load_config()

    # Set up directories
    if base_dir is None:
        base_dir = Path(config.get("paths", {}).get("derived", "data/derived"))
    if output_dir is None:
        output_dir = Path(config.get("paths", {}).get("results", "data/results"))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get analysis parameters
    n_resamples = config.get("analysis", {}).get("bootstrap_count", 1000)
    train_ratio = config.get("analysis", {}).get("train_test_split", 0.7)

    logger.info(f"Starting robustness analysis with {n_resamples} bootstrap resamples")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Process each modality
    modalities = ['visual', 'auditory']
    modality_results = {}
    final_results = {
        'analysis_type': 'modality_specific_robustness',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'n_resamples': n_resamples,
        'train_ratio': train_ratio,
        'modalities': {}
    }

    for modality in modalities:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {modality} modality")
        logger.info(f"{'='*60}")

        try:
            # Load filtered data
            df = load_filtered_data(modality, base_dir)

            # Compute hold-out metrics
            metrics = compute_hold_out_metrics_for_modality(df, train_ratio)
            modality_results[modality] = metrics

            final_results['modalities'][modality] = {
                'n_trials': len(df),
                'n_participants': df['participant_id'].nunique() if 'participant_id' in df.columns else 0,
                'd_prime': metrics.get('d_prime', np.nan),
                'criterion': metrics.get('criterion', np.nan),
                'type2_auc': metrics.get('type2_auc', np.nan),
                'correlation': metrics.get('correlation', np.nan),
                'correlation_p': metrics.get('correlation_p', np.nan),
                'status': 'success'
            }

            logger.info(f"{modality}: d'={metrics.get('d_prime', np.nan):.3f}, "
                        f"AUC={metrics.get('type2_auc', np.nan):.3f}, "
                        f"r={metrics.get('correlation', np.nan):.3f}")

        except FileNotFoundError as e:
            logger.error(f"Data not found for {modality}: {e}")
            final_results['modalities'][modality] = {
                'error': str(e),
                'status': 'data_not_found'
            }
        except Exception as e:
            logger.error(f"Error processing {modality} modality: {e}")
            final_results['modalities'][modality] = {
                'error': str(e),
                'status': 'error'
            }

    # Run bootstrap correlation across modalities
    if all(modality_results.get(m, {}).get('status') != 'error' for m in modalities):
        logger.info("\nRunning bootstrap correlation analysis...")
        bootstrap_results = run_bootstrap_correlation(modality_results, n_resamples)

        # Add bootstrap results to final output
        for modality, boot_res in bootstrap_results.items():
            if modality in final_results['modalities']:
                final_results['modalities'][modality].update({
                    'bootstrap': {
                        'correlation': boot_res.get('correlation', np.nan),
                        'ci_lower': boot_res.get('ci_lower', np.nan),
                        'ci_upper': boot_res.get('ci_upper', np.nan),
                        'p_value': boot_res.get('p_value', np.nan),
                        'n_resamples': boot_res.get('n_resamples', 0)
                    }
                })

    # Write results
    output_path = output_dir / 'robustness_analysis.json'
    write_results(final_results, output_path)

    logger.info(f"\nRobustness analysis complete. Results saved to {output_path}")

    return final_results

def main():
    """Main entry point for robustness analysis."""
    # Set up logging
    logger = setup_logging()
    get_seed()

    logger.info("Starting robustness analysis (T027)")

    try:
        # Run the analysis
        results = run_robustness_analysis()

        # Check for errors
        error_count = sum(
            1 for m in results.get('modalities', {}).values()
            if m.get('status') in ['error', 'data_not_found']
        )

        if error_count > 0:
            logger.warning(f"Analysis completed with {error_count} errors")
            sys.exit(0)  # Exit successfully but with warnings
        else:
            logger.info("All modalities processed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error in robustness analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
