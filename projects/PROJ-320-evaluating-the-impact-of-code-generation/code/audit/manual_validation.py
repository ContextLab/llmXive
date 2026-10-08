"""
Manual Validation Audit Runner (T019b).

Implements a CLI-based audit runner with file polling for human-in-the-loop validation.
This script orchestrates the manual audit process defined in SC-004.

Workflow:
1. Loads labeled PRs and the checklist template.
2. Selects a stratified sample based on T009 logic.
3. Generates `audit_input.jsonl` for human review.
4. Polls the input file for human updates (human_label, human_confidence).
5. Calculates error rates and validates ground truth.
6. Saves results to `data/audit/manual_audit_results.json` and `data/audit/error_rate.json`.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports matching API surface
from utils.logging import get_logger, setup_logging
from utils.config import get_audit_settings, get_path
from utils.seeds import set_global_seed


# --- Configuration & Helpers ---

def get_audit_config() -> Dict[str, Any]:
    """Retrieve audit configuration from utils.config."""
    return get_audit_settings()

def load_labeled_prs(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load PRs from the labeled dataset CSV."""
    if path is None:
        path = str(get_path("processed_prs_labeled"))
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Labeled dataset not found at {path}. "
                                "Ensure T017 (save_labeled_dataset) has completed.")
    
    prs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types
            row["pr_id"] = int(row["pr_id"])
            row["confidence_score"] = float(row["confidence_score"])
            row["detector_score"] = float(row["detector_score"])
            row["flagged"] = row["flagged"].lower() == "true"
            prs.append(row)
    return prs

def load_checklist_template(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load the manual audit checklist template."""
    if path is None:
        path = str(get_path("manual_audit_checklist"))
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checklist template not found at {path}. "
                                "Ensure T019a has created the template.")
    
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def calculate_sample_size(N_llm: int, min_threshold: int = 10, scaling_factor: float = 0.1) -> int:
    """
    Calculate sample size for manual audit.
    Logic from T009: max(min_threshold, floor(N * scaling_factor))
    """
    return max(min_threshold, int(N_llm * scaling_factor))

def select_stratified_sample(prs: List[Dict[str, Any]], sample_size: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Select a stratified sample of PRs for manual audit.
    Stratifies by source_type (llm vs human) to ensure representation.
    """
    set_global_seed(seed)
    
    llm_prs = [p for p in prs if p["source_type"] == "llm"]
    human_prs = [p for p in prs if p["source_type"] == "human"]
    
    # Calculate proportional allocation
    n_llm = min(len(llm_prs), int(sample_size * (len(llm_prs) / len(prs))))
    n_human = sample_size - n_llm
    
    # Ensure we don't exceed available data
    n_llm = min(n_llm, len(llm_prs))
    n_human = min(n_human, len(human_prs))
    
    import random
    random.seed(seed)
    
    sample_llm = random.sample(llm_prs, n_llm) if n_llm > 0 else []
    sample_human = random.sample(human_prs, n_human) if n_human > 0 else []
    
    return sample_llm + sample_human

def generate_audit_input(sample: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate the JSONL input file for human auditors.
    Includes PR details and placeholder fields for human input.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for pr in sample:
            record = {
                "pr_id": pr["pr_id"],
                "source_type": pr["source_type"],
                "confidence_score": pr["confidence_score"],
                "detector_score": pr["detector_score"],
                "automated_label": pr["source_type"],
                "diff_summary": pr.get("diff_summary", "N/A"),
                "human_label": None,  # To be filled by human
                "human_confidence": None
            }
            f.write(json.dumps(record) + "\n")

def poll_for_updates(input_path: str, interval: int = 10, max_wait: int = 60) -> Optional[Dict[str, Any]]:
    """
    Poll the input file for updates.
    Returns the first record that has been updated by a human (has human_label).
    """
    start_time = time.time()
    last_mtime = 0.0
    
    while time.time() - start_time < max_wait:
        if not os.path.exists(input_path):
            time.sleep(interval)
            continue
        
        current_mtime = os.path.getmtime(input_path)
        
        # Check if file has changed since last check
        if current_mtime > last_mtime:
            last_mtime = current_mtime
            
            # Read and check for updates
            with open(input_path, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if record.get("human_label") is not None:
                        return record
        
        time.sleep(interval)
    
    return None

def calculate_error_rate(audit_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate error rates based on audit results.
    Compares automated_label vs human_label.
    """
    total = len(audit_results)
    if total == 0:
        return {"error_rate": 0.0, "count": 0}
    
    errors = 0
    for record in audit_results:
        if record.get("automated_label") != record.get("human_label"):
            errors += 1
    
    return {
        "error_rate": errors / total,
        "total_audited": total,
        "errors": errors
    }

def validate_ground_truth(audit_results: List[Dict[str, Any]], detector_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Validate ground truth for high-confidence cases.
    Compares human_label vs detector_score for high-confidence automated labels.
    """
    high_conf_cases = [r for r in audit_results if r.get("detector_score", 0) >= detector_threshold]
    
    if not high_conf_cases:
        return {"valid": True, "reason": "No high-confidence cases found"}
    
    mismatches = 0
    for r in high_conf_cases:
        if r.get("automated_label") != r.get("human_label"):
            mismatches += 1
    
    return {
        "high_confidence_cases": len(high_conf_cases),
        "mismatches": mismatches,
        "validation_rate": 1.0 - (mismatches / len(high_conf_cases)) if high_conf_cases else 1.0
    }

def save_audit_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the full audit results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def save_error_rate(error_data: Dict[str, Any], output_path: str) -> None:
    """Save the error rate metrics to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(error_data, f, indent=2)

# --- Main Execution ---

def run_manual_validation(
    input_csv: str,
    checklist_csv: str,
    output_dir: str,
    poll_interval: int = 10,
    max_poll_time: int = 60,
    seed: int = 42
) -> None:
    """
    Main orchestration function for the manual validation audit.
    
    1. Load data.
    2. Select stratified sample.
    3. Generate audit input.
    4. Poll for human updates.
    5. Calculate metrics.
    6. Save results.
    """
    logger = get_logger()
    logger.log("audit_start", input=input_csv, output_dir=output_dir)
    
    # Paths
    audit_input_path = os.path.join(output_dir, "audit_input.jsonl")
    results_output_path = os.path.join(output_dir, "manual_audit_results.json")
    error_rate_output_path = os.path.join(output_dir, "error_rate.json")
    
    # 1. Load data
    logger.log("loading_data", input=input_csv, checklist=checklist_csv)
    prs = load_labeled_prs(input_csv)
    checklist = load_checklist_template(checklist_csv)
    
    # 2. Calculate sample size and select sample
    N_llm = len([p for p in prs if p["source_type"] == "llm"])
    sample_size = calculate_sample_size(N_llm)
    logger.log("sample_selected", total_prs=len(prs), n_llm=N_llm, sample_size=sample_size)
    
    sample = select_stratified_sample(prs, sample_size, seed=seed)
    
    # 3. Generate audit input
    logger.log("generating_audit_input", path=audit_input_path)
    generate_audit_input(sample, audit_input_path)
    
    print(f"Audit input generated: {audit_input_path}")
    print(f"Please manually label {len(sample)} PRs in this file.")
    print(f"Set 'human_label' to 'llm' or 'human' and 'human_confidence' (0-1).")
    print(f"Script will poll for updates every {poll_interval}s (max {max_poll_time}s).")
    
    # 4. Poll for updates
    # In a real interactive scenario, we would loop. For this script, we simulate
    # the polling by checking if the file has been modified by the user.
    # Since we cannot block indefinitely in an automated runner, we do one pass
    # or wait if the file exists and is being edited.
    
    updated_results = []
    start_time = time.time()
    
    # Initial read
    if os.path.exists(audit_input_path):
        with open(audit_input_path, "r", encoding="utf-8") as f:
            for line in f:
                updated_results.append(json.loads(line))
    
    # Polling loop
    while time.time() - start_time < max_poll_time:
        current_results = []
        if os.path.exists(audit_input_path):
            with open(audit_input_path, "r", encoding="utf-8") as f:
                for line in f:
                    current_results.append(json.loads(line))
        
        # Check if we have new labels
        if any(r.get("human_label") for r in current_results):
            updated_results = current_results
            print("New labels detected. Saving results...")
            break
        
        time.sleep(poll_interval)
    
    # 5. Calculate Error Rate and Validate Ground Truth
    error_metrics = calculate_error_rate(updated_results)
    ground_truth_validation = validate_ground_truth(updated_results)
    
    # 6. Save results
    save_audit_results(updated_results, results_output_path)
    save_error_rate(error_metrics, error_rate_output_path)
    
    logger.log("audit_complete", error_rate=error_metrics["error_rate"], 
               output_results=results_output_path, output_error=error_rate_output_path)
    
    print(f"Audit complete. Results saved to {results_output_path}")
    print(f"Error rate: {error_metrics['error_rate']:.4f} ({error_metrics['errors']}/{error_metrics['total_audited']})")
    print(f"Ground truth validation rate: {ground_truth_validation.get('validation_rate', 0):.4f}")

def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Manual Validation Audit Runner (T019b)")
    parser.add_argument("--input", type=str, default=None, help="Path to prs_labeled.csv")
    parser.add_argument("--checklist", type=str, default=None, help="Path to manual_audit_checklist.csv")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for audit files")
    parser.add_argument("--poll-interval", type=int, default=10, help="Polling interval in seconds")
    parser.add_argument("--max-poll-time", type=int, default=60, help="Maximum polling time in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    
    args = parser.parse_args()
    
    # Setup logging
    log_config = setup_logging()
    logger = get_logger()
    
    # Determine paths
    if args.input is None:
        args.input = str(get_path("processed_prs_labeled"))
    if args.checklist is None:
        args.checklist = str(get_path("manual_audit_checklist"))
    if args.output_dir is None:
        args.output_dir = str(get_path("audit_dir"))
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        run_manual_validation(
            input_csv=args.input,
            checklist_csv=args.checklist,
            output_dir=args.output_dir,
            poll_interval=args.poll_interval,
            max_poll_time=args.max_poll_time,
            seed=args.seed
        )
    except FileNotFoundError as e:
        logger.log("audit_failed", error=str(e))
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.log("audit_failed", error=str(e))
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()