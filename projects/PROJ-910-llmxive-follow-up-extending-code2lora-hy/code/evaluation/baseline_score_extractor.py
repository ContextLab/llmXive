"""
Baseline Score Extractor for User Story 3 (Sensitivity Analysis).

This module implements T031a: Extract the baseline accuracy score from the neural
evaluation results (T021/T024) and save it to data/results/baseline_score.json.

It relies on the evaluation runner's output (neural_scores.csv) to compute the
mean exact-match score, which serves as the baseline for sensitivity analysis.
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path


def calculate_baseline_accuracy(
    scores_path: str,
    score_column: str = "exact_match"
) -> float:
    """
    Calculate the mean exact-match score from the neural evaluation results.

    Args:
        scores_path: Path to the CSV file containing neural evaluation scores.
                     Expected to be 'data/results/neural_scores.csv'.
        score_column: The column name in the CSV containing the score values.
                      Default is 'exact_match'.

    Returns:
        float: The mean score (baseline accuracy).

    Raises:
        FileNotFoundError: If the scores file does not exist.
        ValueError: If the score column is missing or contains non-numeric values.
    """
    path = Path(scores_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Neural scores file not found at {scores_path}. "
            "Ensure T021 (evaluation runner) has been executed first."
        )

    scores = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if score_column not in reader.fieldnames:
            raise ValueError(
                f"Column '{score_column}' not found in {scores_path}. "
                f"Available columns: {reader.fieldnames}"
            )

        for row in reader:
            try:
                score = float(row[score_column])
                scores.append(score)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid score value '{row[score_column]}' in row: {row}"
                )

    if not scores:
        raise ValueError(f"No valid scores found in {scores_path}")

    return sum(scores) / len(scores)


def save_baseline_score(
    baseline_accuracy: float,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save the baseline accuracy score to a JSON file.

    Args:
        baseline_accuracy: The calculated baseline accuracy.
        output_path: Path to save the JSON file (e.g., 'data/results/baseline_score.json').
        metadata: Optional dictionary of additional metadata to include.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "baseline_accuracy": baseline_accuracy,
        "source": "neural_scores.csv",
        "metadata": metadata or {}
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def extract_baseline_score(
    scores_path: str = "data/results/neural_scores.csv",
    output_path: str = "data/results/baseline_score.json",
    score_column: str = "exact_match"
) -> float:
    """
    Main entry point to extract and save the baseline score.

    This function orchestrates the calculation and saving of the baseline accuracy.

    Args:
        scores_path: Path to the neural scores CSV.
        output_path: Path to save the baseline score JSON.
        score_column: Column name for the score.

    Returns:
        float: The calculated baseline accuracy.
    """
    accuracy = calculate_baseline_accuracy(scores_path, score_column)
    save_baseline_score(accuracy, output_path)
    return accuracy


def main():
    """CLI entry point for T031a."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract baseline accuracy from neural evaluation results."
    )
    parser.add_argument(
        "--scores",
        type=str,
        default="data/results/neural_scores.csv",
        help="Path to the neural scores CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/baseline_score.json",
        help="Path to save the baseline score JSON."
    )
    parser.add_argument(
        "--column",
        type=str,
        default="exact_match",
        help="Column name containing the scores."
    )

    args = parser.parse_args()

    try:
        accuracy = extract_baseline_score(
            scores_path=args.scores,
            output_path=args.output,
            score_column=args.column
        )
        print(f"Baseline accuracy extracted: {accuracy:.4f}")
        print(f"Saved to: {args.output}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error processing scores: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
