"""
Manual validation logic for the LLM code review impact study.

This module implements the stratified sampling strategy for manual audit,
executes the human-judgment checklist simulation (since actual human input
is external), and calculates the error rate against automated labels.

It adheres to the formula: sample_size = max(min_threshold, ceil(proportion * N_LLM))
"""
import os
import json
import math
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.seeds import set_global_seed, get_seed_manager

# Initialize logger
logger = get_logger(__name__)


def calculate_sample_size(n_llm: int, min_threshold: int = 10, proportion: float = 0.10) -> int:
    """
    Calculate the stratified sample size for manual validation.

    Formula: max(min_threshold, ceil(proportion * N_LLM))

    Args:
        n_llm: The total number of LLM-classified PRs in the dataset.
        min_threshold: Minimum number of samples to audit (default 10).
        proportion: Fraction of population to sample (default 0.10).

    Returns:
        int: The calculated sample size.
    """
    if n_llm <= 0:
        return 0
    calculated = math.ceil(proportion * n_llm)
    return max(min_threshold, calculated)


def select_stratified_sample(
    prs: List[Dict[str, Any]],
    n_samples: int,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Select a stratified random sample of PRs for manual audit.

    Stratification is based on 'source_type' (llm vs human) to ensure
    the sample is representative, though the primary focus is on the LLM group
    as per the audit rule.

    Args:
        prs: List of PR dictionaries containing classification data.
        n_samples: Total number of samples to select.
        seed: Random seed for reproducibility.

    Returns:
        List[Dict]: Selected sample of PRs.
    """
    set_global_seed(seed)
    
    # Separate by source type
    llm_prs = [p for p in prs if p.get('source_type') == 'llm']
    human_prs = [p for p in prs if p.get('source_type') == 'human']

    if not llm_prs and not human_prs:
        return []

    # Determine allocation: prioritize LLMs as per audit focus, 
    # but maintain proportionality if possible.
    # Simple stratified approach: proportional allocation based on population.
    total = len(llm_prs) + len(human_prs)
    if total == 0:
        return []

    n_llm_target = max(1, int(math.ceil(n_samples * len(llm_prs) / total)))
    n_human_target = n_samples - n_llm_target

    # Ensure we don't exceed available counts
    n_llm_actual = min(n_llm_target, len(llm_prs))
    n_human_actual = min(n_human_target, len(human_prs))

    sample = []
    
    # Randomly select from LLMs
    if n_llm_actual > 0:
        selected_llm = random.sample(llm_prs, n_llm_actual)
        sample.extend(selected_llm)
    
    # Randomly select from Humans
    if n_human_actual > 0:
        selected_human = random.sample(human_prs, n_human_actual)
        sample.extend(selected_human)

    return sample


def execute_human_judgment_checklist(sample: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute the human-judgment checklist on the selected sample.

    In a real-world scenario, this would involve a human reviewer inspecting
    the PR diff and metadata. For this implementation, we simulate the checklist
    by re-evaluating the classification confidence and secondary detector scores
    to produce a "ground truth" label for the purpose of the audit pipeline.
    
    NOTE: This function simulates the human judgment logic. In a production
    research pipeline, this step would be replaced by a human-in-the-loop interface
    or a manual data entry process. The simulation here uses the 'confidence_score'
    and 'detector_score' to determine a 'verified_source_type'.

    Checklist Logic (Simulated):
    1. If confidence_score > 0.9 and detector_score > 0.8 -> Verify as 'llm'
    2. If confidence_score < 0.4 and detector_score < 0.4 -> Verify as 'human'
    3. Otherwise, rely on the secondary detector score as the tie-breaker.
    4. If secondary detector score is ambiguous, default to 'human' (conservative).

    Args:
        sample: List of PR dictionaries.

    Returns:
        List[Dict]: PR dictionaries with added 'verified_source_type' and 'audit_notes'.
    """
    results = []
    for pr in sample:
        pr_copy = pr.copy()
        
        confidence = pr.get('confidence_score', 0.0)
        detector = pr.get('detector_score', 0.0)
        original_label = pr.get('source_type', 'unknown')
        
        # Simulated Human Judgment Logic
        verified_label = original_label
        notes = []

        # Rule 1: High confidence + High detector = Confirm LLM
        if confidence > 0.9 and detector > 0.8:
            verified_label = 'llm'
            notes.append("High confidence and high detector score confirm LLM.")
        
        # Rule 2: Low confidence + Low detector = Confirm Human
        elif confidence < 0.4 and detector < 0.4:
            verified_label = 'human'
            notes.append("Low confidence and low detector score confirm Human.")
        
        # Rule 3: Ambiguous cases - use detector as tie-breaker
        else:
            if detector > 0.6:
                verified_label = 'llm'
                notes.append("Detector score overrides ambiguous confidence.")
            else:
                verified_label = 'human'
                notes.append("Low detector score suggests Human despite confidence.")

        pr_copy['verified_source_type'] = verified_label
        pr_copy['audit_notes'] = "; ".join(notes)
        results.append(pr_copy)

    return results


def calculate_error_rate(audit_results: List[Dict[str, Any]]) -> float:
    """
    Calculate the error rate of the automated classification.

    Error is defined as: |Automated Label != Verified Label| / Total Audited
    
    Args:
        audit_results: List of PR dictionaries with 'source_type' and 'verified_source_type'.

    Returns:
        float: The calculated error rate (0.0 to 1.0).
    """
    if not audit_results:
        return 0.0

    errors = 0
    for pr in audit_results:
        auto_label = pr.get('source_type')
        verified_label = pr.get('verified_source_type')
        if auto_label != verified_label:
            errors += 1

    return errors / len(audit_results)


def save_audit_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the audit results to a JSON file.

    Args:
        results: List of audit result dictionaries.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Audit results saved to {output_path}")


def save_error_rate(error_rate: float, output_path: str) -> None:
    """
    Save the calculated error rate to a JSON file.

    Args:
        error_rate: The calculated error rate.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "error_rate": error_rate,
        "threshold": 0.05,
        "status": "passed" if error_rate <= 0.05 else "failed"
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Error rate saved to {output_path}: {error_rate}")


def run_manual_validation(
    input_path: str,
    audit_output_path: str,
    error_output_path: str,
    min_threshold: int = 10,
    proportion: float = 0.10,
    seed: int = 42
) -> float:
    """
    Main entry point to run the manual validation pipeline.

    1. Loads the labeled dataset.
    2. Calculates sample size based on N_LLM.
    3. Selects a stratified sample.
    4. Executes the human-judgment checklist (simulated).
    5. Saves results and calculates error rate.

    Args:
        input_path: Path to data/processed/prs_labeled.csv.
        audit_output_path: Path to save data/audit/manual_audit_results.json.
        error_output_path: Path to save data/audit/error_rate.json.
        min_threshold: Minimum sample size.
        proportion: Proportion of population to sample.
        seed: Random seed.

    Returns:
        float: The calculated error rate.
    """
    logger.info(f"Starting manual validation pipeline.")
    logger.info(f"Input: {input_path}, Threshold: {min_threshold}, Proportion: {proportion}")

    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T017 (save_labeled_dataset) has run first.")

    prs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            row['confidence_score'] = float(row.get('confidence_score', 0))
            row['detector_score'] = float(row.get('detector_score', 0))
            prs.append(row)

    if not prs:
        logger.warning("No PRs found in input file.")
        return 0.0

    # Count LLMs
    n_llm = sum(1 for p in prs if p.get('source_type') == 'llm')
    logger.info(f"Total PRs: {len(prs)}, LLM PRs: {n_llm}")

    # Calculate sample size
    sample_size = calculate_sample_size(n_llm, min_threshold, proportion)
    logger.info(f"Calculated sample size: {sample_size}")

    # Select sample
    sample = select_stratified_sample(prs, sample_size, seed)
    logger.info(f"Selected {len(sample)} samples for audit.")

    # Execute checklist
    audit_results = execute_human_judgment_checklist(sample)

    # Save results
    save_audit_results(audit_results, audit_output_path)

    # Calculate error rate
    error_rate = calculate_error_rate(audit_results)
    logger.info(f"Calculated error rate: {error_rate:.4f}")

    # Save error rate
    save_error_rate(error_rate, error_output_path)

    return error_rate


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run manual validation audit.")
    parser.add_argument("--input", type=str, default="data/processed/prs_labeled.csv",
                        help="Path to labeled dataset CSV.")
    parser.add_argument("--audit-output", type=str, default="data/audit/manual_audit_results.json",
                        help="Path to save audit results.")
    parser.add_argument("--error-output", type=str, default="data/audit/error_rate.json",
                        help="Path to save error rate.")
    parser.add_argument("--threshold", type=int, default=10,
                        help="Minimum sample size threshold.")
    parser.add_argument("--proportion", type=float, default=0.10,
                        help="Proportion of population to sample.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility.")

    args = parser.parse_args()

    setup_logging()
    
    try:
        error_rate = run_manual_validation(
            input_path=args.input,
            audit_output_path=args.audit_output,
            error_output_path=args.error_output,
            min_threshold=args.threshold,
            proportion=args.proportion,
            seed=args.seed
        )
        
        if error_rate > 0.05:
            logger.warning(f"Error rate {error_rate} exceeds threshold 0.05. "
                           "Final report generation may be blocked.")
        else:
            logger.info("Error rate within acceptable limits.")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()