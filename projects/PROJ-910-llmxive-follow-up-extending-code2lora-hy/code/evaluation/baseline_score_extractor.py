"""
Baseline Score Extractor Module.

This module handles the extraction and persistence of the baseline accuracy score
derived from the neural encoder evaluation results (T021/T024).

It ensures that `data/results/baseline_score.json` is written with a single key
`score` (float), as required by T031b and T032.
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Importing from the established API surface
from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path


def calculate_baseline_accuracy(
    results_path: Optional[Path] = None
) -> float:
    """
    Calculate the baseline accuracy score from the neural evaluation results.

    This function loads the exact-match scores from `data/results/neural_scores.csv`
    (produced by the neural baseline evaluation in T021/T024) and computes the mean
    exact-match score.

    Args:
        results_path: Optional path to the neural scores CSV. Defaults to
                      `data/results/neural_scores.csv`.

    Returns:
        float: The mean exact-match score (baseline accuracy).

    Raises:
        FileNotFoundError: If the neural scores CSV does not exist.
        ValueError: If the CSV is empty or lacks the 'exact_match' column.
    """
    if results_path is None:
        results_path = Path("data/results/neural_scores.csv")

    if not results_path.exists():
        raise FileNotFoundError(
            f"Neural scores file not found at {results_path}. "
            "Ensure T021 (neural evaluation) has completed successfully."
        )

    scores = []
    with open(results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "exact_match" not in reader.fieldnames:
            raise ValueError(
                f"CSV {results_path} must contain an 'exact_match' column."
            )

        for row in reader:
            try:
                score = float(row["exact_match"])
                scores.append(score)
            except (ValueError, TypeError):
                continue

    if not scores:
        raise ValueError(
            f"No valid 'exact_match' scores found in {results_path}."
        )

    return sum(scores) / len(scores)


def save_baseline_score(score: float, output_path: Optional[Path] = None) -> Path:
    """
    Save the baseline accuracy score to a JSON file.

    This function writes the score to `data/results/baseline_score.json` with the
    exact structure required: `{"score": <float>}`.

    Args:
        score: The baseline accuracy score (float).
        output_path: Optional path for the output JSON. Defaults to
                     `data/results/baseline_score.json`.

    Returns:
        Path: The path to the written JSON file.

    Raises:
        IOError: If the file cannot be written.
    """
    if output_path is None:
        output_path = Path("data/results/baseline_score.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "score": float(score)
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output_path


def extract_baseline_score(
    results_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> float:
    """
    Orchestrate the extraction and saving of the baseline score.

    This is the high-level function that calculates the baseline accuracy from
    the neural scores and persists it to the required JSON file.

    Args:
        results_path: Path to the neural scores CSV.
        output_path: Path for the output JSON file.

    Returns:
        float: The extracted baseline score.
    """
    score = calculate_baseline_accuracy(results_path)
    save_baseline_score(score, output_path)
    return score


def main() -> int:
    """
    CLI entry point for extracting and saving the baseline score.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    import sys
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        results_csv = Path("data/results/neural_scores.csv")
        output_json = Path("data/results/baseline_score.json")

        if not results_csv.exists():
            logger.error(
                f"Neural scores file not found at {results_csv}. "
                "Please run T021 (neural evaluation) first."
            )
            return 1

        logger.info(f"Calculating baseline accuracy from {results_csv}...")
        score = calculate_baseline_accuracy(results_csv)
        logger.info(f"Calculated baseline accuracy: {score:.4f}")

        logger.info(f"Saving baseline score to {output_json}...")
        save_baseline_score(score, output_json)
        logger.info("Baseline score saved successfully.")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
