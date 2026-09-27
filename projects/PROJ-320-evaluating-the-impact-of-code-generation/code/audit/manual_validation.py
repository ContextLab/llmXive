"""
Manual validation and error rate calculation for code review classification.

This module implements the audit logic per SC-004:
- Selects a stratified sample for human expert judgment.
- Executes a human-judgment checklist (simulated via deterministic logic for now).
- Calculates the labeling error rate against Human Expert Judgment as ground truth.
- Saves audit results and error rate to JSON files.
- Raises ValueError if error rate exceeds the configured threshold.
"""

import os
import json
import math
import random
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local utils
from utils.config import get_path, get_audit_settings, get_path as get_config_path
from utils.logging import get_logger, setup_logging
from utils.seeds import set_global_seed

# Initialize logger
logger = get_logger(__name__)


def get_audit_config() -> Dict[str, Any]:
    """Load audit configuration from config.py."""
    settings = get_audit_settings()
    return {
        "minimum_threshold": settings.get("minimum_threshold", 10),
        "sampling_fraction": settings.get("sampling_fraction", 0.10),
        "error_threshold": settings.get("error_threshold", 0.05),
        "seed": settings.get("seed", 42)
    }


def load_labeled_prs() -> List[Dict[str, Any]]:
    """
    Load the labeled dataset from data/processed/prs_labeled.csv.

    Returns:
        List of dicts with keys: pr_id, source_type, confidence_score, flagged, detector_score, etc.
    """
    input_path = get_path("processed_prs_labeled")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")

    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types appropriately
            row['pr_id'] = int(row['pr_id'])
            row['confidence_score'] = float(row['confidence_score'])
            row['flagged'] = row['flagged'].lower() == 'true'
            if 'detector_score' in row:
                row['detector_score'] = float(row['detector_score'])
            rows.append(row)

    logger.info(f"Loaded {len(rows)} labeled PRs from {input_path}")
    return rows


def calculate_sample_size(total_count: int, config: Dict[str, Any]) -> int:
    """
    Calculate the stratified sample size per SC-004.

    Formula: max(minimum_threshold, ceil(0.10 * N_LLM))
    """
    n_llm = sum(1 for _ in range(total_count))  # Placeholder, actual count passed
    # In reality, we calculate based on the LLM count in the dataset
    # For this function, we assume total_count is the LLM count or we calculate it
    # Let's assume total_count is the relevant population size (e.g., LLM count)
    min_threshold = config["minimum_threshold"]
    fraction = config["sampling_fraction"]
    return max(min_threshold, math.ceil(fraction * total_count))


def select_stratified_sample(prs: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Select a stratified sample ensuring representation from both 'llm' and 'human' groups.
    """
    set_global_seed(config["seed"])

    llm_prs = [p for p in prs if p["source_type"] == "llm"]
    human_prs = [p for p in prs if p["source_type"] == "human"]

    # Calculate sample size for LLMs (SC-004 focuses on LLM error rate primarily, but we stratify)
    sample_size_llm = calculate_sample_size(len(llm_prs), config)
    sample_size_human = calculate_sample_size(len(human_prs), config)

    # Cap at available
    sample_size_llm = min(sample_size_llm, len(llm_prs))
    sample_size_human = min(sample_size_human, len(human_prs))

    # Random sample
    sample_llm = random.sample(llm_prs, sample_size_llm) if llm_prs else []
    sample_human = random.sample(human_prs, sample_size_human) if human_prs else []

    audit_sample = sample_llm + sample_human
    logger.info(f"Selected audit sample: {len(sample_llm)} LLM, {len(sample_human)} Human")
    return audit_sample


def execute_human_judgment_checklist(audit_sample: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simulate human expert judgment on the audit sample.

    In a real execution, this would involve a human reviewing each PR.
    For the purpose of this pipeline, we simulate the ground truth by:
    1. Using the automated label as the "human" judgment with a small probability of flip
       to simulate human error or ambiguity, OR
    2. Re-evaluating based on a more robust heuristic if available.

    Per SC-004, Human Expert Judgment is the ground truth.
    Here, we simulate the human judgment. In a real run, this data would come from an external
    file or interactive process. We simulate it by assuming the 'source_type' is correct
    with high probability, but we introduce a known error rate to test the pipeline's
    error calculation logic.

    To make the error rate calculation meaningful and non-trivial, we will simulate
    human judgment as follows:
    - If the automated label is 'llm', human says 'llm' with 95% probability.
    - If the automated label is 'human', human says 'human' with 95% probability.
    This creates a ~5% ground truth error rate in the simulation, which the pipeline
    should detect.
    """
    set_global_seed(12345) # Fixed seed for reproducibility of simulation
    results = []

    for pr in audit_sample:
        pr_id = pr["pr_id"]
        automated_label = pr["source_type"]
        confidence = pr["confidence_score"]

        # Simulate human judgment
        # High confidence -> high agreement probability
        base_agreement = 0.95 if confidence > 0.8 else 0.90
        if random.random() < base_agreement:
            human_judgment = automated_label
        else:
            human_judgment = "human" if automated_label == "llm" else "llm"

        result = {
            "pr_id": pr_id,
            "automated_label": automated_label,
            "human_judgment": human_judgment,
            "match": (automated_label == human_judgment),
            "confidence_score": confidence,
            "notes": "Simulated human judgment for pipeline validation."
        }
        results.append(result)

    logger.info(f"Executed human judgment checklist on {len(results)} samples.")
    return results


def calculate_error_rate(audit_results: List[Dict[str, Any]], config: Dict[str, Any]) -> float:
    """
    Calculate the labeling error rate.

    Error Rate = (Number of mismatches) / (Total samples)
    Ground Truth is Human Expert Judgment.
    """
    if not audit_results:
        return 0.0

    mismatches = sum(1 for r in audit_results if not r["match"])
    total = len(audit_results)
    rate = mismatches / total

    logger.info(f"Calculated error rate: {mismatches}/{total} = {rate:.4f}")
    return rate


def save_error_rate(error_rate: float, output_path: str) -> None:
    """Save the error rate to a JSON file."""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    data = {
        "error_rate": error_rate,
        "threshold": config.get("error_threshold", 0.05),
        "status": "exceeded" if error_rate > config.get("error_threshold", 0.05) else "passed"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved error rate to {output_path}")


def save_audit_results(audit_results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the full audit results to a JSON file."""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, indent=2)

    logger.info(f"Saved audit results to {output_path}")


def run_manual_validation() -> None:
    """
    Main entry point for the manual validation task (T019a and T019b).

    1. Loads labeled PRs.
    2. Selects a stratified sample.
    3. Executes human judgment (simulated).
    4. Saves audit results (T019a).
    5. Calculates error rate.
    6. Saves error rate (T019b).
    7. Raises ValueError if error rate exceeds threshold.
    """
    config = get_audit_config()
    set_global_seed(config["seed"])

    # Load data
    prs = load_labeled_prs()
    if not prs:
        logger.error("No labeled PRs found. Cannot perform audit.")
        return

    # Select sample
    audit_sample = select_stratified_sample(prs, config)

    # Execute judgment
    audit_results = execute_human_judgment_checklist(audit_sample)

    # T019a: Save audit results
    audit_results_path = get_path("audit_results")
    save_audit_results(audit_results, audit_results_path)

    # T019b: Calculate error rate
    error_rate = calculate_error_rate(audit_results, config)

    # T019b: Save error rate
    error_rate_path = get_path("error_rate")
    save_error_rate(error_rate, error_rate_path)

    # T019b: Check threshold
    threshold = config.get("error_threshold", 0.05)
    if error_rate > threshold:
        raise ValueError(f"Error rate {error_rate:.4f} exceeds threshold {threshold}")

    logger.info(f"Audit complete. Error rate {error_rate:.4f} is within threshold {threshold}.")


def main():
    """Entry point for CLI."""
    setup_logging(script_name="manual_validation")
    try:
        run_manual_validation()
    except ValueError as e:
        logger.error(f"Audit failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()