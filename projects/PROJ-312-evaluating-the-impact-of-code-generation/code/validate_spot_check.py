import csv
import json
import logging
import random
from collections import defaultdict
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

def load_processed_data(filepath: str) -> List[Dict[str, Any]]:
    """Load processed PR data."""
    with open(filepath, 'r') as f:
        return json.load(f)

def stratify_data(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Stratify data by repo and PR size (simulated by commit count)."""
    buckets = defaultdict(list)
    for pr in data:
        # Simulate PR size by number of commit messages
        size_bucket = "small" if len(pr.get('commit_messages', [])) < 5 else "large"
        key = f"{pr['repo_name']}_{size_bucket}"
        buckets[key].append(pr)
    return dict(buckets)

def perform_stratified_sampling(strata: Dict[str, List[Dict[str, Any]]], n: int = 50) -> List[Dict[str, Any]]:
    """Perform stratified random sampling."""
    sample = []
    total_size = sum(len(v) for v in strata.values())
    if total_size == 0:
        return []
    
    # Proportional allocation
    for key, items in strata.items():
        proportion = len(items) / total_size
        n_stratum = max(1, int(n * proportion))
        sample.extend(random.sample(items, min(n_stratum, len(items))))
    
    return sample

def simulate_manual_review(prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simulate manual review to detect false negatives.
    In a real scenario, this would involve human review.
    Here we simulate based on heuristic re-evaluation.
    """
    results = []
    for pr in prs:
        # Simulate: if it's marked non-AI but has "copilot" in any message, it's a FN
        is_false_negative = False
        if not pr['is_ai']:
            for msg in pr.get('commit_messages', []):
                if "copilot" in msg.lower() or "ai-generated" in msg.lower():
                    is_false_negative = True
                    break
        
        results.append({
            "pr_id": pr['pr_id'],
            "repo_name": pr['repo_name'],
            "original_label": "AI" if pr['is_ai'] else "Human",
            "reviewed_label": "AI" if is_false_negative or pr['is_ai'] else "Human",
            "is_false_negative": is_false_negative
        })
    return results

def calculate_false_negative_rate(results: List[Dict[str, Any]]) -> float:
    """Calculate false negative rate from review results."""
    non_ai_count = sum(1 for r in results if r['original_label'] == "Human")
    if non_ai_count == 0:
        return 0.0
    fn_count = sum(1 for r in results if r['is_false_negative'])
    return fn_count / non_ai_count

def save_validation_report(results: List[Dict[str, Any]], output_path: str):
    """Save validation report to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def generate_sample_list_for_review(data: List[Dict[str, Any]], output_path: str, n: int = 50):
    """
    Generate a CSV of non-AI-labeled PR IDs (stratified by repo and PR size) 
    for manual review.
    """
    # Filter for non-AI labeled PRs only
    non_ai_data = [pr for pr in data if not pr.get('is_ai', False)]
    
    if not non_ai_data:
        logger.warning("No non-AI labeled PRs found for spot check.")
        # Write empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id', 'repo_name', 'turnaround_hours', 'size_bucket'])
            writer.writeheader()
        return

    # Stratify the non-AI data
    strata = stratify_data(non_ai_data)
    
    # Perform stratified sampling
    sample = perform_stratified_sampling(strata, n=n)
    
    # Prepare rows for CSV
    rows = []
    for pr in sample:
        size_bucket = "small" if len(pr.get('commit_messages', [])) < 5 else "large"
        rows.append({
            'pr_id': pr['pr_id'],
            'repo_name': pr['repo_name'],
            'turnaround_hours': pr.get('turnaround_hours', 0),
            'size_bucket': size_bucket
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pr_id', 'repo_name', 'turnaround_hours', 'size_bucket'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Generated sample list with {len(rows)} PRs at {output_path}")

def load_annotations(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the manually annotated CSV file produced by T019b.
    Expected columns: pr_id, repo_name, true_label (AI/Human)
    """
    annotations = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotations.append(row)
    return annotations

def calculate_validation_metrics(annotations: List[Dict[str, Any]], processed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compare annotations against the original classification in processed_data.
    Calculate false negative rate and generate a detailed report.
    """
    # Create a lookup for processed data by pr_id
    pr_lookup = {pr['pr_id']: pr for pr in processed_data}
    
    results = []
    fn_count = 0
    non_ai_total = 0
    
    for ann in annotations:
        pr_id = ann['pr_id']
        true_label = ann.get('true_label', '').strip()
        
        if pr_id not in pr_lookup:
            logger.warning(f"PR ID {pr_id} in annotations not found in processed data.")
            continue
        
        original_pr = pr_lookup[pr_id]
        original_is_ai = original_pr.get('is_ai', False)
        original_label = "AI" if original_is_ai else "Human"
        
        # Determine if this is a false negative
        # False Negative: Original was Human (non-AI), but True label is AI
        is_fn = (original_label == "Human" and true_label == "AI")
        
        if original_label == "Human":
            non_ai_total += 1
            if is_fn:
                fn_count += 1
        
        results.append({
            "pr_id": pr_id,
            "repo_name": original_pr['repo_name'],
            "original_label": original_label,
            "true_label": true_label,
            "is_false_negative": is_fn
        })
    
    # Calculate metrics
    fdr = fn_count / non_ai_total if non_ai_total > 0 else 0.0
    
    # Add summary row to results? No, save metrics separately or in the report header.
    # The task asks to save the report to CSV. We will include the metrics in the log
    # and ensure the CSV contains the row-level data.
    # However, T020 says "Save spot-check results to data/spot_check/validation_report.csv".
    # We will include the calculated rate in the filename or just log it, 
    # but usually validation reports include the row-level truth.
    # Let's ensure the CSV has the necessary columns.
    
    return results, fdr

def main():
    """
    Main entry point for T019c: Validate spot check annotations.
    1. Load processed data.
    2. Load annotations from T019b (data/spot_check/annotations.csv).
    3. Compare to calculate false negative rate.
    4. Save validation report to data/spot_check/validation_report.csv.
    """
    logging.basicConfig(level=logging.INFO)
    
    processed_data_path = "data/processed/pr_data.json"
    annotations_path = "data/spot_check/annotations.csv"
    report_output_path = "data/spot_check/validation_report.csv"
    
    # Check if annotations file exists (T019b prerequisite)
    if not os.path.exists(annotations_path):
        logger.error(f"Annotations file not found: {annotations_path}. Pipeline halted waiting for T019b.")
        raise FileNotFoundError(f"Missing required input for T019c: {annotations_path}")
    
    logger.info(f"Loading processed data from {processed_data_path}")
    processed_data = load_processed_data(processed_data_path)
    
    logger.info(f"Loading annotations from {annotations_path}")
    annotations = load_annotations(annotations_path)
    
    if not annotations:
        logger.error("Annotations file is empty.")
        raise ValueError("Annotations file is empty. Cannot calculate validation metrics.")
    
    logger.info("Calculating validation metrics...")
    validation_results, false_negative_rate = calculate_validation_metrics(annotations, processed_data)
    
    logger.info(f"False Negative Rate: {false_negative_rate:.2%} ({false_negative_rate:.4f})")
    
    logger.info(f"Saving validation report to {report_output_path}")
    save_validation_report(validation_results, report_output_path)
    
    logger.info("Pipeline resumed successfully after T019c validation.")

if __name__ == "__main__":
    main()