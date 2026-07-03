import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from scipy.stats import pearsonr
import numpy as np

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.classify import load_sampled_prs
from data.logging_config import get_logger
from data.config import STRATIFICATION_SEED

logger = get_logger(__name__)

def load_manual_labels(file_path: str) -> Dict[int, str]:
    """
    Load manual labels from CSV.
    Expected format: pr_number, manual_label
    Returns a dictionary mapping pr_number (int) to manual_label (str).
    """
    if not os.path.exists(file_path):
        logger.error(f"Manual labels file not found: {file_path}")
        return {}

    manual_labels = {}
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pr_number = int(row['pr_number'])
                label = row['manual_label'].strip()
                if label not in ['Disclosing', 'Non-Disclosing']:
                    logger.warning(f"Invalid manual label '{label}' for PR {pr_number}. Skipping.")
                    continue
                manual_labels[pr_number] = label
    except Exception as e:
        logger.error(f"Error reading manual labels file: {e}")
        return {}

    return manual_labels

def calculate_cohen_kappa(
    predicted_labels: List[str],
    actual_labels: List[str]
) -> float:
    """
    Calculate Cohen's Kappa coefficient.
    Formula: Kappa = (Po - Pe) / (1 - Pe)
    Po = observed agreement, Pe = expected agreement by chance.
    """
    if len(predicted_labels) != len(actual_labels):
        raise ValueError("Label lists must be of equal length.")
    
    if len(predicted_labels) == 0:
        logger.warning("No overlapping samples to calculate Kappa.")
        return 0.0

    n = len(predicted_labels)
    
    # Calculate observed agreement (Po)
    agreements = sum(1 for p, a in zip(predicted_labels, actual_labels) if p == a)
    po = agreements / n

    # Calculate expected agreement (Pe)
    # Count occurrences of each class in both lists
    classes = set(predicted_labels) | set(actual_labels)
    
    pe = 0.0
    for cls in classes:
        p_cls = predicted_labels.count(cls) / n
        a_cls = actual_labels.count(cls) / n
        pe += p_cls * a_cls

    if abs(1 - pe) < 1e-9:
        logger.warning("Pe is 1.0, Kappa undefined. Returning 0.0.")
        return 0.0

    kappa = (po - pe) / (1 - pe)
    return kappa

def validate_disclosure_signal(
    data_path: str,
    manual_labels_path: str,
    output_path: str
) -> bool:
    """
    Main validation logic.
    1. Load sampled PRs (with origin_label).
    2. Load manual labels.
    3. Match by pr_number.
    4. Calculate Cohen's Kappa.
    5. If Kappa < 0.6, flag dataset.
    6. Write results to validation_log.csv.
    
    Returns True if validation passed (Kappa >= 0.6), False otherwise.
    """
    logger.info(f"Loading sampled PRs from {data_path}")
    prs = load_sampled_prs(data_path)
    
    logger.info(f"Loading manual labels from {manual_labels_path}")
    manual_labels = load_manual_labels(manual_labels_path)
    
    if not manual_labels:
        logger.error("No valid manual labels found. Cannot validate.")
        # Still write a log entry indicating failure due to missing data
        write_validation_log(output_path, 0.0, False, "No manual labels found")
        return False

    # Filter PRs that have manual labels
    matched_prs = []
    for pr in prs:
        if pr['pr_number'] in manual_labels:
            matched_prs.append(pr)

    if not matched_prs:
        logger.error("No overlapping PRs found between sampled data and manual labels.")
        write_validation_log(output_path, 0.0, False, "No overlapping PRs found")
        return False

    predicted_labels = [pr['origin_label'] for pr in matched_prs]
    actual_labels = [manual_labels[pr['pr_number']] for pr in matched_prs]

    logger.info(f"Calculated Cohen's Kappa for {len(matched_prs)} overlapping PRs.")
    kappa = calculate_cohen_kappa(predicted_labels, actual_labels)
    
    logger.info(f"Cohen's Kappa: {kappa:.4f}")
    
    passed = kappa >= 0.6
    status = "PASS" if passed else "FAIL"
    reason = f"Kappa >= 0.6 ({kappa:.4f})" if passed else f"Kappa < 0.6 ({kappa:.4f})"
    
    write_validation_log(output_path, kappa, passed, reason)
    
    if not passed:
        logger.warning(f"Validation FAILED: Kappa ({kappa:.4f}) is below threshold 0.6. Dataset flagged in {output_path}.")
        return False
    
    logger.info("Validation PASSED.")
    return True

def write_validation_log(
    output_path: str,
    kappa: float,
    passed: bool,
    reason: str
):
    """
    Append validation results to the log file.
    Creates the file if it doesn't exist.
    """
    file_exists = os.path.exists(output_path)
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['metric', 'value', 'status', 'details'])
        
        writer.writerow([
            'cohen_kappa',
            f"{kappa:.4f}",
            'PASS' if passed else 'FAIL',
            reason
        ])

def main():
    """
    Entry point for the validation script.
    """
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data"
    
    sampled_prs_path = data_dir / "processed" / "sampled_prs.csv"
    manual_labels_path = data_dir / "manual_labels.csv"
    validation_log_path = data_dir / "validation_log.csv"
    
    if not sampled_prs_path.exists():
        logger.error(f"Sampled PRs file not found at {sampled_prs_path}. "
                     "Please ensure T014 (sampling) has been completed.")
        sys.exit(1)
    
    if not manual_labels_path.exists():
        logger.error(f"Manual labels file not found at {manual_labels_path}. "
                     "Please provide a manual_labels.csv with columns: pr_number, manual_label")
        # We exit with error rather than writing a fail log if the input file is missing,
        # as the task implies the file should exist to perform the check.
        sys.exit(1)
    
    success = validate_disclosure_signal(
        data_path=str(sampled_prs_path),
        manual_labels_path=str(manual_labels_path),
        output_path=str(validation_log_path)
    )
    
    if not success:
        logger.warning("Validation failed. Check data/validation_log.csv for details.")
        # Exit with non-zero code to indicate failure in pipeline
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
