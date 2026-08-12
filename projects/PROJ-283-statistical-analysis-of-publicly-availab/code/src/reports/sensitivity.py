"""
Sensitivity Analysis Module (T025)

Implements threshold sweep analysis over specific p-value thresholds to evaluate
model stability and predictor significance variation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default thresholds as per Spec SC-004
DEFAULT_THRESHOLDS = [0.005, 0.01, 0.05]
JACCARD_THRESHOLD_GATE = 0.8


def get_significant_predictors(
    model_metrics: Dict,
    threshold: float,
    model_type: Optional[str] = None
) -> Set[str]:
    """
    Extract the set of predictors with corrected p-value < threshold.

    Args:
        model_metrics: Dictionary containing model results (from T027).
        threshold: The p-value threshold for significance.
        model_type: Optional filter for specific model type.

    Returns:
        Set of predictor names considered significant at this threshold.
    """
    if not model_metrics or 'models' not in model_metrics:
        logger.warning("Model metrics structure invalid or empty.")
        return set()

    predictors = set()
    models_data = model_metrics['models']

    # If specific model requested, filter; otherwise iterate all
    if model_type:
        models_to_check = [m for m in models_data if m.get('model_type') == model_type]
    else:
        models_to_check = models_data

    for model in models_to_check:
        if 'corrected_p_values' not in model:
            continue

        p_values = model['corrected_p_values']
        # Ensure p_values is a dictionary or similar mapping
        if isinstance(p_values, dict):
            for pred, p_val in p_values.items():
                # Exclude NaN values
                if pd.isna(p_val):
                    continue
                if p_val < threshold:
                    predictors.add(pred)

    return predictors


def calculate_jaccard_index(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate the Jaccard index between two sets of predictors.

    Jaccard Index = |A ∩ B| / |A ∪ B|

    Args:
        set_a: First set of predictors.
        set_b: Second set of predictors.

    Returns:
        Jaccard index (float between 0.0 and 1.0). Returns 0.0 if union is empty.
    """
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))

    if union == 0:
        # Edge case: both sets empty -> defined as 0.0 per spec
        return 0.0

    return intersection / union


def perform_threshold_sweep(
    model_metrics: Dict,
    thresholds: List[float]
) -> Dict[str, Dict]:
    """
    Perform a threshold sweep analysis over the provided p-value thresholds.

    Args:
        model_metrics: Dictionary containing model results.
        thresholds: List of thresholds to sweep.

    Returns:
        Dictionary mapping thresholds to their significant predictor sets and counts.
    """
    results = {}
    for threshold in thresholds:
        sig_preds = get_significant_predictors(model_metrics, threshold)
        results[threshold] = {
            'significant_predictors': list(sig_preds),
            'count': len(sig_preds)
        }
        logger.info(f"Threshold {threshold}: {len(sig_preds)} significant predictors")

    return results


def calculate_pairwise_jaccard(
    sweep_results: Dict[str, Dict],
    thresholds: List[float]
) -> List[Dict]:
    """
    Calculate pairwise Jaccard indices for all pairs in the threshold set.

    Args:
        sweep_results: Results from perform_threshold_sweep.
        thresholds: The list of thresholds used.

    Returns:
        List of dictionaries containing pair info and Jaccard index.
    """
    pairwise_results = []
    n = len(thresholds)

    for i in range(n):
        for j in range(i + 1, n):
            t1 = thresholds[i]
            t2 = thresholds[j]
            set1 = set(sweep_results[t1]['significant_predictors'])
            set2 = set(sweep_results[t2]['significant_predictors'])

            jaccard = calculate_jaccard_index(set1, set2)

            pairwise_results.append({
                'threshold_pair': [t1, t2],
                'jaccard_index': jaccard,
                'set1_size': len(set1),
                'set2_size': len(set2)
            })
            logger.info(f"Jaccard({t1}, {t2}): {jaccard:.4f}")

    return pairwise_results


def generate_sensitivity_report(
    model_metrics: Dict,
    output_path: str,
    thresholds: Optional[List[float]] = None
) -> Dict:
    """
    Generate the full sensitivity analysis report.

    Args:
        model_metrics: Dictionary containing model results (from T027).
        output_path: Path to save the JSON report.
        thresholds: Optional list of thresholds (defaults to DEFAULT_THRESHOLDS).

    Returns:
        The generated report dictionary.

    Raises:
        ValueError: If the minimum Jaccard index is below the gate threshold (0.8).
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")

    # 1. Perform Sweep
    sweep_results = perform_threshold_sweep(model_metrics, thresholds)

    # 2. Calculate Delta (variation in count)
    counts = [sweep_results[t]['count'] for t in thresholds]
    deltas = []
    for i in range(1, len(counts)):
        deltas.append(counts[i] - counts[i-1])

    # 3. Calculate Pairwise Jaccard
    pairwise_jaccard = calculate_pairwise_jaccard(sweep_results, thresholds)

    # 4. Check Gate
    min_jaccard = min(item['jaccard_index'] for item in pairwise_jaccard)
    logger.info(f"Minimum Jaccard Index: {min_jaccard:.4f}")

    if min_jaccard < JACCARD_THRESHOLD_GATE:
        error_msg = (
            f"Validation Gate Failed: Minimum Jaccard Index ({min_jaccard:.4f}) "
            f"is below threshold ({JACCARD_THRESHOLD_GATE}). "
            "Model stability is insufficient."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # 5. Compile Report
    report = {
        'thresholds': thresholds,
        'sweep_results': sweep_results,
        'delta_counts': deltas,
        'pairwise_jaccard': pairwise_jaccard,
        'min_jaccard_index': min_jaccard,
        'gate_passed': True
    }

    # 6. Save Report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity report saved to {output_path}")

    return report


def main():
    """
    Main entry point for running sensitivity analysis.
    Expects model_metrics.json to exist at data/results/model_metrics.json.
    """
    # Paths
    input_path = Path("data/results/model_metrics.json")
    output_path = "data/results/sensitivity_analysis.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load data
    try:
        with open(input_path, 'r') as f:
            model_metrics = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse input JSON: {e}")
        sys.exit(1)

    # Run Analysis
    try:
        generate_sensitivity_report(model_metrics, output_path)
        print(f"Sensitivity analysis completed successfully. Output: {output_path}")
    except ValueError as e:
        # Gate failure
        print(f"Sensitivity analysis failed validation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()