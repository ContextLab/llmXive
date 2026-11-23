"""
Validator module for User Story 4: Manual Validation of VADER Thresholds.

This module handles loading the validation dataset, running VADER sentiment
analysis against manually labeled comments, computing Cohen's Kappa, and
validating the thresholds.

Dependencies:
- src/bias_pipeline/extractor (for analyze_sentiment)
- src/bias_pipeline/error_handler (for safe execution)
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from sklearn.metrics import cohen_kappa_score

# Import from sibling modules
from .extractor import analyze_sentiment
from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .utils import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Path constants
VALIDATION_DATA_PATH = Path("data/validation/labels.csv")
KAPPA_THRESHOLD = 0.6

def load_validation_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the validation dataset of manually labeled comments.
    
    Args:
        path: Path to the CSV file. Defaults to data/validation/labels.csv.
    
    Returns:
        pd.DataFrame: DataFrame with columns: 'comment', 'label'
        where label is 0 (negative/neutral) or 1 (positive/biased).
    
    Raises:
        FileNotFoundError: If the validation dataset does not exist.
        ValueError: If the dataset format is incorrect.
    """
    target_path = path or VALIDATION_DATA_PATH
    
    if not target_path.exists():
        raise FileNotFoundError(
            f"Validation dataset not found at {target_path}. "
            "Please ensure T041 has acquired the dataset."
        )
    
    try:
        df = pd.read_csv(target_path)
        
        # Validate required columns
        required_cols = {'comment', 'label'}
        if not required_cols.issubset(df.columns):
            raise ValueError(
                f"Validation dataset missing required columns: {required_cols - set(df.columns)}"
            )
        
        # Validate label values
        if not df['label'].isin([0, 1]).all():
            raise ValueError("Validation dataset 'label' column must contain only 0 or 1.")
        
        logger.info(f"Loaded validation dataset with {len(df)} samples from {target_path}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load validation dataset: {e}")
        raise

def run_vader_validation(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """
    Run VADER sentiment analysis on the validation dataset and compute Cohen's Kappa.
    
    Args:
        df: DataFrame with 'comment' and 'label' columns.
    
    Returns:
        Tuple of (kappa_score, results_dict) where results_dict contains
        detailed metrics and per-sample predictions.
    """
    if df.empty:
        raise ValueError("Cannot run validation on empty dataset.")
    
    logger.info(f"Running VADER validation on {len(df)} samples...")
    
    predictions = []
    labels = df['label'].tolist()
    
    for idx, row in df.iterrows():
        comment = row['comment']
        true_label = row['label']
        
        # Run VADER analysis
        sentiment_scores = analyze_sentiment(comment)
        
        # VADER compound score threshold: >= 0.05 is positive (1), else negative/neutral (0)
        # This aligns with standard VADER interpretation for binary classification
        compound = sentiment_scores.get('compound', 0.0)
        predicted_label = 1 if compound >= 0.05 else 0
        
        predictions.append(predicted_label)
    
    # Compute Cohen's Kappa
    kappa = cohen_kappa_score(labels, predictions)
    
    logger.info(f"Cohen's Kappa score: {kappa:.4f}")
    
    results = {
        'kappa_score': kappa,
        'n_samples': len(df),
        'threshold_used': 0.05,
        'predictions': predictions,
        'true_labels': labels
    }
    
    return kappa, results

def validate_threshold(kappa_score: float, threshold: float = KAPPA_THRESHOLD) -> bool:
    """
    Validate that the Cohen's Kappa score meets the minimum threshold.
    
    Args:
        kappa_score: The computed Cohen's Kappa score.
        threshold: Minimum acceptable Kappa score (default: 0.6).
    
    Returns:
        bool: True if kappa_score >= threshold, False otherwise.
    
    Raises:
        ExecutionError: If the threshold is not met (pipeline should halt).
    """
    if kappa_score < threshold:
        error_msg = (
            f"Validation FAILED: Cohen's Kappa ({kappa_score:.4f}) is below "
            f"the required threshold ({threshold}). The VADER sentiment "
            f"thresholds are not reliable for this dataset. Pipeline halted."
        )
        logger.error(error_msg)
        raise ExecutionError(error_msg)
    
    logger.info(f"Validation PASSED: Cohen's Kappa ({kappa_score:.4f}) >= {threshold}")
    return True

@handle_pipeline_error
def run_validation_pipeline(
    data_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full validation pipeline: load data, run VADER, compute Kappa, validate threshold.
    
    Args:
        data_path: Path to validation dataset. Defaults to data/validation/labels.csv.
        output_path: Path to write results JSON. Defaults to data/processed/validation_results.json.
    
    Returns:
        Dict with validation results.
    
    Raises:
        ExecutionError: If validation fails (Kappa < threshold).
        FileNotFoundError: If validation dataset is missing.
    """
    output_path = output_path or Path("data/processed/validation_results.json")
    
    # Step 1: Load dataset
    df = load_validation_dataset(data_path)
    
    # Step 2: Run VADER validation
    kappa_score, results = run_vader_validation(df)
    
    # Step 3: Validate threshold
    validate_threshold(kappa_score)
    
    # Step 4: Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results['status'] = 'PASSED'
    results['kappa_threshold'] = KAPPA_THRESHOLD
    
    with open(output_path, 'w') as f:
        import json
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation results written to {output_path}")
    return results
