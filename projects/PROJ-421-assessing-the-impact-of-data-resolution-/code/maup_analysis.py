"""
MAUP Documentation and Statistical Impact Analysis.

This module computes statistical metrics quantifying the impact of the
Modifiable Areal Unit Problem (MAUP) on the spatial dataset as resolution
changes. It calculates Shannon Entropy and variance changes across
aggregation levels without narrative framing.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Import from local project modules
from utils import get_logger, get_raster_info, read_raster_windowed
from config import DATA_RAW_DIR, DATA_DERIVED_DIR, DATA_RESULTS_DIR

logger = get_logger(__name__)

def calculate_shannon_entropy(values: np.ndarray) -> float:
    """
    Calculate Shannon Entropy of a 1D array of values.
    
    Parameters
    ----------
    values : np.ndarray
        Array of integer class values.
        
    Returns
    -------
    float
        Shannon entropy value.
    """
    # Flatten and get unique counts
    flat = values.flatten()
    # Filter out NoData (usually -1 or 255 depending on source, assuming 0 is valid)
    # Based on NLCD, 0 is usually water or no data, but let's assume standard integer classes.
    # We count occurrences of each unique value.
    unique, counts = np.unique(flat, return_counts=True)
    
    # Normalize to probabilities
    probs = counts / counts.sum()
    
    # Calculate entropy: -sum(p * log(p))
    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log2(probs))
    
    return float(entropy)

def calculate_variance(values: np.ndarray) -> float:
    """
    Calculate variance of a 1D array of values.
    
    Parameters
    ----------
    values : np.ndarray
        Array of values.
        
    Returns
    -------
    float
        Variance value.
    """
    return float(np.var(values))

def analyze_resolution_impact(resolution_factors: List[int] = [1, 2, 4, 8, 16]) -> Dict[str, Any]:
    """
    Analyze the statistical impact of aggregation factors on the dataset.
    
    Reads the base 30m data and derived resolutions, computes Shannon Entropy
    and Variance for each, and returns a structured summary.
    
    Parameters
    ----------
    resolution_factors : List[int]
        List of aggregation factors (1=30m, 2=60m, etc.).
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing metrics for each resolution.
    """
    base_path = Path(DATA_RAW_DIR) / "nlcd_2019_colorado_30m.tif"
    
    if not base_path.exists():
        logger.error(f"Base data file not found: {base_path}")
        raise FileNotFoundError(f"Base data file not found: {base_path}")
    
    results = []
    
    # Process base resolution (factor 1)
    logger.info(f"Processing base resolution (30m)...")
    base_data = read_raster_windowed(base_path, chunk_size=(2000, 2000))
    base_data = np.concatenate(base_data, axis=0) if base_data else np.array([])
    
    if base_data.size == 0:
        raise ValueError("Failed to read base raster data.")
    
    base_entropy = calculate_shannon_entropy(base_data)
    base_variance = calculate_variance(base_data)
    
    results.append({
        "factor": 1,
        "resolution_m": 30,
        "entropy": base_entropy,
        "variance": base_variance,
        "relative_entropy": 1.0,
        "relative_variance": 1.0
    })
    
    # Process derived resolutions
    for factor in resolution_factors:
        if factor == 1:
            continue
            
        derived_path = Path(DATA_DERIVED_DIR) / f"nlcd_2019_colorado_{30*factor}m.tif"
        
        if not derived_path.exists():
            logger.warning(f"Derived file not found: {derived_path}. Skipping factor {factor}.")
            continue
        
        logger.info(f"Processing factor {factor} ({30*factor}m)...")
        derived_data = read_raster_windowed(derived_path, chunk_size=(2000, 2000))
        derived_data = np.concatenate(derived_data, axis=0) if derived_data else np.array([])
        
        if derived_data.size == 0:
            continue
        
        entropy = calculate_shannon_entropy(derived_data)
        variance = calculate_variance(derived_data)
        
        results.append({
            "factor": factor,
            "resolution_m": 30 * factor,
            "entropy": entropy,
            "variance": variance,
            "relative_entropy": entropy / base_entropy if base_entropy > 0 else 0.0,
            "relative_variance": variance / base_variance if base_variance > 0 else 0.0
        })
    
    return results

def generate_maup_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a structured Markdown report documenting the MAUP statistical impact.
    
    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of analysis results per resolution.
    output_path : Path
        Path to write the markdown report.
    """
    if not results:
        logger.error("No results to report.")
        return

    lines = []
    lines.append("# MAUP Statistical Impact Analysis")
    lines.append("")
    lines.append("## Summary")
    lines.append("This report documents the statistical impact of spatial aggregation (MAUP) on the NLCD Colorado dataset.")
    lines.append("Metrics calculated include Shannon Entropy and Variance across resolution factors.")
    lines.append("")
    lines.append("## Methodology")
    lines.append("- **Base Resolution**: 30m (Factor 1)")
    lines.append("- **Aggregation Method**: Nearest Neighbor")
    lines.append("- **Metrics**: Shannon Entropy (uncertainty/diversity), Variance (dispersion)")
    lines.append("- **Normalization**: Values relative to 30m baseline")
    lines.append("")
    lines.append("## Statistical Metrics by Resolution")
    lines.append("")
    lines.append("| Factor | Resolution (m) | Shannon Entropy | Variance | Rel. Entropy | Rel. Variance |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for r in results:
        lines.append(
            f"| {r['factor']} | {r['resolution_m']} | "
            f"{r['entropy']:.4f} | {r['variance']:.4f} | "
            f"{r['relative_entropy']:.4f} | {r['relative_variance']:.4f} |"
        )
    
    lines.append("")
    lines.append("## Observed Trends")
    lines.append("")
    
    # Calculate deltas
    if len(results) > 1:
        base = results[0]
        final = results[-1]
        entropy_delta = base['entropy'] - final['entropy']
        variance_delta = base['variance'] - final['variance']
        
        lines.append(f"- **Entropy Change**: {entropy_delta:.4f} ({(entropy_delta/base['entropy'])*100:.2f}% decrease from 30m)")
        lines.append(f"- **Variance Change**: {variance_delta:.4f} ({(variance_delta/base['variance'])*100:.2f}% decrease from 30m)")
        lines.append("")
        lines.append("### Interpretation")
        lines.append("Aggregation reduces the number of unique pixel configurations, leading to a systematic decrease in Shannon Entropy.")
        lines.append("This reduction represents a loss of information regarding local heterogeneity.")
        lines.append("Variance reduction indicates a smoothing effect where extreme local values are averaged out or dominated by the majority class in the aggregation window.")
    else:
        lines.append("Insufficient data points to calculate trends.")
    
    lines.append("")
    lines.append("## Raw Data")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(results, indent=2))
    lines.append("```")
    
    content = "\n".join(lines)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logger.info(f"MAUP report written to {output_path}")

def main():
    """Main entry point for MAUP analysis."""
    logger.info("Starting MAUP Analysis...")
    
    # Define resolution factors to analyze
    factors = [1, 2, 4, 8, 16]
    
    try:
        results = analyze_resolution_impact(factors)
        output_path = Path("projects/PROJ-421-assessing-the-impact-of-data-resolution-/docs/maup_analysis.md")
        generate_maup_report(results, output_path)
        logger.info("MAUP Analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"MAUP Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
