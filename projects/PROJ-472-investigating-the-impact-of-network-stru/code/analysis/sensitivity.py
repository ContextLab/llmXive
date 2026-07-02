"""
Sensitivity Analysis for Neural Avalanche Dynamics.

Implements a sweep across a range of amplitude thresholds to test the
robustness of the power-law exponent (tau) against threshold variations.
This addresses FR-008: "Sensitivity analysis sweep across a range of thresholds".
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Local imports based on project API surface
from config import get_data_root
from utils.logger import get_logger, handle_exceptions
from analysis.fitting import fit_power_law_model, load_avalanche_sizes_from_store
from analysis.avalanches import detect_avalanches, calculate_threshold, z_score_normalize

logger = get_logger(__name__)

# Constants for sensitivity analysis
DEFAULT_THRESHOLD_MIN = 0.5  # Lower bound as fraction of baseline threshold
DEFAULT_THRESHOLD_MAX = 2.5  # Upper bound as fraction of baseline threshold
DEFAULT_NUM_STEPS = 20       # Number of steps in the sweep
DEFAULT_OUTPUT_FILE = "data/results/sensitivity_analysis.csv"
DEFAULT_PLOT_FILE = "figures/sensitivity_sweep.png"


@handle_exceptions
def calculate_threshold_multiplier_range(
    min_mult: float = DEFAULT_THRESHOLD_MIN,
    max_mult: float = DEFAULT_THRESHOLD_MAX,
    num_steps: int = DEFAULT_NUM_STEPS
) -> List[float]:
    """
    Generate a list of threshold multipliers for the sensitivity sweep.

    Args:
        min_mult: Minimum multiplier relative to the baseline threshold.
        max_mult: Maximum multiplier relative to the baseline threshold.
        num_steps: Number of steps in the sweep.

    Returns:
        List of multipliers.
    """
    return np.linspace(min_mult, max_mult, num_steps).tolist()


@handle_exceptions
def run_sensitivity_sweep_for_subject(
    subject_id: str,
    eeg_data: np.ndarray,
    threshold_multipliers: List[float],
    baseline_threshold_percentile: float = 90.0
) -> Dict[str, Any]:
    """
    Run the sensitivity sweep for a single subject.

    For each multiplier, the baseline threshold is adjusted, avalanches are
    detected, and the power-law exponent (tau) is fitted.

    Args:
        subject_id: Unique identifier for the subject.
        eeg_data: 2D numpy array (channels x time) of z-scored EEG data.
        threshold_multipliers: List of multipliers to apply to the baseline threshold.
        baseline_threshold_percentile: Percentile used to calculate the baseline threshold.

    Returns:
        Dictionary containing results for each multiplier.
    """
    results = []
    
    # Calculate baseline threshold once
    baseline_thresh = calculate_threshold(eeg_data, percentile=baseline_threshold_percentile)
    
    logger.info(f"Subject {subject_id}: Baseline threshold = {baseline_thresh:.4f}")

    for mult in threshold_multipliers:
        current_thresh = baseline_thresh * mult
        
        try:
            # Detect avalanches with the modified threshold
            avalanche_sizes = detect_avalanches(eeg_data, threshold=current_thresh)
            
            if len(avalanche_sizes) < 10:
                # Not enough data for fitting
                logger.warning(f"Subject {subject_id}: Insufficient avalanches ({len(avalanche_sizes)}) at multiplier {mult:.2f}")
                tau = np.nan
                n_avalanches = len(avalanche_sizes)
                p_value = np.nan
                is_power_law = False
            else:
                # Fit power law
                fit_result = fit_power_law_model(avalanche_sizes)
                tau = fit_result.get('tau', np.nan)
                p_value = fit_result.get('p_value', np.nan)
                is_power_law = fit_result.get('is_power_law', False)
                n_avalanches = len(avalanche_sizes)

            results.append({
                'subject_id': subject_id,
                'threshold_multiplier': mult,
                'absolute_threshold': current_thresh,
                'n_avalanches': n_avalanches,
                'tau': tau,
                'p_value': p_value,
                'is_power_law': is_power_law
            })

        except Exception as e:
            logger.error(f"Subject {subject_id}: Error at multiplier {mult}: {e}")
            results.append({
                'subject_id': subject_id,
                'threshold_multiplier': mult,
                'absolute_threshold': current_thresh,
                'n_avalanches': 0,
                'tau': np.nan,
                'p_value': np.nan,
                'is_power_law': False
            })

    return results


@handle_exceptions
def load_processed_eeg_for_subject(subject_id: str, data_root: Path) -> np.ndarray:
    """
    Load z-scored EEG data for a subject from the store.
    
    Args:
        subject_id: Subject identifier.
        data_root: Root path for data directories.
        
    Returns:
        2D numpy array (channels x time).
    """
    # Construct path based on project conventions (data/processed)
    file_path = data_root / "processed" / f"{subject_id}_eeg_zscored.csv"
    
    if not file_path.exists():
        # Fallback to checking data/results if processed doesn't exist yet
        file_path = data_root / "results" / f"{subject_id}_eeg_zscored.csv"
        
    if not file_path.exists():
        raise FileNotFoundError(f"Z-scored EEG data not found for {subject_id} at {file_path}")

    df = pd.read_csv(file_path)
    # Assuming first column is time, rest are channels
    # Or if it's just channels x time, handle accordingly.
    # Standardizing to: rows = channels, cols = time
    data = df.values
    if data.shape[0] == 1:
        data = data.T # Transpose if stored as 1xT
    return data


@handle_exceptions
def run_sensitivity_pipeline(
    subject_ids: Optional[List[str]] = None,
    min_mult: float = DEFAULT_THRESHOLD_MIN,
    max_mult: float = DEFAULT_THRESHOLD_MAX,
    num_steps: int = DEFAULT_NUM_STEPS,
    data_root: Optional[Path] = None,
    output_csv: Optional[Path] = None,
    output_plot: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run the full sensitivity analysis pipeline for all available subjects.

    Args:
        subject_ids: List of subject IDs to process. If None, discovers all valid subjects.
        min_mult: Minimum threshold multiplier.
        max_mult: Maximum threshold multiplier.
        num_steps: Number of steps in the sweep.
        data_root: Root directory for data. Defaults to config root.
        output_csv: Path to save the results CSV.
        output_plot: Path to save the sensitivity plot.

    Returns:
        DataFrame containing sensitivity analysis results.
    """
    if data_root is None:
        data_root = get_data_root()

    # Ensure output directories exist
    if output_csv is None:
        output_csv = Path(get_data_root()) / DEFAULT_OUTPUT_FILE
    else:
        output_csv = Path(output_csv)
        
    if output_plot is None:
        output_plot = Path(get_data_root()).parent / "figures" / DEFAULT_PLOT_FILE
    else:
        output_plot = Path(output_plot)
        
    output_plot.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting sensitivity analysis sweep from {min_mult} to {max_mult} ({num_steps} steps)")
    
    # Discover subjects if not provided
    if subject_ids is None:
        # Look for files in data/processed or data/results
        processed_dir = data_root / "processed"
        results_dir = data_root / "results"
        
        candidates = set()
        for d in [processed_dir, results_dir]:
            if d.exists():
                for f in d.glob("*_eeg_zscored.csv"):
                    # Extract subject ID (remove suffix)
                    sub_id = f.stem.replace("_eeg_zscored", "")
                    candidates.add(sub_id)
        subject_ids = sorted(list(candidates))
        
    if not subject_ids:
        logger.error("No subjects found for sensitivity analysis.")
        raise ValueError("No subjects found for sensitivity analysis.")

    logger.info(f"Processing {len(subject_ids)} subjects: {subject_ids}")

    threshold_multipliers = calculate_threshold_multiplier_range(min_mult, max_mult, num_steps)
    all_results = []

    for sub_id in subject_ids:
        logger.info(f"Processing subject: {sub_id}")
        try:
            eeg_data = load_processed_eeg_for_subject(sub_id, data_root)
            subject_results = run_sensitivity_sweep_for_subject(
                sub_id, 
                eeg_data, 
                threshold_multipliers
            )
            all_results.extend(subject_results)
        except FileNotFoundError as e:
            logger.warning(str(e))
        except Exception as e:
            logger.error(f"Failed to process subject {sub_id}: {e}")
            continue

    # Create DataFrame
    df_results = pd.DataFrame(all_results)
    
    if df_results.empty:
        logger.warning("Sensitivity analysis produced no results.")
        df_results.to_csv(output_csv, index=False)
        return df_results

    # Save CSV
    df_results.to_csv(output_csv, index=False)
    logger.info(f"Sensitivity results saved to {output_csv}")

    # Generate Plot
    plot_sensitivity_results(df_results, output_plot)

    return df_results


@handle_exceptions
def plot_sensitivity_results(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot the sensitivity of tau against threshold multipliers.

    Args:
        df: DataFrame with sensitivity results.
        output_path: Path to save the plot.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    subjects = df['subject_id'].unique()
    
    # Color map
    cmap = plt.get_cmap('tab10')
    colors = {sub: cmap(i % 10) for i, sub in enumerate(subjects)}

    for sub_id in subjects:
        sub_data = df[df['subject_id'] == sub_id]
        # Filter out NaN taus for plotting
        valid = sub_data[~sub_data['tau'].isna()]
        
        if len(valid) > 1:
            ax.plot(
                valid['threshold_multiplier'], 
                valid['tau'], 
                marker='o', 
                label=sub_id, 
                color=colors[sub_id],
                alpha=0.7
            )

    # Add a horizontal line at the median tau if possible
    median_tau = df['tau'].median()
    if not np.isnan(median_tau):
        ax.axhline(y=median_tau, color='black', linestyle='--', linewidth=1.5, label=f'Median Tau ({median_tau:.2f})')

    ax.set_xlabel('Threshold Multiplier (relative to baseline)', fontsize=12)
    ax.set_ylabel('Power-Law Exponent (Tau)', fontsize=12)
    ax.set_title('Sensitivity of Avalanche Exponent to Threshold Variation', fontsize=14)
    ax.legend(title='Subject ID', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax.set_xlim([df['threshold_multiplier'].min(), df['threshold_multiplier'].max()])
    
    # Annotate robustness
    # If the lines are relatively flat, the system is robust.
    # Calculate slope variance as a metric
    slopes = []
    for sub_id in subjects:
        sub_data = df[df['subject_id'] == sub_id]
        valid = sub_data[~sub_data['tau'].isna()]
        if len(valid) > 1:
            # Simple linear regression slope
            x = valid['threshold_multiplier'].values
            y = valid['tau'].values
            if len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]
                slopes.append(slope)
    
    if slopes:
        avg_slope = np.mean(slopes)
        ax.text(
            0.05, 0.95, 
            f'Avg Slope: {avg_slope:.4f}', 
            transform=ax.transAxes, 
            fontsize=10, 
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")


def main():
    """Entry point for the sensitivity analysis script."""
    logger.info("Starting Sensitivity Analysis Pipeline (T022)")
    
    try:
        # Run the pipeline with defaults
        df = run_sensitivity_pipeline()
        
        if not df.empty:
            logger.info(f"Analysis complete. Processed {df['subject_id'].nunique()} subjects.")
            logger.info(f"Results summary:\n{df.describe()}")
        else:
            logger.warning("Pipeline completed but no data was processed.")
            
    except Exception as e:
        logger.critical(f"Sensitivity analysis pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()