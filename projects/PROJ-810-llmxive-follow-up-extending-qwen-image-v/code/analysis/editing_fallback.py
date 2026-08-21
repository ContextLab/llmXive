"""
Manual Verification Fallback Logic for User Story 2.

This module implements the fallback mechanism for T032:
If OCR accuracy < 95%, sample failed samples for manual verification.
"""

import json
import random
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
MANUAL_DIR = DATA_DIR / "manual"


def load_ocr_results(ocr_file_path: Path) -> Dict[str, Any]:
    """
    Load OCR verification results from a JSON file.

    Args:
        ocr_file_path: Path to the ocr_accuracy.json file.

    Returns:
        Dictionary containing 'overall_accuracy' and 'failed_samples' (list of dicts).
    """
    if not ocr_file_path.exists():
        raise FileNotFoundError(f"OCR results file not found: {ocr_file_path}")

    with open(ocr_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_overall_accuracy(ocr_results: Dict[str, Any]) -> float:
    """
    Extract the overall accuracy from the OCR results.

    Args:
        ocr_results: Dictionary containing OCR metrics.

    Returns:
        Float representing the overall accuracy (0.0 to 1.0).
    """
    return float(ocr_results.get('overall_accuracy', 0.0))


def get_failed_samples(ocr_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Retrieve the list of samples that failed the OCR verification.

    Args:
        ocr_results: Dictionary containing OCR metrics and sample details.

    Returns:
        List of dictionaries representing failed samples.
    """
    return ocr_results.get('failed_samples', [])


def sample_failed_indices(
    failed_samples: List[Dict[str, Any]],
    max_samples: int = 50,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Randomly sample a subset of failed samples for manual verification.

    Logic:
    - If total failed count < 5, sample all.
    - Otherwise, sample up to max_samples (default 50).
    - Uses a fixed seed for reproducibility.

    Args:
        failed_samples: List of all failed sample records.
        max_samples: Maximum number of samples to select.
        seed: Random seed for reproducibility.

    Returns:
        List of sampled failed sample records.
    """
    if not failed_samples:
        return []

    random.seed(seed)
    count = len(failed_samples)

    if count < 5:
        # If count < 5, sample all
        selected = failed_samples
    else:
        # Sample up to max_samples
        # We use random.sample to pick unique indices
        k = min(max_samples, count)
        indices = random.sample(range(count), k)
        selected = [failed_samples[i] for i in indices]

    return selected


def write_verification_queue(
    sampled_samples: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Write the sampled failed samples to a CSV file for manual verification.

    Args:
        sampled_samples: List of sampled failed sample records.
        output_path: Path to the output CSV file.
    """
    if not sampled_samples:
        # If no samples to verify, create an empty file with headers
        # This satisfies the requirement that the file exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_id', 'source_image', 'expected_text', 'detected_text', 'confidence', 'reason'])
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine headers from the first sample (assuming uniform structure)
    fieldnames = list(sampled_samples[0].keys())
    # Ensure sample_id is first for clarity, if present
    if 'sample_id' in fieldnames:
        fieldnames.remove('sample_id')
        fieldnames.insert(0, 'sample_id')

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sampled_samples)


def main() -> None:
    """
    Main entry point for the Manual Verification Fallback task (T032).

    Logic:
    1. Load OCR results from data/results/ocr_accuracy.json.
    2. Calculate overall accuracy.
    3. If accuracy < 0.95 (95%):
       - Get failed samples.
       - Sample a subset (all if < 5, else up to 50).
       - Write to data/manual/verification_queue.csv.
    4. If accuracy >= 0.95:
       - Create an empty verification_queue.csv (header only) to indicate no action needed.
    """
    ocr_results_path = RESULTS_DIR / "ocr_accuracy.json"
    output_path = MANUAL_DIR / "verification_queue.csv"

    try:
        ocr_results = load_ocr_results(ocr_results_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Cannot proceed without OCR results. Please ensure T029-run has completed.")
        sys.exit(1)

    accuracy = calculate_overall_accuracy(ocr_results)
    print(f"Overall OCR Accuracy: {accuracy:.4f}")

    if accuracy < 0.95:
        print("Accuracy below 95% threshold. Initiating manual verification fallback...")
        failed_samples = get_failed_samples(ocr_results)
        print(f"Total failed samples: {len(failed_samples)}")

        if not failed_samples:
            print("Warning: Accuracy < 95% but no failed_samples found in results.")
            # Still write an empty queue to be safe
            write_verification_queue([], output_path)
        else:
            sampled = sample_failed_indices(failed_samples, max_samples=50, seed=42)
            print(f"Selected {len(sampled)} samples for manual verification.")
            write_verification_queue(sampled, output_path)
            print(f"Verification queue written to: {output_path}")
    else:
        print("Accuracy meets or exceeds 95% threshold. No manual verification required.")
        # Create empty file with headers to indicate status
        write_verification_queue([], output_path)
        print(f"Empty verification queue written to: {output_path}")


if __name__ == "__main__":
    main()
