"""
Task T036: Generate MDES distribution histogram and summary statistics.

Reads power audit results from data/processed/power_audit_results.json,
computes MDES summary statistics (median, IQR), and generates a histogram
saved to data/processed/mdes_histogram.png.
"""
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging using project standard
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

INPUT_FILE = Path("data/processed/power_audit_results.json")
OUTPUT_HISTOGRAM = Path("data/processed/mdes_histogram.png")
OUTPUT_SUMMARY = Path("data/processed/mdes_summary.json")


def load_power_results(filepath: Path) -> List[Dict[str, Any]]:
    """Load power audit results from JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of results, got {type(data)}")
    
    return data


def extract_mdes_values(results: List[Dict[str, Any]]) -> List[float]:
    """Extract MDES values from results, filtering out None/invalid entries."""
    mdes_values = []
    for entry in results:
        mdes = entry.get('mdes')
        if mdes is not None and isinstance(mdes, (int, float)) and not np.isnan(mdes):
            mdes_values.append(float(mdes))
    return mdes_values


def compute_summary_statistics(values: List[float]) -> Dict[str, float]:
    """Compute median and IQR for the given values."""
    if not values:
        return {
            "count": 0,
            "median": None,
            "iqr": None,
            "min": None,
            "max": None,
            "mean": None
        }
    
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    
    return {
        "count": len(values),
        "median": median,
        "iqr": iqr,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr))
    }


def generate_histogram(
    values: List[float],
    output_path: Path,
    title: str = "Distribution of Minimum Detectable Effect Size (MDES)",
    xlabel: str = "MDES",
    ylabel: str = "Frequency",
    bins: int = 20,
    color: str = "steelblue"
) -> None:
    """Generate and save a histogram of MDES values."""
    if not values:
        logger.warning("No MDES values to plot. Creating empty plot.")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title(title)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return

    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=bins, color=color, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(axis='y', alpha=0.3)
    
    # Add median line
    median = np.median(values)
    plt.axvline(median, color='red', linestyle='dashed', linewidth=2, label=f'Median: {median:.3f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Histogram saved to {output_path}")


def save_summary_statistics(summary: Dict[str, float], output_path: Path) -> None:
    """Save summary statistics to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary statistics saved to {output_path}")


def main() -> int:
    """Main entry point for T036."""
    try:
        logger.info(f"Loading power audit results from {INPUT_FILE}")
        results = load_power_results(INPUT_FILE)
        
        logger.info(f"Loaded {len(results)} results")
        
        mdes_values = extract_mdes_values(results)
        logger.info(f"Extracted {len(mdes_values)} valid MDES values")
        
        summary = compute_summary_statistics(mdes_values)
        
        logger.info(f"Computing summary statistics: {summary}")
        
        generate_histogram(
            mdes_values,
            OUTPUT_HISTOGRAM,
            title="Distribution of Minimum Detectable Effect Size (MDES)",
            xlabel="MDES",
            ylabel="Frequency",
            bins=20,
            color="steelblue"
        )
        
        save_summary_statistics(summary, OUTPUT_SUMMARY)
        
        logger.info("T036 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())