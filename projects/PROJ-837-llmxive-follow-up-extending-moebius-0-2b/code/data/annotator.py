import os
import json
import csv
import math
import argparse
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode, get_path
from utils.logger import get_logger, get_timestamp
from data.loader import fetch_places365_subset

# Importing logging setup to ensure consistent logging
logger = get_logger("annotator")

def validate_sample_size(sample_count: int, min_threshold: int = 50) -> bool:
    """
    Validates that the sample size meets the minimum threshold.
    
    Args:
        sample_count (int): The number of samples to validate.
        min_threshold (int): The minimum required sample size (default 50).
    
    Returns:
        bool: True if sample_size >= min_threshold, False otherwise.
    """
    if sample_count < min_threshold:
        logger.error(f"Sample size {sample_count} is below minimum threshold {min_threshold}.")
        return False
    return True

def validate_label_independence(
    scores_path: Path,
    mask_metrics_path: Path,
    threshold: float = 0.0
) -> bool:
    """
    Validates that labels (scores) are independent of mask metrics.
    
    This check ensures that the generated scores do not correlate with the
    synthetic mask metrics (gradient_variance, texture_entropy) beyond a
    negligible threshold, preventing circularity in the labeling process.
    
    Args:
        scores_path (Path): Path to the scores CSV (decoupled_scores.csv or human_scores.csv).
        mask_metrics_path (Path): Path to the mask_metrics.json file.
        threshold (float): Maximum allowed correlation coefficient. Default 0.0.
    
    Returns:
        bool: True if independence holds (correlation <= threshold), False otherwise.
    
    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If the independence check fails.
    """
    if not scores_path.exists():
        logger.error(f"Scores file not found: {scores_path}")
        raise FileNotFoundError(f"Scores file not found: {scores_path}")
    
    if not mask_metrics_path.exists():
        logger.error(f"Mask metrics file not found: {mask_metrics_path}")
        raise FileNotFoundError(f"Mask metrics file not found: {mask_metrics_path}")

    # Load scores
    scores_data = []
    with open(scores_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores_data.append(row)

    if not scores_data:
        logger.error("Scores data is empty.")
        return False

    # Load mask metrics
    with open(mask_metrics_path, 'r', encoding='utf-8') as f:
        mask_metrics = json.load(f)

    # Extract metrics for correlation check
    # Assuming mask_metrics is a dict keyed by image_id
    image_ids = [row['image_id'] for row in scores_data]
    
    # Ensure we have metrics for the images in scores
    valid_metrics = {}
    for iid in image_ids:
        if iid in mask_metrics:
            valid_metrics[iid] = mask_metrics[iid]
        else:
            logger.warning(f"No mask metrics found for image_id: {iid}")
    
    if not valid_metrics:
        logger.error("No valid mask metrics found for the provided scores.")
        return False

    # Calculate correlation between scores and metrics
    # We will check correlation for 'gradient_variance' and 'texture_entropy'
    metrics_to_check = ['gradient_variance', 'texture_entropy']
    max_correlation = 0.0

    for metric in metrics_to_check:
        metric_values = [valid_metrics[iid].get(metric, 0.0) for iid in valid_metrics]
        score_values = [float(row['score']) for row in scores_data if row['image_id'] in valid_metrics]

        if len(metric_values) != len(score_values) or len(metric_values) < 2:
            logger.warning(f"Not enough data points for {metric} correlation check.")
            continue

        try:
            # Using numpy for correlation calculation
            corr_matrix = np.corrcoef(metric_values, score_values)
            corr = corr_matrix[0, 1]
            if abs(corr) > max_correlation:
                max_correlation = abs(corr)
            logger.info(f"Correlation between {metric} and score: {corr:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate correlation for {metric}: {e}")
            continue

    if max_correlation > threshold:
        logger.error(f"Label independence check failed. Max correlation {max_correlation:.4f} > threshold {threshold}.")
        return False

    logger.info(f"Label independence check passed. Max correlation: {max_correlation:.4f} <= {threshold}.")
    return True

def log_validation_result(
    result: bool,
    check_name: str,
    details: str = "",
    log_path: Optional[Path] = None
) -> None:
    """
    Logs the result of a validation check to the validation log file.
    
    Args:
        result (bool): The result of the validation (True/False).
        check_name (str): The name of the check being validated.
        details (str): Additional details about the check.
        log_path (Optional[Path]): Path to the validation log file. Defaults to data/results/validation_log.txt.
    """
    if log_path is None:
        log_path = Path(get_path("results")) / "validation_log.txt"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = get_timestamp()
    status = "PASSED" if result else "FAILED"
    
    log_entry = f"[{timestamp}] [{check_name}] {status} - {details}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    if result:
        logger.info(f"Validation passed: {check_name}")
    else:
        logger.error(f"Validation failed: {check_name} - {details}")

def generate_ci_scores(
    image_ids: List[str],
    seed: int,
    output_path: Path
) -> None:
    """
    Generates decoupled random scores for CI Mode.
    
    This function generates scores strictly decoupled from synthetic mask metrics
    to avoid circularity, as required for CI Mode simulation.
    
    Args:
        image_ids (List[str]): List of image IDs to generate scores for.
        seed (int): Random seed for reproducibility.
        output_path (Path): Path to save the output CSV.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['image_id', 'score', 'mode', 'seed_used'])
        
        for img_id in image_ids:
            # Generate score uniformly between 1 and 5
            score = np.random.uniform(1, 5)
            writer.writerow([img_id, f"{score:.4f}", 'CI_MODE_SIMULATION', seed])
    
    logger.info(f"Generated CI scores for {len(image_ids)} images to {output_path}")

def save_scores(scores_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves scores to a CSV file.
    
    Args:
        scores_data (List[Dict[str, Any]]): List of score dictionaries.
        output_path (Path): Path to save the CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not scores_data:
        logger.warning("No scores data to save.")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=scores_data[0].keys())
        writer.writeheader()
        writer.writerows(scores_data)
    
    logger.info(f"Saved scores to {output_path}")

def load_research_annotations(input_path: Path) -> List[Dict[str, Any]]:
    """
    Loads human-annotated scores for Research Mode.
    
    Args:
        input_path (Path): Path to the human_scores.csv file.
    
    Returns:
        List[Dict[str, Any]]: List of score dictionaries.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the schema is invalid.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Human annotation file not found: {input_path}")
    
    scores_data = []
    required_keys = {'image_id', 'score', 'rater_id'}
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Check schema
        if not required_keys.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Invalid schema in {input_path}. Required keys: {required_keys}")
        
        for row in reader:
            scores_data.append(row)
    
    logger.info(f"Loaded {len(scores_data)} human annotations from {input_path}")
    return scores_data

def run_ci_mode(
    seed: int,
    sample_size: int,
    output_scores_path: Path,
    log_path: Path,
    mask_metrics_path: Path
) -> bool:
    """
    Executes the CI Mode workflow: generate decoupled scores and validate.
    
    Args:
        seed (int): Random seed.
        sample_size (int): Number of samples to process.
        output_scores_path (Path): Path to save decoupled scores.
        log_path (Path): Path to validation log.
        mask_metrics_path (Path): Path to mask metrics for independence check.
    
    Returns:
        bool: True if all validations pass, False otherwise.
    """
    logger.info("Starting CI Mode workflow.")
    
    # 1. Validate Sample Size
    if not validate_sample_size(sample_size):
        log_validation_result(False, "Sample Size Check", f"Size {sample_size} < 50", log_path)
        return False
    
    log_validation_result(True, "Sample Size Check", f"Size {sample_size} >= 50", log_path)
    
    # 2. Generate Decoupled Scores
    # We need image_ids. In CI mode, we might generate them or load from a small subset.
    # For this implementation, we assume we have a list of image_ids.
    # If not provided, we generate dummy IDs for the sample_size.
    image_ids = [f"ci_img_{i:04d}" for i in range(sample_size)]
    generate_ci_scores(image_ids, seed, output_scores_path)
    
    # 3. Validate Label Independence
    try:
        if not validate_label_independence(output_scores_path, mask_metrics_path, threshold=0.0):
            log_validation_result(False, "Label Independence Check", "Correlation > 0.0", log_path)
            return False
        log_validation_result(True, "Label Independence Check", "Correlation <= 0.0", log_path)
    except FileNotFoundError as e:
        logger.warning(f"Skipping independence check due to missing file: {e}")
        # In CI mode, if metrics are missing, we might still proceed but log a warning.
        # However, the task requires raising an error if check fails.
        # If the file is missing, we cannot verify independence, so we log it as a failure of the check.
        log_validation_result(False, "Label Independence Check", f"Missing metrics file: {e}", log_path)
        return False
    
    return True

def run_research_mode(
    input_scores_path: Path,
    log_path: Path,
    mask_metrics_path: Path
) -> bool:
    """
    Executes the Research Mode workflow: load human scores and validate.
    
    Args:
        input_scores_path (Path): Path to human_scores.csv.
        log_path (Path): Path to validation log.
        mask_metrics_path (Path): Path to mask metrics for independence check.
    
    Returns:
        bool: True if all validations pass, False otherwise.
    """
    logger.info("Starting Research Mode workflow.")
    
    # 1. Load and Validate Annotations
    try:
        scores_data = load_research_annotations(input_scores_path)
    except FileNotFoundError as e:
        logger.error(f"Research mode disabled: {e}")
        log_validation_result(False, "Human Annotation Load", str(e), log_path)
        return False
    except ValueError as e:
        logger.error(f"Invalid annotation schema: {e}")
        log_validation_result(False, "Human Annotation Schema", str(e), log_path)
        return False
    
    # 2. Validate Sample Size
    sample_size = len(scores_data)
    if not validate_sample_size(sample_size):
        log_validation_result(False, "Sample Size Check", f"Size {sample_size} < 50", log_path)
        return False
    log_validation_result(True, "Sample Size Check", f"Size {sample_size} >= 50", log_path)
    
    # 3. Validate Label Independence (Optional for Research Mode if human data is trusted, 
    # but the task requires the check logic to exist and run if possible)
    # For Research Mode, we check if scores are correlated with mask metrics to ensure 
    # the human raters weren't biased by the synthetic metrics (if they had access).
    # Or, we check that the scores are not trivially correlated (e.g., constant).
    try:
        # Create a temporary scores file for the check function
        temp_scores_path = Path(get_path("annotations")) / "temp_research_scores.csv"
        save_scores(scores_data, temp_scores_path)
        
        if not validate_label_independence(temp_scores_path, mask_metrics_path, threshold=0.5):
            log_validation_result(False, "Label Independence Check", "Correlation > 0.5", log_path)
            # In research mode, high correlation might indicate bias, but we log and return False
            return False
        log_validation_result(True, "Label Independence Check", "Correlation <= 0.5", log_path)
    except FileNotFoundError as e:
        logger.warning(f"Skipping independence check in Research Mode: {e}")
        # If metrics are missing, we cannot check, but we don't fail the whole mode necessarily.
        # However, per task T016, we must raise error if check fails. If we can't check, 
        # we log a warning but might proceed.
        log_validation_result(False, "Label Independence Check", f"Missing metrics file: {e}", log_path)
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Annotator for Human Complexity Annotation")
    parser.add_argument("--participants", action="store_true", help="Run in Research Mode (with participants)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for CI Mode")
    parser.add_argument("--sample-size", type=int, default=500, help="Sample size for CI Mode")
    
    args = parser.parse_args()
    
    mode = get_mode()
    is_ci = is_ci_mode()
    is_research = is_research_mode()
    
    log_path = Path(get_path("results")) / "validation_log.txt"
    scores_path = Path(get_path("annotations"))
    mask_metrics_path = Path(get_path("processed")) / "mask_metrics.json"
    
    if args.participants or is_research:
        # Research Mode
        human_scores_path = scores_path / "human_scores.csv"
        success = run_research_mode(human_scores_path, log_path, mask_metrics_path)
        if not success:
            logger.error("Research Mode validation failed.")
            return 1
    else:
        # CI Mode
        decoupled_scores_path = scores_path / "decoupled_scores.csv"
        success = run_ci_mode(args.seed, args.sample_size, decoupled_scores_path, log_path, mask_metrics_path)
        if not success:
            logger.error("CI Mode validation failed.")
            return 1
    
    logger.info("Annotator validation completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())