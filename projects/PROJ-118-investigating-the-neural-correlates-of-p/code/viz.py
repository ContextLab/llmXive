"""
Visualization module for US3: Generate and save ERP plots and topographic maps.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import mne
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server execution
import matplotlib.pyplot as plt
from scipy import stats

from config_loader import get_project_root, get_config, ensure_directory
from extract import load_epochs, get_subject_epochs_paths

logger = logging.getLogger(__name__)

def load_metrics() -> pd.DataFrame:
    """Load metrics from results/metrics.csv."""
    metrics_path = get_project_root() / "results" / "metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return pd.read_csv(metrics_path)

def calculate_prevalence(metrics_df: pd.DataFrame) -> float:
    """Calculate the proportion of participants with peak_detected=true."""
    if 'peak_detected' not in metrics_df.columns:
        logger.warning("Column 'peak_detected' not found in metrics. Assuming all valid.")
        return 1.0
    # Ensure boolean handling
    valid_flags = metrics_df['peak_detected'].astype(str).str.lower().isin(['true', '1', 'yes'])
    return float(valid_flags.sum() / len(metrics_df)) if len(metrics_df) > 0 else 0.0

def plot_grand_average_erp(metrics_df: pd.DataFrame, save_path: Optional[Path] = None) -> None:
    """
    Generate grand-average ERP plots (Standard, Deviant, Difference) with 95% CI.
    Loads processed epochs from data/processed/epo_raw.fif.
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    epochs_file = processed_dir / "epo_raw.fif"

    if not epochs_file.exists():
        raise FileNotFoundError(f"Required epochs file not found: {epochs_file}")

    logger.info(f"Loading epochs from {epochs_file}")
    epochs = mne.read_epochs(epochs_file, verbose=False)

    # Check for required conditions
    if 'standard' not in epochs or 'deviant' not in epochs:
        available = list(epochs.event_id.keys()) if hasattr(epochs, 'event_id') else list(epochs.ch_names)
        raise ValueError(f"Expected 'standard' and 'deviant' conditions in epochs. Found: {available}")

    # Select electrodes Fz and FCz
    ch_names = ['Fz', 'FCz']
    missing_chs = [ch for ch in ch_names if ch not in epochs.ch_names]
    if missing_chs:
        logger.warning(f"Channels {missing_chs} not found in epochs. Using all available channels.")
        ch_names = epochs.ch_names

    # Compute averages
    evoked_std = epochs['standard'].average()
    evoked_dev = epochs['deviant'].average()
    
    # Create difference wave manually by subtracting evoked objects
    # MNE Evoked subtraction
    evoked_diff = evoked_dev.copy()
    evoked_diff.data = evoked_dev.data - evoked_std.data
    evoked_diff.comment = "Deviant - Standard"

    # Prepare data for plotting (mean across channels if multiple selected, or plot each)
    # We will plot Fz specifically as primary MMN site
    target_ch = 'Fz' if 'Fz' in epochs.ch_names else epochs.ch_names[0]
    
    # Extract time and data for the target channel
    times = evoked_std.times
    idx = evoked_std.ch_names.index(target_ch)
    
    data_std = evoked_std.data[idx]
    data_dev = evoked_dev.data[idx]
    data_diff = evoked_diff.data[idx]

    # Calculate 95% CI (assuming subjects are averaged in the epochs object already? 
    # Note: The current pipeline loads epo_raw.fif which might contain all subjects concatenated.
    # If epo_raw.fif is a single Evoked (grand average), we cannot compute CI from it directly.
    # However, the task implies we have subject-level data to compute CI.
    # If epochs is a Epochs object, we need to average per subject first.
    # Since T018 outputs 'epo_raw.fif', let's assume it's an Epochs object containing all subjects.
    # We need to group by subject if possible, or if not, we can't compute CI properly without raw subject separation.
    # Given the constraints and typical MNE output, if 'subject' info is in metadata, we use that.
    # If not, and we only have one Evoked, we skip CI or use bootstrapping (too complex for this task).
    # Let's assume we can iterate subjects if metadata exists.
    
    # Fallback: If we can't separate subjects easily, we plot the single grand average with shaded error 
    # based on the standard error of the mean across trials (not subjects) if available, 
    # but true CI requires subject-level means.
    # For this implementation, we will attempt to group by subject ID if present in info['subject'].
    
    subject_ids = []
    if epochs.metadata is not None and 'subject' in epochs.metadata.columns:
        subject_ids = epochs.metadata['subject'].unique()
    
    if len(subject_ids) > 1:
        # Compute subject-level averages
        subject_means = []
        for sub in subject_ids:
            sub_epo = epochs[epochs.metadata['subject'] == sub]
            ev_sub = sub_epo['standard'].average()
            ev_dev_sub = sub_epo['deviant'].average()
            # Difference
            ev_diff_sub = ev_dev_sub.copy()
            ev_diff_sub.data = ev_dev_sub.data - ev_sub.data
            subject_means.append(ev_diff_sub.data[idx])
        
        subject_means = np.array(subject_means)
        mean_diff = np.mean(subject_means, axis=0)
        std_diff = np.std(subject_means, axis=0)
        n = len(subject_ids)
        sem_diff = std_diff / np.sqrt(n)
        ci_95 = 1.96 * sem_diff
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.fill_between(times, mean_diff - ci_95, mean_diff + ci_95, alpha=0.2, label='95% CI')
        ax.plot(times, mean_diff, label='Difference Wave (Fz)', color='black', linewidth=2)
        
        # Also plot Standard and Deviant if needed, but focus on difference for MMN
        # Let's plot all three for completeness
        # Re-calculate for standard and deviant
        std_means = []
        dev_means = []
        for sub in subject_ids:
            sub_epo = epochs[epochs.metadata['subject'] == sub]
            ev_sub = sub_epo['standard'].average()
            ev_dev_sub = sub_epo['deviant'].average()
            std_means.append(ev_sub.data[idx])
            dev_means.append(ev_dev_sub.data[idx])
        
        std_means = np.array(std_means)
        dev_means = np.array(dev_means)
        
        mean_std = np.mean(std_means, axis=0)
        mean_dev = np.mean(dev_means, axis=0)
        
        ax.plot(times, mean_std, label='Standard', color='blue', linestyle='--')
        ax.plot(times, mean_dev, label='Deviant', color='red', linestyle='--')
        
        ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude (µV)')
        ax.set_title(f'Grand Average ERP at {target_ch} (n={n} subjects)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    else:
        # Fallback if no subject separation: just plot the average
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(times, data_std, label='Standard', color='blue')
        ax.plot(times, data_dev, label='Deviant', color='red')
        ax.plot(times, data_diff, label='Difference', color='black', linewidth=2)
        ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude (µV)')
        ax.set_title(f'Grand Average ERP at {target_ch}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        logger.warning("Could not compute 95% CI across subjects. Plotting grand average only.")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved ERP plot to {save_path}")
    plt.close()

def plot_topomap_at_peak(metrics_df: pd.DataFrame, save_path: Optional[Path] = None) -> None:
    """
    Generate topographic map of the MMN difference (Deviant - Standard) at peak latency.
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    epochs_file = processed_dir / "epo_raw.fif"

    if not epochs_file.exists():
        raise FileNotFoundError(f"Required epochs file not found: {epochs_file}")

    if metrics_df.empty:
        raise ValueError("Metrics DataFrame is empty. Cannot determine peak latency.")

    # Filter for valid peaks
    valid_peaks = metrics_df[metrics_df['peak_detected'] == True]
    if valid_peaks.empty:
        logger.warning("No valid peaks found in metrics. Using median latency or default 200ms.")
        peak_latency = 0.200
    else:
        # Use the median peak latency across participants
        peak_latency = valid_peaks['deviant_latency'].median() / 1000.0  # Convert ms to s

    logger.info(f"Plotting topomap at peak latency: {peak_latency:.3f} s")

    # Load epochs
    epochs = mne.read_epochs(epochs_file, verbose=False)
    
    # Compute difference wave evoked
    if 'standard' in epochs and 'deviant' in epochs:
        ev_std = epochs['standard'].average()
        ev_dev = epochs['deviant'].average()
        ev_diff = ev_dev.copy()
        ev_diff.data = ev_dev.data - ev_std.data
        ev_diff.comment = "MMN Difference"
    else:
        raise ValueError("Epochs must contain 'standard' and 'deviant' conditions.")

    # Check montage
    if ev_diff.info['ch_names'] is None or len(ev_diff.info['ch_names']) == 0:
        raise ValueError("No channels found in epochs info. Montage may be missing.")

    # Plot topomap
    fig = ev_diff.plot_topomap(
        times=peak_latency,
        ch_type='eeg',
        cmap='RdBu_r',
        size=3,
        show=False,
        extrapolate='local',
        sphere=0.9
    )
    
    plt.suptitle(f"MMN Topography at {peak_latency*1000:.0f} ms", fontsize=14)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved topomap to {save_path}")
    plt.close()

def run_viz_pipeline() -> None:
    """
    Execute the visualization pipeline: load metrics, calculate prevalence,
    generate plots, and save to results/plots/.
    """
    project_root = get_project_root()
    plots_dir = project_root / "results" / "plots"
    ensure_directory(plots_dir)

    logger.info("Starting visualization pipeline...")

    # Load metrics
    try:
        metrics_df = load_metrics()
    except FileNotFoundError as e:
        logger.error(f"Cannot run viz pipeline: {e}")
        return

    # Calculate and log prevalence
    prevalence = calculate_prevalence(metrics_df)
    logger.info(f"Calculated MMN prevalence: {prevalence:.2%}")

    # Generate ERP Plot
    erp_path = plots_dir / "erp_plot.png"
    try:
        plot_grand_average_erp(metrics_df, erp_path)
    except Exception as e:
        logger.error(f"Failed to generate ERP plot: {e}")

    # Generate Topomap
    topo_path = plots_dir / "topomap.png"
    try:
        plot_topomap_at_peak(metrics_df, topo_path)
    except Exception as e:
        logger.error(f"Failed to generate topomap: {e}")

    logger.info("Visualization pipeline completed.")

def main():
    logging.basicConfig(level=logging.INFO)
    run_viz_pipeline()

if __name__ == "__main__":
    main()
