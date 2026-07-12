"""
Visualization module for User Story 3.
Generates plots of sampling rate vs. bias magnitude with catalog uncertainty thresholds.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments

from code.config import RESULTS_DIR, DATA_DIR
from code.analysis.aggregate import load_all_metrics_from_dir, aggregate_results
from code.utils.logging_config import get_derivation_logger

logger = get_derivation_logger(__name__)

def plot_sampling_rate_vs_bias(
    results_dir: Path,
    output_path: Path,
    event_id: Optional[str] = None
) -> Path:
    """
    Generate a visualization of sampling rate vs. bias magnitude.

    Args:
        results_dir: Directory containing metric results (JSON/CSV).
        output_path: Path where the figure will be saved.
        event_id: Optional specific event ID to plot. If None, aggregates all.

    Returns:
        Path to the saved figure.
    """
    logger.info(f"Generating bias vs. resolution plot for {results_dir}")

    # Load aggregated results
    # We expect the aggregation logic to have produced a summary file or
    # we load raw metrics and aggregate here.
    # Based on T029/T030, we expect a structure where we can group by event and resolution.
    
    try:
        # Attempt to load the aggregation report if it exists (from T033)
        # If not, we load raw metrics and perform a lightweight aggregation here.
        aggregation_file = results_dir / "aggregation_report.json"
        if aggregation_file.exists():
            import json
            with open(aggregation_file, 'r') as f:
                data = json.load(f)
            # Flatten the structure for plotting if necessary
            # Expected structure: list of dicts with 'event_id', 'sampling_rate', 'bias', 'uncertainty'
            metrics = data.get('metrics', [])
        else:
            # Fallback: Load raw metrics from the directory structure
            # This assumes T023/T024 have produced per-resolution JSON files
            metrics = load_all_metrics_from_dir(results_dir)
            
        if not metrics:
            logger.warning("No metrics found to plot. Creating a placeholder warning figure.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No valid metrics found for visualization", 
                    transform=ax.transAxes, ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return output_path

        # Prepare data for plotting
        # We need to group by event_id to plot multiple lines or just aggregate all?
        # The task asks for "sampling rate vs. bias magnitude". 
        # We will plot all valid data points, potentially grouped by event if multiple exist,
        # or aggregate if single event.
        
        sampling_rates = []
        bias_values = []
        uncertainty_values = []
        event_labels = []

        for m in metrics:
            # Filter out inconclusive or excluded events if they are in the raw list
            # But the aggregation logic (T029) should have handled exclusion for the threshold calculation.
            # For the plot, we show the trend, so we include valid measurements.
            
            rate = m.get('sampling_rate')
            bias = m.get('bias_magnitude') # Assuming this key exists from T024
            unc = m.get('catalog_uncertainty') # The threshold line value
            eid = m.get('event_id', 'Unknown')

            if rate is None or bias is None:
                continue

            sampling_rates.append(rate)
            bias_values.append(bias)
            uncertainty_values.append(unc)
            event_labels.append(eid)

        if not sampling_rates:
            logger.warning("No valid data points after filtering. Creating warning figure.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No valid data points for visualization", 
                    transform=ax.transAxes, ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return output_path

        # Sort by sampling rate for clean line plotting
        sorted_indices = np.argsort(sampling_rates)
        rates = np.array(sampling_rates)[sorted_indices]
        biases = np.array(bias_values)[sorted_indices]
        uncs = np.array(uncertainty_values)[sorted_indices]
        
        # If we have multiple events, we might want to plot them separately or average.
        # For this MVP, we will plot the global trend and the threshold line.
        # If distinct events exist, we can use a legend or color mapping.
        
        unique_events = list(set(event_labels))
        
        fig, ax = plt.subplots(figsize=(10, 6))

        if len(unique_events) == 1:
            # Single event case
            ax.plot(rates, biases, 'o-', label='Bias Magnitude', color='blue')
        else:
            # Multiple events: Plot each event with a light line, and a bold average
            # Group by event
            from collections import defaultdict
            event_data = defaultdict(list)
            for r, b, u, e in zip(rates, biases, uncs, event_labels):
                event_data[e].append((r, b))
            
            for eid, points in event_data.items():
                pts_r = [p[0] for p in points]
                pts_b = [p[1] for p in points]
                pts_s = np.argsort(pts_r)
                ax.plot(np.array(pts_r)[pts_s], np.array(pts_b)[pts_s], 
                        'o-', alpha=0.3, label=f'{eid}')

            # Calculate and plot average
            # Since rates might differ slightly, we interpolate or just plot all points with low alpha
            # and add a trend line for the aggregate if possible.
            # For simplicity in this script, we just plot the aggregate as a bold line over the average
            # of points at similar rates if we had binned data. 
            # Instead, let's just plot the raw points with low alpha and a global trend.
            ax.plot(rates, biases, 'k.', alpha=0.1, markersize=10)
            # Add a simple trend line (linear fit) for the aggregate
            if len(rates) > 1:
                coeffs = np.polyfit(rates, biases, 1)
                p = np.poly1d(coeffs)
                ax.plot(rates, p(rates), 'k--', label='Aggregate Trend', linewidth=2)

        # Plot the catalog uncertainty threshold line
        # The threshold is constant per event, but might vary between events.
        # We plot the average threshold or the specific one if single event.
        if len(unique_events) == 1:
            threshold_val = uncs[0]
            ax.axhline(y=threshold_val, color='red', linestyle='--', 
                       label=f'Catalog Uncertainty (90% CI) = {threshold_val:.2e}')
        else:
            # Plot average threshold
            avg_threshold = np.mean(uncs)
            ax.axhline(y=avg_threshold, color='red', linestyle='--', 
                       label=f'Avg Catalog Uncertainty = {avg_threshold:.2e}')
            # Optionally plot min/max range
            # ax.fill_between([min(rates), max(rates)], np.min(uncs), np.max(uncs), 
            #                 color='red', alpha=0.1, label='Uncertainty Range')

        ax.set_xlabel('Sampling Rate (Hz)', fontsize=12)
        ax.set_ylabel('Bias Magnitude (Normalized)', fontsize=12)
        ax.set_title('Impact of Data Resolution on Parameter Estimation Bias', fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(True, which='both', linestyle=':', alpha=0.6)
        
        # Log scale for X axis if rates vary significantly (e.g. 4096 to 1024)
        # ax.set_xscale('log') 

        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Visualization saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate visualization: {e}", exc_info=True)
        raise

def main():
    """
    Entry point for generating the visualization.
    Reads from RESULTS_DIR and writes to figures/ directory.
    """
    from code.config import ensure_directories
    ensure_directories()
    
    # Determine input and output paths
    results_dir = RESULTS_DIR / "metrics"
    if not results_dir.exists():
        logger.error(f"Results directory {results_dir} does not exist. Cannot generate plot.")
        return

    output_dir = RESULTS_DIR.parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "sampling_rate_vs_bias.png"

    try:
        plot_sampling_rate_vs_bias(results_dir, output_file)
        print(f"Successfully generated: {output_file}")
    except Exception as e:
        logger.critical(f"Visualization generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
