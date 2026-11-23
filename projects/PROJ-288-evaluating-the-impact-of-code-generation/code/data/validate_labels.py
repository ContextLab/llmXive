import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from scipy.stats import cohen_kappa_score
from data.logging_config import get_logger
from data.classify import load_sampled_prs

logger = get_logger(__name__)

def load_manual_labels(file_path: str) -> Dict[int, str]:
    """
    Load manual labels from a CSV file.
    Expected format: pr_number, manual_label
    Returns a dictionary mapping pr_number (int) to manual_label (str).
    """
    labels = {}
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Manual labels file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pr_num = int(row['pr_number'])
                label = row['manual_label'].strip()
                if label not in ('Disclosing', 'Non-Disclosing'):
                    logger.warning(f"Invalid label '{label}' for PR {pr_num}, skipping.")
                    continue
                labels[pr_num] = label
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row in manual labels: {row} - {e}")
    return labels

def calculate_cohen_kappa(automated_labels: List[str], manual_labels: List[str]) -> float:
    """
    Calculate Cohen's Kappa score between automated and manual labels.
    """
    if len(automated_labels) != len(manual_labels):
        raise ValueError("Label lists must be of equal length")
    if len(automated_labels) == 0:
        raise ValueError("No overlapping labels found to calculate Kappa")
    
    try:
        kappa = cohen_kappa_score(automated_labels, manual_labels)
        return float(kappa)
    except Exception as e:
        logger.error(f"Error calculating Cohen's Kappa: {e}")
        raise

def validate_disclosure_signal(
    sampled_prs_path: str,
    manual_labels_path: str,
    output_log_path: str,
    threshold: float = 0.6
) -> Tuple[bool, Dict]:
    """
    Validate the disclosure signal by comparing automated classification
    against manual labels using Cohen's Kappa.
    
    Returns:
        Tuple[bool, Dict]: (is_valid, metrics_dict)
        is_valid is False if Kappa < threshold.
    """
    logger.info(f"Loading manual labels from {manual_labels_path}")
    manual_labels_map = load_manual_labels(manual_labels_path)
    
    logger.info(f"Loading sampled PRs from {sampled_prs_path}")
    # Assuming load_sampled_prs returns a list of dicts with 'pr_number' and 'origin_label'
    try:
        prs = load_sampled_prs(sampled_prs_path)
    except Exception as e:
        logger.error(f"Failed to load sampled PRs: {e}")
        raise

    # Filter PRs that exist in manual labels
    matching_prs = []
    for pr in prs:
        pr_num = pr.get('pr_number')
        if pr_num in manual_labels_map:
            matching_prs.append({
                'pr_number': pr_num,
                'origin_label': pr.get('origin_label'),
                'manual_label': manual_labels_map[pr_num]
            })

    if not matching_prs:
        raise ValueError("No overlapping PRs found between sampled data and manual labels.")

    automated = [p['origin_label'] for p in matching_prs]
    manual = [p['manual_label'] for p in matching_prs]

    kappa = calculate_cohen_kappa(automated, manual)
    logger.info(f"Calculated Cohen's Kappa: {kappa:.4f} (Threshold: {threshold})")

    is_valid = kappa >= threshold
    metrics = {
        'kappa': kappa,
        'threshold': threshold,
        'sample_size': len(matching_prs),
        'is_valid': is_valid,
        'status': 'PASS' if is_valid else 'FAIL'
    }

    # Write results to log
    write_validation_log(output_log_path, metrics)

    return is_valid, metrics

def write_validation_log(log_path: str, metrics: Dict) -> None:
    """
    Append validation metrics to the validation log CSV.
    """
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists() and path.stat().st_size > 0
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['kappa', 'threshold', 'sample_size', 'is_valid', 'status'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'kappa': metrics['kappa'],
            'threshold': metrics['threshold'],
            'sample_size': metrics['sample_size'],
            'is_valid': metrics['is_valid'],
            'status': metrics['status']
        })
    logger.info(f"Validation log written to {log_path}")

def main():
    """
    Main entry point for T016: Manual validation subset logic.
    """
    # Paths
    project_root = Path(__file__).parent.parent.parent
    sampled_prs_path = project_root / "data" / "processed" / "sampled_prs.csv"
    manual_labels_path = project_root / "data" / "manual_labels.csv"
    output_log_path = project_root / "data" / "validation_log.csv"

    logger.info("Starting T016: Manual validation subset logic")
    
    try:
        is_valid, metrics = validate_disclosure_signal(
            str(sampled_prs_path),
            str(manual_labels_path),
            str(output_log_path),
            threshold=0.6
        )

        if not is_valid:
            logger.error(f"Kappa ({metrics['kappa']:.4f}) is below threshold (0.6). Halting execution.")
            # The task requirement says "halt execution". We exit with error code.
            sys.exit(1)
        
        logger.info(f"Validation passed. Kappa: {metrics['kappa']:.4f}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        # If manual_labels.csv is missing, we cannot proceed.
        # We write a failure entry to the log or exit.
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
