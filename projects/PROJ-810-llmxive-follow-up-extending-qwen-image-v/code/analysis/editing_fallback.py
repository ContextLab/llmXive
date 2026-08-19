"""
T032: Manual Verification Fallback Implementation.

Logic:
1. Load OCR accuracy results from `data/results/ocr_accuracy.json`.
2. If overall accuracy < 95%, identify failed samples.
3. Randomly sample up to 50 failed samples (using fixed seed 42).
   - If total failures < 5, sample all of them.
4. Write the sampled indices/paths to `data/manual/verification_queue.csv`.
5. If accuracy >= 95%, write an empty queue with a note.
"""

import json
import random
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from itertools import islice

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_MANUAL_DIR = PROJECT_ROOT / "data" / "manual"

OCR_RESULTS_PATH = DATA_RESULTS_DIR / "ocr_accuracy.json"
VERIFICATION_QUEUE_PATH = DATA_MANUAL_DIR / "verification_queue.csv"

# Constants
ACCURACY_THRESHOLD = 0.95
MAX_SAMPLE_SIZE = 50
MIN_SAMPLE_SIZE = 5
RANDOM_SEED = 42


def load_ocr_results() -> Dict[str, Any]:
    """Load the OCR accuracy results JSON."""
    if not OCR_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"OCR results file not found at {OCR_RESULTS_PATH}. "
            "Ensure T029-run has been executed successfully."
        )
    
    with open(OCR_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_overall_accuracy(results: Dict[str, Any]) -> float:
    """Calculate the overall accuracy from the results."""
    # Expecting structure: {"overall_accuracy": float, "samples": [...]}
    # Fallback to manual calculation if structure differs
    if "overall_accuracy" in results:
        return float(results["overall_accuracy"])
    
    samples = results.get("samples", [])
    if not samples:
        return 1.0  # No samples, assume perfect (edge case)
    
    correct_count = sum(1 for s in samples if s.get("is_correct", False))
    return correct_count / len(samples)


def get_failed_samples(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the list of failed samples from the results."""
    samples = results.get("samples", [])
    return [s for s in samples if not s.get("is_correct", False)]


def sample_failed_indices(failed_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Randomly sample failed samples.
    
    Logic:
    - If count < 5, sample all.
    - Otherwise, sample min(50, count).
    - Uses fixed seed for reproducibility.
    """
    count = len(failed_samples)
    if count == 0:
        return []
    
    if count < MIN_SAMPLE_SIZE:
        # Sample all if fewer than 5
        return failed_samples
    
    # Set seed for reproducibility
    random.seed(RANDOM_SEED)
    
    # Determine sample size
    sample_size = min(MAX_SAMPLE_SIZE, count)
    
    # Randomly sample
    # Note: We use random.sample on the list directly
    sampled = random.sample(failed_samples, sample_size)
    
    return sampled


def write_verification_queue(sampled_failures: List[Dict[str, Any]], accuracy: float) -> None:
    """Write the verification queue CSV file."""
    # Ensure directory exists
    DATA_MANUAL_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(VERIFICATION_QUEUE_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            "sample_id", 
            "image_path", 
            "target_text", 
            "predicted_text", 
            "confidence",
            "reason"
        ])
        
        # Metadata comment row (optional, but good for manual review)
        # We write it as a data row with empty first cell if needed, 
        # but standard CSV parsers might skip it. 
        # Instead, we'll just write the data.
        
        if not sampled_failures:
            writer.writerow([
                "", "", "", "", "", 
                f"Accuracy {accuracy:.2%} >= {ACCURACY_THRESHOLD:.2%}. No verification needed."
            ])
            return

        for sample in sampled_failures:
            writer.writerow([
                sample.get("sample_id", ""),
                sample.get("image_path", ""),
                sample.get("target_text", ""),
                sample.get("predicted_text", ""),
                sample.get("confidence", 0.0),
                "OCR Accuracy < 95% - Manual Review Required"
            ])


def main():
    """Main entry point for T032."""
    print(f"Starting T032: Manual Verification Fallback...")
    print(f"Reading OCR results from: {OCR_RESULTS_PATH}")
    
    try:
        results = load_ocr_results()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    accuracy = calculate_overall_accuracy(results)
    print(f"Calculated Overall Accuracy: {accuracy:.2%}")
    
    if accuracy >= ACCURACY_THRESHOLD:
        print(f"Accuracy ({accuracy:.2%}) meets threshold ({ACCURACY_THRESHOLD:.2%}). "
              f"Creating empty verification queue.")
        sampled = []
    else:
        print(f"Accuracy ({accuracy:.2%}) below threshold ({ACCURACY_THRESHOLD:.2%}). "
              f"Identifying failed samples for manual verification.")
        failed_samples = get_failed_samples(results)
        print(f"Total failed samples: {len(failed_samples)}")
        sampled = sample_failed_indices(failed_samples)
        print(f"Selected {len(sampled)} samples for manual verification.")
    
    write_verification_queue(sampled, accuracy)
    print(f"Verification queue written to: {VERIFICATION_QUEUE_PATH}")
    print("T032 completed successfully.")


if __name__ == "__main__":
    main()
