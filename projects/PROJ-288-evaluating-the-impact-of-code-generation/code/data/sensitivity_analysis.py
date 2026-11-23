import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from existing API surface
from data.classify import load_sampled_prs, calculate_heuristic_scores, check_disclosure_keywords
from data.logging_config import get_logger

logger = get_logger(__name__)

def load_heuristic_scores_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load heuristic scores from the processed CSV file.
    Expects 'data/processed/sampled_prs.csv' which contains heuristic columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    records = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric string fields to float
            record = {}
            for k, v in row.items():
                try:
                    # Try to convert to float if possible
                    record[k] = float(v)
                except (ValueError, TypeError):
                    record[k] = v
            records.append(record)
    
    logger.info(f"Loaded {len(records)} records from {file_path}")
    return records

def calculate_sensitivity_metrics(
    records: List[Dict[str, Any]], 
    thresholds: List[float]
) -> List[Dict[str, Any]]:
    """
    Calculate sensitivity metrics (error rates) for a range of thresholds.
    
    Context: The primary label is binary (Disclosing/Non-Disclosing) based on keywords.
    This analysis sweeps thresholds on the *heuristic scores* (covariates) to see
    how classification quality changes if we were to use heuristics as a proxy.
    
    We compare the heuristic-based prediction (at threshold T) against the 
    'manual_label' (ground truth) if available, or the keyword label if manual is missing.
    
    Returns a list of metrics dicts: {threshold, true_positives, false_positives, 
    true_negatives, false_negatives, precision, recall, f1, error_rate}
    """
    if not records:
        logger.warning("No records provided for sensitivity analysis.")
        return []

    metrics_list = []
    
    # Identify ground truth column. Prefer 'manual_label' if it exists in data, 
    # otherwise fallback to 'origin_label' (keyword-based).
    # We assume 'manual_label' is 1 for Disclosing, 0 for Non-Disclosing.
    # 'origin_label' is string 'Disclosing'/'Non-Disclosing'.
    has_manual = 'manual_label' in records[0]
    ground_truth_key = 'manual_label' if has_manual else 'origin_label'
    
    # Heuristic score key. Based on T015, this is likely 'heuristic_score' or similar.
    # We look for the column that contains the continuous score.
    heuristic_key = None
    for key in records[0].keys():
        if 'heuristic' in key.lower() and 'score' in key.lower():
            heuristic_key = key
            break
    
    if not heuristic_key:
        # Fallback: try to find any float column that isn't an ID or count
        for key in records[0].keys():
            val = records[0][key]
            if isinstance(val, float) and key.lower() not in ['pr_number', 'lines_changed', 'review_time']:
                heuristic_key = key
                break
    
    if not heuristic_key:
        raise ValueError("Could not identify a heuristic score column in the dataset.")

    logger.info(f"Using heuristic column: {heuristic_key}, Ground truth: {ground_truth_key}")

    for threshold in thresholds:
        tp, fp, tn, fn = 0, 0, 0, 0
        
        for record in records:
            score = float(record[heuristic_key])
            
            # Determine predicted label based on threshold
            predicted_is_disclosing = score >= threshold
            
            # Determine actual label
            if has_manual:
                actual_is_disclosing = int(record[ground_truth_key]) == 1
            else:
                actual_str = str(record[ground_truth_key])
                actual_is_disclosing = (actual_str == 'Disclosing')
            
            if predicted_is_disclosing and actual_is_disclosing:
                tp += 1
            elif predicted_is_disclosing and not actual_is_disclosing:
                fp += 1
            elif not predicted_is_disclosing and actual_is_disclosing:
                fn += 1
            else:
                tn += 1
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        total = tp + fp + tn + fn
        error_rate = (fp + fn) / total if total > 0 else 0.0
        
        metrics_list.append({
            'threshold': threshold,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'error_rate': error_rate
        })
        
        logger.debug(f"Threshold {threshold}: TP={tp}, FP={fp}, TN={tn}, FN={fn}, Error={error_rate:.4f}")

    return metrics_list

def append_sensitivity_to_log(
    metrics_list: List[Dict[str, Any]], 
    log_path: str
) -> None:
    """
    Append sensitivity analysis results to the validation log CSV.
    Creates the file if it doesn't exist, otherwise appends.
    """
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'threshold', 'true_positives', 'false_positives', 'true_negatives', 
        'false_negatives', 'precision', 'recall', 'f1_score', 'error_rate'
    ]
    
    file_exists = path.exists() and path.stat().st_size > 0
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            # Add a marker row to indicate this is sensitivity analysis
            writer.writerow({'threshold': '---', 'error_rate': '---'}) 
            writer.writerow({'threshold': 'Sensitivity Analysis Sweep', 'error_rate': '---'})
            writer.writeheader() # Write header again after marker? No, standard CSV.
            # Let's just write data. If file exists, we assume header is there.
            # To be safe, we write header only if file is empty.
        
        # Re-open to handle header logic cleanly if we want to be strictly CSV compliant
        # But 'a' mode with DictWriter requires header check.
        # Let's do a simpler append logic.
        pass

    # Rewrite for strict header handling
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        for m in metrics_list:
            writer.writerow(m)
    
    logger.info(f"Sensitivity metrics appended to {log_path}")

def main():
    """
    Main entry point for T017: Sensitivity Analysis Sweep.
    
    1. Load sampled PRs (which should have heuristic scores from T015).
    2. Define a range of thresholds (e.g., 0.0 to 1.0 in steps of 0.1).
    3. Calculate metrics for each threshold.
    4. Append results to data/validation_log.csv.
    """
    logger.info("Starting Sensitivity Analysis (T017)...")
    
    input_file = "data/processed/sampled_prs.csv"
    output_log = "data/validation_log.csv"
    
    # Define thresholds
    thresholds = [i * 0.1 for i in range(11)] # 0.0, 0.1, ..., 1.0
    
    try:
        # Load data
        records = load_heuristic_scores_from_file(input_file)
        
        # Calculate metrics
        metrics = calculate_sensitivity_metrics(records, thresholds)
        
        # Append to log
        append_sensitivity_to_log(metrics, output_log)
        
        logger.info("Sensitivity analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        logger.error("Ensure T015 (classify.py) has run and populated data/processed/sampled_prs.csv with heuristic scores.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
