import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from data.classify import load_sampled_prs, calculate_heuristic_scores, check_disclosure_keywords
from data.logging_config import get_logger
from data.validate_labels import load_manual_labels, calculate_cohen_kappa

logger = get_logger(__name__)

def load_heuristic_scores_from_file(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load the sampled PRs which should already contain heuristic scores 
    (calculated in T015) and manual labels (if available for validation).
    Returns a list of dicts with keys: pr_number, heuristic_score, manual_label (optional).
    """
    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = {
                'pr_number': int(row['pr_number']),
                'heuristic_score': float(row.get('heuristic_score', 0.0)),
                'origin_label': row.get('origin_label', 'Non-Disclosing'),
                'manual_label': None
            }
            # Try to extract manual label if present in the row or later joined
            if 'manual_label' in row:
                record['manual_label'] = row['manual_label']
            data.append(record)
    return data

def calculate_sensitivity_metrics(
    data: List[Dict[str, Any]], 
    thresholds: List[float],
    manual_labels: Dict[int, str]
) -> List[Dict[str, Any]]:
    """
    Sweep across thresholds to calculate error rates (FP, FN, Accuracy) 
    against manual labels.
    
    Context: The primary label 'origin_label' is keyword-based.
    This analysis tests the sensitivity of the *heuristic* scores 
    (validation/covariate) against manual ground truth.
    
    Returns a list of metrics dicts.
    """
    results = []
    
    for thresh in thresholds:
        tp, tn, fp, fn = 0, 0, 0, 0
        
        for record in data:
            pr_num = record['pr_number']
            heuristic_score = record['heuristic_score']
            
            # Predicted label based on heuristic threshold
            predicted_label = 'Disclosing' if heuristic_score >= thresh else 'Non-Disclosing'
            
            # Ground truth from manual labels
            if pr_num not in manual_labels:
                continue  # Skip if no manual label available for this PR
            
            true_label = manual_labels[pr_num]
            
            if true_label == 'Disclosing':
                if predicted_label == 'Disclosing':
                    tp += 1
                else:
                    fn += 1
            else: # true_label == 'Non-Disclosing'
                if predicted_label == 'Non-Disclosing':
                    tn += 1
                else:
                    fp += 1
        
        total = tp + tn + fp + fn
        if total == 0:
            accuracy = 0.0
            fpr = 0.0
            fnr = 0.0
        else:
            accuracy = (tp + tn) / total
            # False Positive Rate: FP / (FP + TN)
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            # False Negative Rate: FN / (FN + TP)
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            'threshold': thresh,
            'accuracy': accuracy,
            'false_positive_rate': fpr,
            'false_negative_rate': fnr,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        })
        
    return results

def append_sensitivity_to_log(results: List[Dict[str, Any]], log_path: str):
    """
    Append the sensitivity analysis results to the existing validation_log.csv.
    If the file doesn't exist or is empty, create it with headers.
    """
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=['threshold', 'accuracy', 'false_positive_rate', 'false_negative_rate', 'tp', 'tn', 'fp', 'fn', 'analysis_type']
        )
        
        if not file_exists:
            writer.writeheader()
        
        for row in results:
            row['analysis_type'] = 'sensitivity_sweep'
            writer.writerow(row)

def main():
    logger.info("Starting Sensitivity Analysis (T017)")
    
    # Paths
    project_root = Path(__file__).resolve().parents[2]
    sampled_csv_path = project_root / "data" / "processed" / "sampled_prs.csv"
    manual_labels_path = project_root / "data" / "manual_labels.csv"
    log_path = project_root / "data" / "validation_log.csv"
    
    if not sampled_csv_path.exists():
        logger.error(f"Required input file not found: {sampled_csv_path}")
        logger.error("Run T015 (classify.py) and T016 (validate_labels.py) first.")
        sys.exit(1)
    
    if not manual_labels_path.exists():
        logger.error(f"Manual labels file not found: {manual_labels_path}")
        logger.error("Cannot perform sensitivity analysis without ground truth.")
        sys.exit(1)
    
    # Load Data
    logger.info(f"Loading sampled PRs from {sampled_csv_path}")
    data = load_heuristic_scores_from_file(str(sampled_csv_path))
    
    logger.info(f"Loading manual labels from {manual_labels_path}")
    manual_labels = load_manual_labels(str(manual_labels_path))
    
    if not manual_labels:
        logger.warning("No manual labels found. Sensitivity analysis cannot be computed.")
        sys.exit(1)
    
    # Define Threshold Sweep
    # Sweep from 0.0 to 1.0 in steps of 0.1
    thresholds = [i * 0.1 for i in range(0, 11)]
    
    logger.info(f"Running sensitivity sweep across {len(thresholds)} thresholds...")
    results = calculate_sensitivity_metrics(data, thresholds, manual_labels)
    
    # Append to log
    logger.info(f"Appending results to {log_path}")
    append_sensitivity_to_log(results, str(log_path))
    
    logger.info("Sensitivity Analysis completed successfully.")
    logger.info(f"Results appended to {log_path}")

if __name__ == "__main__":
    main()
