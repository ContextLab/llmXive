import csv
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import existing utilities from sibling modules if available, otherwise define locally
# Based on API surface, we assume load_processed_data exists in a shared context or define minimal loaders here
# For T019d, we focus on the missing file handling logic.

def load_processed_data(file_path: str) -> List[Dict[str, Any]]:
    """Load processed PR data from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_annotations(file_path: str) -> List[Dict[str, Any]]:
    """Load human annotations from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Annotations file not found: {file_path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def stratify_data(data: List[Dict[str, Any]], strata_keys: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by strata keys."""
    strata = {}
    for item in data:
        key = tuple(str(item[k]) for k in strata_keys)
        if key not in strata:
            strata[key] = []
        strata[key].append(item)
    return strata

def perform_stratified_sampling(strata: Dict[str, List[Dict[str, Any]]], sample_size: int) -> List[Dict[str, Any]]:
    """Perform stratified sampling from grouped data."""
    sample = []
    total_items = sum(len(v) for v in strata.values())
    if total_items == 0:
        return sample
    
    # Simple proportional sampling logic for this task
    for key, items in strata.items():
        # Ensure we don't sample more than available
        n = min(sample_size, len(items))
        if n > 0:
            sample.extend(random.sample(items, n))
    return sample

def generate_sample_list_for_review(data: List[Dict[str, Any]], output_path: str, sample_size: int = 50):
    """Generate a CSV of non-AI labeled PRs for manual review."""
    non_ai_data = [pr for pr in data if pr.get('is_ai_assisted', '0') == '0']
    
    strata = stratify_data(non_ai_data, ['repo_name', 'lines_changed'])
    sampled = perform_stratified_sampling(strata, sample_size)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['pr_id', 'repo_name', 'lines_changed'])
        writer.writeheader()
        for pr in sampled:
            writer.writerow({
                'pr_id': pr['pr_id'],
                'repo_name': pr['repo_name'],
                'lines_changed': pr.get('lines_changed', '')
            })

def generate_annotation_template(output_path: str, sample_list_path: str):
    """Generate a blank CSV template for human annotators."""
    sample_data = []
    if os.path.exists(sample_list_path):
        with open(sample_list_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sample_data = list(reader)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header comment as requested
        writer.writerow(['# Annotation Instructions'])
        writer.writerow(['# Open this file in a text editor. For each PR ID, manually review the PR on GitHub.'])
        writer.writerow(['# If you see AI-generated code (e.g., Copilot suggestions), set is_ai_assisted to 1, otherwise 0.'])
        writer.writerow(['# Save the file as annotations.csv.'])
        writer.writerow([])
        writer.writerow(['pr_id', 'is_ai_assisted'])
        
        for row in sample_data:
            writer.writerow([row['pr_id'], ''])

def calculate_false_negative_rate(annotations: List[Dict[str, Any]], processed_data: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """Calculate false negative rate based on annotations."""
    processed_dict = {pr['pr_id']: pr for pr in processed_data}
    
    misclassified_ai = 0
    total_sampled = 0
    details = {'correct': 0, 'false_negative': 0, 'false_positive': 0, 'true_negative': 0}
    
    for ann in annotations:
        pr_id = ann['pr_id']
        human_label = int(ann.get('is_ai_assisted', 0))
        
        if pr_id in processed_dict:
            pr_data = processed_dict[pr_id]
            auto_label = int(pr_data.get('is_ai_assisted', 0))
            total_sampled += 1
            
            if human_label == 1 and auto_label == 0:
                misclassified_ai += 1
                details['false_negative'] += 1
            elif human_label == 0 and auto_label == 1:
                details['false_positive'] += 1
            elif human_label == 1 and auto_label == 1:
                details['correct'] += 1
            else:
                details['true_negative'] += 1
    
    fdr = misclassified_ai / total_sampled if total_sampled > 0 else 0.0
    return fdr, details

def save_validation_report(report_data: Dict[str, Any], output_path: str):
    """Save validation report to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=report_data.keys())
        writer.writeheader()
        writer.writerow(report_data)

def handle_missing_annotations(processed_data_path: str, annotations_path: str, report_output_path: str, final_report_flag: bool = False):
    """
    Handle missing real data (annotations.csv).
    Logs CRITICAL warning, flags validation status as 'UNVALIDATED',
    and returns a status indicating heuristic-only classification.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not Path(annotations_path).exists():
        logger.critical(f"CRITICAL: Annotations file '{annotations_path}' is missing. Cannot perform human validation.")
        logger.critical("Proceeding with analysis using heuristic-only classification.")
        
        # Create a validation report indicating UNVALIDATED status
        report_data = {
            'status': 'UNVALIDATED',
            'reason': 'Missing annotations.csv',
            'false_negative_rate': None,
            'sample_size': 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_validation_report(report_data, report_output_path)
        
        # If this is meant to update a final report flag
        if final_report_flag:
            logger.warning("Final report flag set to 'UNVALIDATED'.")
        
        return {
            'status': 'UNVALIDATED',
            'reason': 'Missing annotations.csv',
            'proceed_with_heuristic': True
        }
    
    return None

def main():
    """Main entry point for spot check validation pipeline."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Paths
    processed_data_path = "data/processed/pr_turnaround.csv"
    sample_list_path = "data/spot_check/sample_list.csv"
    template_path = "data/spot_check/annotation_template.csv"
    annotations_path = "data/spot_check/annotations.csv"
    validation_report_path = "data/spot_check/validation_report.csv"

    # Step 1: Handle missing annotations (T019d requirement)
    # Check if annotations exist. If not, log critical warning and flag status.
    if not Path(annotations_path).exists():
        result = handle_missing_annotations(
            processed_data_path, 
            annotations_path, 
            validation_report_path,
            final_report_flag=True
        )
        if result and result['status'] == 'UNVALIDATED':
            logger.info("Validation pipeline halted at ingestion due to missing annotations. Status: UNVALIDATED.")
            # We do not proceed to calculate FNR, but we log that the analysis continues with heuristics.
            return result

    # Step 2: Load processed data (if we reached here, we assume data exists for T019d context)
    try:
        processed_data = load_processed_data(processed_data_path)
    except FileNotFoundError:
        logger.error(f"Processed data not found at {processed_data_path}")
        return

    # Step 3: Load annotations
    try:
        annotations = load_annotations(annotations_path)
    except FileNotFoundError:
        # This case should be caught by handle_missing_annotations, but as a fallback:
        handle_missing_annotations(processed_data_path, annotations_path, validation_report_path, final_report_flag=True)
        return

    # Step 4: Calculate False Negative Rate
    fdr, details = calculate_false_negative_rate(annotations, processed_data)
    
    report_data = {
        'status': 'VALIDATED',
        'false_negative_rate': fdr,
        'sample_size': len(annotations),
        'correct': details['correct'],
        'false_negative': details['false_negative'],
        'false_positive': details['false_positive'],
        'true_negative': details['true_negative'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    save_validation_report(report_data, validation_report_path)
    logger.info(f"Validation report saved to {validation_report_path}. FNR: {fdr:.4f}")

    return report_data

if __name__ == "__main__":
    main()