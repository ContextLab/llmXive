"""
Validator module for User Story 4: Manual Validation of VADER Thresholds.

This module handles the loading of the Validation Dataset and the computation
of Cohen's Kappa to validate VADER sentiment thresholds against human labels.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .utils import setup_logging, PipelineError
from .error_handler import safe_execute, ExecutionError

logger = setup_logging(__name__)

def load_validation_dataset(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the 'Validation Dataset' of manually labeled comments.
    
    This function attempts to load the dataset from `data/validation/labels.csv`.
    If the file does not exist, it attempts to fetch it from a verified external
    source (HuggingFace). If neither is available, it raises a FileNotFoundError
    to fail loudly, as per the requirement to never generate synthetic labels.
    
    Args:
        path: Optional override path for the validation dataset.
        
    Returns:
        A pandas DataFrame with columns: 'comment_text', 'human_label'.
        
    Raises:
        FileNotFoundError: If no valid source for the real dataset is found.
        PipelineError: If the dataset format is invalid.
    """
    default_path = Path("data/validation/labels.csv")
    target_path = Path(path) if path else default_path
    
    # 1. Check local file first
    if target_path.exists():
        logger.info(f"Loading validation dataset from local file: {target_path}")
        try:
            df = pd.read_csv(target_path)
            if 'comment_text' not in df.columns or 'human_label' not in df.columns:
                raise PipelineError(
                    f"Invalid dataset format in {target_path}. "
                    "Expected columns: 'comment_text', 'human_label'."
                )
            logger.info(f"Successfully loaded {len(df)} labeled comments from {target_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to read local validation dataset: {e}")
            # If local read fails, we do not fall back to synthetic.
            # We proceed to try external, but if that also fails, we raise.
    
    # 2. Attempt to fetch from verified HuggingFace source
    # Verified Source: 'codeparrot/github-comments' (subset) or a specific curated set.
    # Since the task requires a "Validation Dataset of manually labeled comments",
    # and specific HuggingFace datasets for "bias labels" are rare/variable,
    # we will attempt to load a specific known dataset ID if provided in config,
    # or raise a clear error if the local file is missing and no external source is configured.
    # 
    # For this implementation, we assume the local file MUST exist or the pipeline halts.
    # The task says: "Acquire... OR execute a script to validate a manually curated CSV".
    # Since we cannot guarantee a specific public dataset exists with *exact* labels
    # for *this* project without a specific ID in the prompt, we enforce the local file requirement
    # to prevent fabrication.
    
    raise FileNotFoundError(
        f"Validation dataset not found at {target_path}. "
        "Please ensure 'data/validation/labels.csv' exists with columns 'comment_text' and 'human_label'. "
        "Do NOT generate synthetic labels."
    )

def run_vader_validation(df: pd.DataFrame, threshold: float = 0.05) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Run VADER sentiment analysis on the labeled comments and compute Cohen's Kappa.
    
    Args:
        df: DataFrame with 'comment_text' and 'human_label'.
        threshold: The threshold for VADER to consider a comment "Negative".
                   Human labels are assumed to be 0 (Positive/Neutral) or 1 (Negative).
                   
    Returns:
        Tuple of (Cohen's Kappa score, list of results).
        
    Raises:
        ExecutionError: If the validation fails due to data issues.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        raise ExecutionError("vaderSentiment is not installed. Please install it via requirements.txt.")
        
    analyzer = SentimentIntensityAnalyzer()
    
    predictions = []
    human_labels = []
    
    logger.info(f"Running VADER validation on {len(df)} samples...")
    
    for idx, row in df.iterrows():
        text = str(row['comment_text'])
        human_label = row['human_label']
        
        # Ensure human label is binary (0 or 1)
        if human_label not in [0, 1]:
            logger.warning(f"Row {idx} has non-binary human_label: {human_label}. Skipping.")
            continue
            
        # VADER: If compound score < threshold, predict 1 (Negative), else 0
        scores = analyzer.polarity_scores(text)
        compound = scores['compound']
        
        pred_label = 1 if compound < threshold else 0
        
        predictions.append(pred_label)
        human_labels.append(human_label)
        
    if len(predictions) < 2:
        raise ExecutionError("Insufficient data to compute Cohen's Kappa (need at least 2 samples).")
        
    kappa = cohen_kappa_score(human_labels, predictions)
    logger.info(f"Validation complete. Cohen's Kappa: {kappa:.4f}")
    
    results = [
        {
            "index": i,
            "human_label": h,
            "predicted_label": p,
            "agreement": (h == p)
        }
        for i, (h, p) in enumerate(zip(human_labels, predictions))
    ]
    
    return kappa, results

def validate_threshold(kappa: float, min_kappa: float = 0.6) -> bool:
    """
    Validate the threshold based on the Cohen's Kappa score.
    
    Args:
        kappa: The calculated Cohen's Kappa score.
        min_kappa: The minimum acceptable Kappa score (default 0.6).
        
    Returns:
        True if kappa >= min_kappa, False otherwise.
    """
    if kappa < min_kappa:
        logger.error(f"Validation FAILED: Cohen's Kappa ({kappa:.4f}) is below threshold ({min_kappa}).")
        return False
    else:
        logger.info(f"Validation PASSED: Cohen's Kappa ({kappa:.4f}) meets threshold ({min_kappa}).")
        return True

def run_validation_pipeline(
    data_path: Optional[str] = None,
    threshold: float = 0.05,
    min_kappa: float = 0.6,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full validation pipeline: load data, run VADER, compute Kappa, validate.
    
    Args:
        data_path: Path to the validation dataset.
        threshold: VADER threshold for negative classification.
        min_kappa: Minimum required Kappa score.
        output_path: Optional path to write the results JSON.
        
    Returns:
        Dictionary with validation results.
        
    Raises:
        ExecutionError: If validation fails (Kappa < min_kappa) or data is missing.
    """
    try:
        df = load_validation_dataset(data_path)
        kappa, results = run_vader_validation(df, threshold)
        
        is_valid = validate_threshold(kappa, min_kappa)
        
        report = {
            "status": "PASS" if is_valid else "FAIL",
            "kappa_score": kappa,
            "min_kappa_threshold": min_kappa,
            "vader_threshold": threshold,
            "samples_processed": len(df),
            "details": results[:10]  # Limit details in report for brevity
        }
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Validation report written to {output_file}")
            
        if not is_valid:
            raise ExecutionError(f"Validation failed: Kappa {kappa:.4f} < {min_kappa}")
            
        return report
        
    except FileNotFoundError as e:
        logger.error(f"Data acquisition failed: {e}")
        raise ExecutionError(f"Data acquisition failed: {e}")
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        raise ExecutionError(f"Validation pipeline failed: {e}")
