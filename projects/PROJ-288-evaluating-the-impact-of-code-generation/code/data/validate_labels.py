import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from scipy.stats import pearsonr
from statsmodels.stats.inter_rater import cohens_kappa

from data.logging_config import get_logger

logger = get_logger(__name__)

def load_manual_labels(file_path: str) -> Dict[int, str]:
    """
    Load manual labels from a CSV file.
    Expected format: pr_number, manual_label
    
    Args:
        file_path: Path to the manual labels CSV file
        
    Returns:
        Dictionary mapping pr_number (int) to manual_label (str)
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file format is incorrect
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Manual labels file not found: {file_path}")
    
    manual_labels = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate headers
        if 'pr_number' not in reader.fieldnames or 'manual_label' not in reader.fieldnames:
            raise ValueError(f"Invalid CSV format. Expected 'pr_number' and 'manual_label' columns. Found: {reader.fieldnames}")
        
        for row in reader:
            try:
                pr_num = int(row['pr_number'])
                label = row['manual_label'].strip()
                if label not in ['Disclosing', 'Non-Disclosing']:
                    logger.warning(f"Invalid label '{label}' for PR {pr_num}. Skipping.")
                    continue
                manual_labels[pr_num] = label
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row in manual labels: {row}. Error: {e}")
                continue
    
    logger.info(f"Loaded {len(manual_labels)} manual labels from {file_path}")
    return manual_labels

def calculate_cohen_kappa(automated_labels: List[str], manual_labels: List[str]) -> float:
    """
    Calculate Cohen's Kappa between automated and manual labels.
    
    Args:
        automated_labels: List of labels from the automated classifier (origin_label)
        manual_labels: List of labels from human annotators
        
    Returns:
        Cohen's Kappa score
        
    Raises:
        ValueError: If labels lists are empty or have different lengths
    """
    if len(automated_labels) != len(manual_labels):
        raise ValueError(f"Label lists must have same length. Got {len(automated_labels)} and {len(manual_labels)}")
    
    if len(automated_labels) == 0:
        raise ValueError("Cannot calculate Kappa with empty label lists")
    
    # statsmodels cohens_kappa expects a contingency matrix or two 1D arrays
    # We pass two 1D arrays of labels
    try:
        kappa_result = cohens_kappa(automated_labels, manual_labels)
        return float(kappa_result['kappa'])
    except Exception as e:
        logger.error(f"Error calculating Cohen's Kappa: {e}")
        raise

def validate_disclosure_signal(
    sampled_prs_path: str,
    manual_labels_path: str,
    output_log_path: str
) -> Tuple[bool, float]:
    """
    Validate the disclosure signal by comparing automated labels with manual labels.
    
    Args:
        sampled_prs_path: Path to the sampled_prs.csv file containing origin_label
        manual_labels_path: Path to the manual_labels.csv file
        output_log_path: Path to write the validation log
        
    Returns:
        Tuple of (is_valid, kappa_score)
        is_valid is True if kappa >= 0.6, False otherwise
        
    Raises:
        FileNotFoundError: If input files don't exist
        ValueError: If data is inconsistent
    """
    logger.info(f"Starting validation of disclosure signal...")
    logger.info(f"  Sampled PRs: {sampled_prs_path}")
    logger.info(f"  Manual Labels: {manual_labels_path}")
    
    # Load manual labels
    manual_labels_dict = load_manual_labels(manual_labels_path)
    
    # Load sampled PRs and extract matching labels
    automated_labels = []
    manual_labels_list = []
    pr_numbers_matched = []
    
    with open(sampled_prs_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            pr_num = int(row['pr_number'])
            if pr_num in manual_labels_dict:
                automated_label = row.get('origin_label', '').strip()
                if automated_label not in ['Disclosing', 'Non-Disclosing']:
                    logger.warning(f"Invalid automated label '{automated_label}' for PR {pr_num}. Skipping.")
                    continue
                
                automated_labels.append(automated_label)
                manual_labels_list.append(manual_labels_dict[pr_num])
                pr_numbers_matched.append(pr_num)
    
    logger.info(f"Found {len(automated_labels)} PRs with both automated and manual labels.")
    
    if len(automated_labels) == 0:
        raise ValueError("No matching PRs found between sampled_prs.csv and manual_labels.csv")
    
    # Calculate Cohen's Kappa
    kappa_score = calculate_cohen_kappa(automated_labels, manual_labels_list)
    logger.info(f"Calculated Cohen's Kappa: {kappa_score:.4f}")
    
    # Determine validity
    is_valid = kappa_score >= 0.6
    status = "PASS" if is_valid else "FAIL"
    logger.info(f"Validation Status: {status} (Threshold: 0.6, Score: {kappa_score:.4f})")
    
    if not is_valid:
        logger.error(f"Kappa ({kappa_score:.4f}) is below threshold (0.6). Halting execution as per constraint.")
    
    # Write validation log
    write_validation_log(
        output_log_path,
        kappa_score,
        len(automated_labels),
        status,
        is_valid
    )
    
    return is_valid, kappa_score

def write_validation_log(
    output_path: str,
    kappa_score: float,
    sample_size: int,
    status: str,
    is_valid: bool
) -> None:
    """
    Write validation results to a CSV log file.
    
    Args:
        output_path: Path to the output log file
        kappa_score: Calculated Cohen's Kappa
        sample_size: Number of PRs compared
        status: "PASS" or "FAIL"
        is_valid: Boolean validity flag
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = path.exists()
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'metric', 'value', 'sample_size', 'status', 'valid'])
        
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        writer.writerow([
            timestamp,
            'cohens_kappa',
            f'{kappa_score:.4f}',
            sample_size,
            status,
            is_valid
        ])
    
    logger.info(f"Validation log written to {output_path}")

def main():
    """
    Main entry point for the validation script.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    sampled_prs_path = project_root / 'data' / 'processed' / 'sampled_prs.csv'
    manual_labels_path = project_root / 'data' / 'manual_labels.csv'
    validation_log_path = project_root / 'data' / 'validation_log.csv'
    
    # Check if files exist
    if not sampled_prs_path.exists():
        logger.error(f"Sampled PRs file not found: {sampled_prs_path}")
        sys.exit(1)
    
    if not manual_labels_path.exists():
        logger.error(f"Manual labels file not found: {manual_labels_path}")
        logger.error("Cannot proceed without manual labels for validation.")
        sys.exit(1)
    
    try:
        is_valid, kappa_score = validate_disclosure_signal(
            str(sampled_prs_path),
            str(manual_labels_path),
            str(validation_log_path)
        )
        
        if not is_valid:
            logger.error("Validation failed. Dataset flagged in validation_log.csv.")
            sys.exit(1)
        
        logger.info("Validation completed successfully.")
        
    except Exception as e:
        logger.error(f"Validation process failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
