"""
Baseline Score Extractor for User Story 3.

This module extracts the baseline accuracy score from the neural evaluation results
(produced by T021/T024) and saves it to data/results/baseline_score.json.

This is a prerequisite for T032 (minimal feature set identification).
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path


def calculate_baseline_accuracy(neural_scores_path: Optional[str] = None) -> float:
    """
    Calculate the baseline accuracy from neural evaluation scores.

    The baseline accuracy is computed as the mean of exact-match scores
    from the neural adapter evaluation (T021/T024).

    Args:
        neural_scores_path: Path to the neural scores CSV file.
                            Defaults to 'data/results/neural_scores.csv'.

    Returns:
        The baseline accuracy as a float (0.0 to 1.0).

    Raises:
        FileNotFoundError: If the neural scores file does not exist.
        ValueError: If the scores file is empty or has invalid format.
    """
    if neural_scores_path is None:
        neural_scores_path = "data/results/neural_scores.csv"

    scores_file = Path(neural_scores_path)
    if not scores_file.exists():
        raise FileNotFoundError(
            f"Neural scores file not found: {neural_scores_path}. "
            "Please ensure T021/T024 has been executed first."
        )

    scores: List[float] = []

    with open(scores_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate header
        if 'exact_match' not in reader.fieldnames:
            raise ValueError(
                f"Invalid format in {neural_scores_path}. "
                "Expected 'exact_match' column in CSV header."
            )

        for row in reader:
            try:
                score = float(row['exact_match'])
                scores.append(score)
            except (ValueError, KeyError) as e:
                raise ValueError(
                    f"Invalid score value in row: {row}. Error: {e}"
                ) from e

    if not scores:
        raise ValueError(
            f"No valid scores found in {neural_scores_path}. "
            "The file appears to be empty or contains no data rows."
        )

    baseline_accuracy = sum(scores) / len(scores)
    return baseline_accuracy


def save_baseline_score(
    baseline_accuracy: float,
    output_path: Optional[str] = None
) -> Path:
    """
    Save the baseline accuracy score to a JSON file.

    Args:
        baseline_accuracy: The baseline accuracy value to save.
        output_path: Path for the output JSON file.
                    Defaults to 'data/results/baseline_score.json'.

    Returns:
        The Path object of the created file.
    """
    if output_path is None:
        output_path = "data/results/baseline_score.json"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "baseline_accuracy": baseline_accuracy,
        "source": "neural_adapter_evaluation",
        "description": "Mean exact-match score from neural adapter evaluation on RepoPeftBench"
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    return output_file


def extract_baseline_score(
    neural_scores_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> float:
    """
    Main function to extract baseline score from neural results and save to JSON.

    This is the primary entry point for T031a.

    Args:
        neural_scores_path: Path to neural scores CSV (default: data/results/neural_scores.csv).
        output_path: Path for output JSON (default: data/results/baseline_score.json).

    Returns:
        The extracted baseline accuracy as a float.
    """
    # Calculate baseline accuracy from neural scores
    baseline_accuracy = calculate_baseline_accuracy(neural_scores_path)

    # Save to JSON
    output_file = save_baseline_score(baseline_accuracy, output_path)

    return baseline_accuracy


def main() -> int:
    """
    CLI entry point for baseline score extraction.

    Returns:
        0 on success, 1 on failure.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract baseline accuracy from neural evaluation results."
    )
    parser.add_argument(
        "--neural-scores",
        type=str,
        default="data/results/neural_scores.csv",
        help="Path to neural scores CSV file (default: data/results/neural_scores.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/baseline_score.json",
        help="Path for output JSON file (default: data/results/baseline_score.json)"
    )

    args = parser.parse_args()

    try:
        baseline_accuracy = extract_baseline_score(
            neural_scores_path=args.neural_scores,
            output_path=args.output
        )
        print(f"Baseline accuracy extracted: {baseline_accuracy:.4f}")
        print(f"Saved to: {args.output}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
