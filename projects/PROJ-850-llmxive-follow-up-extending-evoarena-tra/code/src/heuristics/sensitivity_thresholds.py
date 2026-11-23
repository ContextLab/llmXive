"""
Sensitivity analysis for conflict detection thresholds.

Executes the conflict detector across a range of thresholds to determine
optimal precision/recall trade-offs.

Output: data/processed/sensitivity_analysis_thresholds.csv
Columns: threshold, precision, recall, f1_score, model_name
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.heuristics.conflict_detector import ConflictDetector, load_synthetic_pairs
from src.utils.seeding import set_deterministic_seed


def calculate_metrics(
    predictions: List[bool],
    ground_truth: List[bool]
) -> Tuple[float, float, float]:
    """
    Calculate precision, recall, and F1 score.

    Args:
        predictions: List of predicted boolean values (True=conflict, False=no conflict)
        ground_truth: List of ground truth boolean values

    Returns:
        Tuple of (precision, recall, f1_score)
    """
    if not predictions or not ground_truth:
        return 0.0, 0.0, 0.0

    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    tp = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1


def run_sensitivity_analysis(
    detector: ConflictDetector,
    pairs: List[Dict[str, Any]],
    thresholds: List[float],
    model_name: str = "distilbert-base-uncased"
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis across multiple thresholds.

    Args:
        detector: Initialized ConflictDetector instance
        pairs: List of synthetic pairs with ground truth
        thresholds: List of threshold values to test
        model_name: Name of the model being analyzed

    Returns:
        List of dictionaries containing threshold, precision, recall, f1_score, model_name
    """
    results = []

    # Extract ground truth
    ground_truth = [pair["is_contradiction"] for pair in pairs]

    for threshold in thresholds:
        # Update detector threshold
        detector.threshold = threshold

        # Run predictions
        predictions = []
        for pair in pairs:
            result = detector.predict(pair["patch_a"], pair["patch_b"])
            predictions.append(result.is_conflict)

        # Calculate metrics
        precision, recall, f1 = calculate_metrics(predictions, ground_truth)

        results.append({
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "model_name": model_name
        })

    return results


def write_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Write sensitivity analysis results to CSV.

    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["threshold", "precision", "recall", "f1_score", "model_name"]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    """Main entry point for sensitivity threshold analysis."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on conflict detection thresholds"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="distilbert-base-uncased",
        help="Model name to analyze (default: distilbert-base-uncased)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/sensitivity_analysis_thresholds.csv",
        help="Output CSV path (default: data/processed/sensitivity_analysis_thresholds.csv)"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.5,0.6,0.7,0.8,0.9,0.95",
        help="Comma-separated list of thresholds to test"
    )

    args = parser.parse_args()

    # Set deterministic seed
    set_deterministic_seed(42)

    # Parse thresholds
    thresholds = [float(t) for t in args.thresholds.split(",")]

    # Load synthetic pairs
    synthetic_pairs_path = project_root / "data" / "raw" / "synthetic_pairs.json"
    if not synthetic_pairs_path.exists():
        raise FileNotFoundError(
            f"Synthetic pairs file not found at {synthetic_pairs_path}. "
            "Please run T005 first to generate the dataset."
        )

    pairs = load_synthetic_pairs(synthetic_pairs_path)

    if not pairs:
        raise ValueError("No synthetic pairs loaded. Cannot run sensitivity analysis.")

    # Initialize detector
    detector = ConflictDetector(model_name=args.model)

    # Run sensitivity analysis
    print(f"Running sensitivity analysis on {len(pairs)} pairs...")
    print(f"Testing thresholds: {thresholds}")

    results = run_sensitivity_analysis(
        detector=detector,
        pairs=pairs,
        thresholds=thresholds,
        model_name=args.model
    )

    # Write results to CSV
    output_path = Path(args.output)
    write_results_to_csv(results, output_path)

    print(f"Sensitivity analysis complete. Results written to: {output_path}")

    # Print summary
    print("\nThreshold Sensitivity Summary:")
    print("-" * 60)
    print(f"{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print("-" * 60)
    for r in results:
        print(f"{r['threshold']:<12.2f} {r['precision']:<12.4f} {r['recall']:<12.4f} {r['f1_score']:<12.4f}")
    print("-" * 60)


if __name__ == "__main__":
    main()
