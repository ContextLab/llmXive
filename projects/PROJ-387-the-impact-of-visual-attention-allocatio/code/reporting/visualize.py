import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils.config import get_project_root, get_output_path, get_data_path, set_global_seed
from utils.logger import get_logger

# Set random seed for reproducibility
set_global_seed()

logger = get_logger(__name__)

def load_lmm_results() -> Optional[Dict[str, Any]]:
    """Load LMM results from the analysis output."""
    root = get_project_root()
    results_path = root / "output" / "results" / "lmm_summary.csv"
    if not results_path.exists():
        logger.warning(f"LMM results not found at {results_path}")
        return None
    try:
        df = pd.read_csv(results_path)
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Failed to load LMM results: {e}")
        return None

def load_correction_results() -> Optional[Dict[str, Any]]:
    """Load Bonferroni correction results."""
    root = get_project_root()
    results_path = root / "output" / "results" / "correction_results.json"
    if not results_path.exists():
        logger.warning(f"Correction results not found at {results_path}")
        return None
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load correction results: {e}")
        return None

def read_valence_count() -> int:
    """Read the number of valence categories from the quality report."""
    root = get_project_root()
    report_path = root / "data" / "eye-tracking" / "quality_report.md"
    if not report_path.exists():
        logger.warning(f"Quality report not found at {report_path}, defaulting to 3 valence categories")
        return 3
    try:
        content = report_path.read_text()
        # Look for 'valence_categories_count: X' in the markdown
        for line in content.split('\n'):
            if 'valence_categories_count' in line:
                # Extract the number after the colon
                parts = line.split(':')
                if len(parts) > 1:
                    return int(parts[1].strip())
    except Exception as e:
        logger.error(f"Failed to read valence count: {e}")
    return 3

def plot_scatter(data: pd.DataFrame, metric: str, recall_col: str, valence: str, output_dir: Path) -> str:
    """
    Create a scatter plot of Attention Metric vs. Recall Accuracy for a specific valence.
    
    Ensures axes are labeled "Attention Metric" and "Recall Accuracy" as per SC-005.
    """
    plt.figure(figsize=(10, 6))
    
    # Filter data for the specific valence if a 'valence' column exists
    if 'valence' in data.columns:
        subset = data[data['valence'] == valence]
    else:
        subset = data

    if subset.empty:
        logger.warning(f"No data found for valence={valence}, metric={metric}")
        plt.close()
        return ""

    # Ensure the columns exist
    if metric not in subset.columns or recall_col not in subset.columns:
        logger.error(f"Columns {metric} or {recall_col} not found in data")
        plt.close()
        return ""

    plt.scatter(subset[metric], subset[recall_col], alpha=0.6, edgecolors='w', s=50)
    
    # SC-005: Ensure specific axis labels
    plt.xlabel("Attention Metric")
    plt.ylabel("Recall Accuracy")
    plt.title(f"Attention Metric ({metric}) vs Recall Accuracy by Valence ({valence})")
    
    plt.grid(True, linestyle='--', alpha=0.7)
    
    filename = f"scatter_{valence}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved scatter plot: {filepath}")
    return str(filepath)

def plot_histogram(data: pd.DataFrame, metric: str, valence: str, output_dir: Path) -> str:
    """
    Create a histogram of an attention metric for a specific valence.
    
    Ensures axes are labeled appropriately.
    """
    plt.figure(figsize=(10, 6))
    
    if 'valence' in data.columns:
        subset = data[data['valence'] == valence]
    else:
        subset = data

    if subset.empty:
        logger.warning(f"No data found for valence={valence}, metric={metric}")
        plt.close()
        return ""

    if metric not in subset.columns:
        logger.error(f"Column {metric} not found in data")
        plt.close()
        return ""

    plt.hist(subset[metric], bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    
    plt.xlabel("Attention Metric")
    plt.ylabel("Frequency")
    plt.title(f"Distribution of {metric} by Valence ({valence})")
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    filename = f"hist_{metric}_{valence}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved histogram: {filepath}")
    return str(filepath)

def run_visualization():
    """
    Main execution function for visualization.
    Loads processed data (or LMM results if raw data is unavailable) and generates plots.
    """
    root = get_project_root()
    output_dir = root / "output" / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting visualization pipeline...")
    
    # Determine data source
    # Try to load raw processed data first
    data_path = get_data_path() / "processed" / "merged_analysis_data.csv"
    data = None
    
    if data_path.exists():
        try:
            data = pd.read_csv(data_path)
            logger.info(f"Loaded raw data from {data_path}")
        except Exception as e:
            logger.warning(f"Could not load raw data: {e}. Attempting to use LMM results for plotting.")
            data = None
    
    # If raw data is not available, try to reconstruct from LMM results or fail
    if data is None:
        lmm_results = load_lmm_results()
        if lmm_results:
            # Convert LMM results to a DataFrame for plotting (simulated for visualization if needed)
            # Note: In a real scenario, we would need the raw data points. 
            # Since we cannot fabricate data, we will attempt to load a standard dataset if available
            # or use the LMM summary to indicate association.
            # However, for the purpose of T042 (labels), we need to ensure the plotting functions
            # work correctly. We will try to find a standard dataset path or exit gracefully if data is missing.
            logger.error("Raw data not found. Cannot generate scatter plots without actual data points.")
            logger.info("Skipping plot generation due to missing raw data. (Real data requirement)")
            return
        else:
            logger.error("No data source available (neither raw nor LMM results).")
            return

    # Get valence categories
    valence_count = read_valence_count()
    # Determine unique valences from data or default
    if 'valence' in data.columns:
        valences = data['valence'].unique().tolist()
    else:
        # Fallback if column missing but we have data
        valences = ['positive', 'negative', 'neutral'][:valence_count]
    
    # Common attention metrics based on project context
    metrics = ['fixation_duration', 'saccade_amplitude', 'gaze_distribution']
    recall_col = 'recall_accuracy'

    for metric in metrics:
        for valence in valences:
            # Generate Scatter Plot (T040 requirement, ensuring T042 labels)
            plot_scatter(data, metric, recall_col, valence, output_dir)
            
            # Generate Histogram (T041 requirement)
            plot_histogram(data, metric, valence, output_dir)

    logger.info("Visualization pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Generate visualizations for visual attention analysis.")
    parser.parse_args()
    run_visualization()

if __name__ == "__main__":
    main()