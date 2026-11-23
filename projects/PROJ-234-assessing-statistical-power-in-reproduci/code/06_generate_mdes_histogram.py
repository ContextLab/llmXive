import json
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logging_config import setup_logging

def load_power_results(filepath: str) -> List[Dict[str, Any]]:
    """Load power audit results from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Power results file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {filepath}, got {type(data)}")
    
    return data

def extract_mdes_values(results: List[Dict[str, Any]]) -> List[float]:
    """Extract MDES values from power audit results, filtering out None/NaN."""
    values = []
    for item in results:
        if 'mdes' in item and item['mdes'] is not None:
            try:
                val = float(item['mdes'])
                if not np.isnan(val):
                    values.append(val)
            except (TypeError, ValueError):
                continue
    return values

def compute_summary_statistics(values: List[float]) -> Dict[str, float]:
    """Compute median and IQR for a list of values."""
    if not values:
        return {
            "median": 0.0,
            "iqr": 0.0,
            "count": 0,
            "min": 0.0,
            "max": 0.0
        }
    
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    
    return {
        "median": median,
        "iqr": iqr,
        "count": len(values),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def generate_histogram(
    values: List[float], 
    output_path: str, 
    title: str = "MDES Distribution",
    xlabel: str = "Minimum Detectable Effect Size (Cohen's d)",
    ylabel: str = "Frequency",
    bins: int = 20,
    color: str = "steelblue"
) -> None:
    """Generate and save an MDES distribution histogram."""
    if not values:
        # Create an empty plot if no data
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No MDES data available", transform=ax.transAxes, 
                ha='center', va='center', fontsize=14)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(values, bins=bins, color=color, edgecolor='black', alpha=0.7)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Add median line
        median = np.median(values)
        ax.axvline(median, color='red', linestyle='dashed', linewidth=2, label=f'Median: {median:.3f}')
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)

def save_summary_statistics(stats: Dict[str, float], output_path: str) -> None:
    """Save summary statistics to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def main():
    """Main entry point for generating MDES histogram and summary."""
    # Setup logging
    logger = setup_logging("mdes_histogram")
    logger.info("Starting MDES histogram generation")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "power_audit_results.json"
    output_hist_path = project_root / "data" / "processed" / "mdes_histogram.png"
    output_summary_path = project_root / "data" / "processed" / "mdes_summary.json"
    
    # Load data
    try:
        results = load_power_results(str(input_path))
        logger.info(f"Loaded {len(results)} power audit results")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Extract MDES values
    mdes_values = extract_mdes_values(results)
    logger.info(f"Extracted {len(mdes_values)} valid MDES values")
    
    if len(mdes_values) == 0:
        logger.warning("No valid MDES values found. Generating empty plot and zero stats.")
    
    # Compute statistics
    stats = compute_summary_statistics(mdes_values)
    logger.info(f"Computed summary statistics: median={stats['median']:.3f}, IQR={stats['iqr']:.3f}")
    
    # Generate histogram
    generate_histogram(mdes_values, str(output_hist_path))
    logger.info(f"Saved histogram to {output_hist_path}")
    
    # Save summary
    save_summary_statistics(stats, str(output_summary_path))
    logger.info(f"Saved summary statistics to {output_summary_path}")
    
    print(f"MDES analysis complete. Histogram: {output_hist_path}, Summary: {output_summary_path}")

if __name__ == "__main__":
    main()
