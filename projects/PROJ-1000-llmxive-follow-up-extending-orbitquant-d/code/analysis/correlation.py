"""
Correlation Analysis Module for OrbitQuant Follow-up.

Computes Pearson correlation coefficient and p-value between prompt semantic entropy
scores and DiT activation variances.

This module implements the core statistical analysis for User Story 1 (US1).
"""

import os
import json
import logging
import csv
import numpy as np
from scipy import stats
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from config import Config

logger = logging.getLogger(__name__)


def load_entropy_scores(file_path: str) -> Dict[str, float]:
    """
    Load semantic entropy scores from a CSV file.

    Expected format:
    prompt_id,entropy_score

    Args:
        file_path: Path to the CSV file containing entropy scores.

    Returns:
        Dictionary mapping prompt_id to entropy_score.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    scores = {}
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Entropy scores file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'prompt_id' not in row or 'entropy_score' not in row:
                raise ValueError(f"Invalid CSV format in {file_path}. Expected 'prompt_id' and 'entropy_score' columns.")
            try:
                prompt_id = row['prompt_id'].strip()
                score = float(row['entropy_score'])
                scores[prompt_id] = score
            except ValueError as e:
                raise ValueError(f"Failed to parse row in {file_path}: {row} - {e}")

    logger.info(f"Loaded {len(scores)} entropy scores from {file_path}")
    return scores


def load_activation_variances(file_path: str) -> Dict[str, Dict[str, float]]:
    """
    Load activation variances from a JSON file.

    Expected format:
    {
        "prompt_id": {
            "layer_name": variance_value,
            ...
        },
        ...
    }

    Args:
        file_path: Path to the JSON file containing activation variances.

    Returns:
        Dictionary mapping prompt_id to a dictionary of layer_name -> variance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Activation variances file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON format in {file_path}. Expected a dictionary.")

    for prompt_id, layers in data.items():
        if not isinstance(layers, dict):
            raise ValueError(f"Invalid data for prompt_id '{prompt_id}' in {file_path}. Expected a dictionary of layers.")
        for layer_name, val in layers.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"Invalid variance value for layer '{layer_name}' in prompt '{prompt_id}'.")

    logger.info(f"Loaded activation variances for {len(data)} prompts from {file_path}")
    return data


def compute_pearson_correlation(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p-value.

    Args:
        x: First array of values (e.g., entropy scores).
        y: Second array of values (e.g., activation variances).

    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(x) != len(y):
        raise ValueError(f"Input arrays must have the same length: {len(x)} vs {len(y)}")

    if len(x) < 2:
        raise ValueError("At least 2 data points are required for correlation analysis.")

    # Check for constant arrays
    if np.all(x == x[0]) or np.all(y == y[0]):
        logger.warning("One or both input arrays are constant. Correlation is undefined.")
        return 0.0, 1.0

    r, p = stats.pearsonr(x, y)
    return float(r), float(p)


def analyze_correlation(
    entropy_file: str,
    variance_file: str,
    output_file: str,
    layer_subset: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Perform correlation analysis between entropy scores and activation variances.

    This function:
    1. Loads entropy scores and activation variances.
    2. Aligns data by prompt_id.
    3. Computes Pearson correlation for each requested layer.
    4. Saves results to the specified output file.

    Args:
        entropy_file: Path to the CSV file with entropy scores.
        variance_file: Path to the JSON file with activation variances.
        output_file: Path to save the correlation results JSON.
        layer_subset: Optional list of layer names to analyze. If None, all layers are used.

    Returns:
        Dictionary containing the correlation results.
    """
    # Load data
    entropy_scores = load_entropy_scores(entropy_file)
    variance_data = load_activation_variances(variance_file)

    # Identify common prompt IDs
    common_ids = set(entropy_scores.keys()) & set(variance_data.keys())
    if not common_ids:
        raise ValueError("No common prompt IDs found between entropy and variance files.")

    logger.info(f"Found {len(common_ids)} common prompt IDs for analysis.")

    # Sort IDs to ensure consistent ordering
    sorted_ids = sorted(common_ids)

    # Determine which layers to analyze
    all_layers = set()
    for pid in common_ids:
        all_layers.update(variance_data[pid].keys())
    layers_to_analyze = sorted(layer_subset) if layer_subset else sorted(all_layers)

    if not layers_to_analyze:
        raise ValueError("No layers found to analyze.")

    logger.info(f"Analyzing {len(layers_to_analyze)} layers: {layers_to_analyze}")

    # Prepare results
    results = {
        "metadata": {
            "entropy_file": entropy_file,
            "variance_file": variance_file,
            "num_samples": len(sorted_ids),
            "layers_analyzed": layers_to_analyze
        },
        "correlations": {}
    }

    # Compute correlations
    for layer in layers_to_analyze:
        x_vals = []
        y_vals = []

        for pid in sorted_ids:
            x_vals.append(entropy_scores[pid])
            y_vals.append(variance_data[pid][layer])

        x_arr = np.array(x_vals)
        y_arr = np.array(y_vals)

        r, p = compute_pearson_correlation(x_arr, y_arr)

        results["correlations"][layer] = {
            "pearson_r": r,
            "p_value": p,
            "n": len(sorted_ids),
            "significant": p < 0.05
        }

        logger.info(f"Layer '{layer}': r={r:.4f}, p={p:.4f}, significant={p < 0.05}")

    # Identify significant correlations
    significant_layers = [
        layer for layer, data in results["correlations"].items()
        if data["significant"]
    ]
    results["summary"] = {
        "total_layers": len(layers_to_analyze),
        "significant_count": len(significant_layers),
        "significant_layers": significant_layers,
        "hypothesis_supported": len(significant_layers) > 0
    }

    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Correlation results saved to {output_file}")

    return results


def main():
    """
    Main entry point for the correlation analysis script.

    Reads configuration from `code/config.py` and executes the analysis.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = Config()

    # Define paths based on config
    entropy_file = str(config.data_path / "processed" / "entropy_scores.csv")
    variance_file = str(config.data_path / "processed" / "activation_variances.json")
    output_file = str(config.data_path / "processed" / "correlation_results.json")

    # Check if input files exist
    if not Path(entropy_file).exists():
        logger.error(f"Entropy scores file not found: {entropy_file}")
        logger.error("Please run T009 (entropy_proxy.py) first to generate entropy scores.")
        return 1

    if not Path(variance_file).exists():
        logger.error(f"Activation variances file not found: {variance_file}")
        logger.error("Please run T017 (run_correlation.py) or the variance capture step first.")
        return 1

    try:
        results = analyze_correlation(entropy_file, variance_file, output_file)
        logger.info("Analysis completed successfully.")
        logger.info(f"Significant layers: {results['summary']['significant_layers']}")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())