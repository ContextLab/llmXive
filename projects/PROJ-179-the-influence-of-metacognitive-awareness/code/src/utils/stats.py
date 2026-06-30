"""
Statistical utilities for Signal Detection Theory (SDT) and Type-2 AUC (Meta-d') calculations.

This module provides functions to compute:
- d' (d-prime) and criterion from trial data
- Type-2 AUC (meta-d') from confidence ratings and accuracy

Dependencies:
- scipy.stats
- numpy
- pandas
"""
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def compute_sdt_metrics(
    hits: int, 
    misses: int, 
    false_alarms: int, 
    correct_rejections: int
) -> Tuple[float, float]:
    """
    Compute d' (d-prime) and criterion from counts of hits, misses, false alarms, and correct rejections.
    
    Parameters:
        hits: Number of hits (signal present, response present)
        misses: Number of misses (signal present, response absent)
        false_alarms: Number of false alarms (signal absent, response present)
        correct_rejections: Number of correct rejections (signal absent, response absent)
    
    Returns:
        Tuple of (d_prime, criterion)
    
    Raises:
        ValueError: If any count is negative or if hit/FA rates are 0 or 1 (requires correction)
    """
    if hits < 0 or misses < 0 or false_alarms < 0 or correct_rejections < 0:
        raise ValueError("Counts cannot be negative")
    
    # Calculate hit rate and false alarm rate
    hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
    fa_rate = false_alarms / (false_alarms + correct_rejections) if (false_alarms + correct_rejections) > 0 else 0
    
    # Apply log-linear correction to avoid 0 or 1 rates
    # Adding 0.5 to numerator and 1 to denominator
    n_signal = hits + misses
    n_noise = false_alarms + correct_rejections
    
    if n_signal == 0 or n_noise == 0:
        raise ValueError("Cannot compute SDT metrics: need both signal and noise trials")
    
    hit_rate_corrected = (hits + 0.5) / (n_signal + 1)
    fa_rate_corrected = (false_alarms + 0.5) / (n_noise + 1)
    
    # Compute d' and criterion
    z_hit = norm.ppf(hit_rate_corrected)
    z_fa = norm.ppf(fa_rate_corrected)
    
    d_prime = z_hit - z_fa
    
    # Criterion = -0.5 * (z_hit + z_fa)
    criterion = -0.5 * (z_hit + z_fa)
    
    return d_prime, criterion

def compute_sdt_from_trials(
    trials: pd.DataFrame,
    response_col: str = 'participant_response',
    target_col: str = 'source_label',
    target_value: Any = 'internal'
) -> Tuple[float, float]:
    """
    Compute d' and criterion directly from trial-level data.
    
    Parameters:
        trials: DataFrame containing trial data
        response_col: Column name for participant response
        target_col: Column name for source label (ground truth)
        target_value: The value in target_col that represents "signal present"
    
    Returns:
        Tuple of (d_prime, criterion)
    """
    # Define signal present/absent
    signal_present = trials[target_col] == target_value
    signal_absent = ~signal_present
    
    # Define response present/absent (assuming binary response)
    # We assume 'present' or similar indicates a "yes" response
    # This logic may need adjustment based on actual data schema
    response_present = trials[response_col].apply(lambda x: str(x).lower() in ['present', 'yes', '1', 'true'])
    response_absent = ~response_present
    
    # Calculate counts
    hits = ((signal_present) & (response_present)).sum()
    misses = ((signal_present) & (response_absent)).sum()
    false_alarms = ((signal_absent) & (response_present)).sum()
    correct_rejections = ((signal_absent) & (response_absent)).sum()
    
    return compute_sdt_metrics(int(hits), int(misses), int(false_alarms), int(correct_rejections))

def compute_type2_auc(
    trials: pd.DataFrame,
    accuracy_col: str = 'accuracy',
    confidence_col: str = 'confidence_rating',
    split_col: Optional[str] = None,
    train_split_value: Any = 'train'
) -> float:
    """
    Compute Type-2 AUC (meta-d') from confidence ratings and accuracy.
    
    This function calculates the area under the Type-2 ROC curve, which represents
    metacognitive efficiency. It uses the training split of data if a split column is provided.
    
    Parameters:
        trials: DataFrame containing trial data with accuracy and confidence
        accuracy_col: Column name for binary accuracy (1=correct, 0=incorrect)
        confidence_col: Column name for confidence rating
        split_col: Optional column name indicating train/test split
        train_split_value: Value in split_col that indicates training data
    
    Returns:
        Type-2 AUC value (float between 0 and 1)
    """
    # Filter for training data if split column is provided
    if split_col is not None:
        if split_col not in trials.columns:
            logger.warning(f"Split column '{split_col}' not found in trials. Using all data.")
            train_data = trials
        else:
            train_data = trials[trials[split_col] == train_split_value]
    else:
        train_data = trials
    
    if len(train_data) == 0:
        raise ValueError("No training data available for Type-2 AUC calculation")
    
    # Ensure required columns exist
    if accuracy_col not in train_data.columns:
        raise ValueError(f"Accuracy column '{accuracy_col}' not found in data")
    if confidence_col not in train_data.columns:
        raise ValueError(f"Confidence column '{confidence_col}' not found in data")
    
    # Extract accuracy and confidence
    accuracy = train_data[accuracy_col].values
    confidence = train_data[confidence_col].values
    
    # Calculate Type-2 AUC
    # Type-2 AUC is the area under the curve of accuracy vs confidence threshold
    # We sort unique confidence thresholds and calculate accuracy at each threshold
    
    unique_thresholds = np.sort(np.unique(confidence))
    auc_values = []
    
    for threshold in unique_thresholds:
        # For each threshold, calculate accuracy of high-confidence responses
        high_conf_mask = confidence >= threshold
        if np.sum(high_conf_mask) > 0:
            threshold_accuracy = np.mean(accuracy[high_conf_mask])
            auc_values.append((threshold, threshold_accuracy))
    
    if len(auc_values) == 0:
        return 0.0
    
    # Calculate AUC using trapezoidal rule
    thresholds = [x[0] for x in auc_values]
    accuracies = [x[1] for x in auc_values]
    
    # Sort by threshold (should already be sorted, but ensure)
    sorted_pairs = sorted(zip(thresholds, accuracies), key=lambda x: x[0])
    thresholds = [x[0] for x in sorted_pairs]
    accuracies = [x[1] for x in sorted_pairs]
    
    # Trapezoidal integration
    auc = np.trapz(accuracies, thresholds)
    
    # Normalize by range of thresholds
    if thresholds[-1] - thresholds[0] > 0:
        auc = auc / (thresholds[-1] - thresholds[0])
    
    return float(auc)

def compute_meta_d_prime(
    trials: pd.DataFrame,
    accuracy_col: str = 'accuracy',
    confidence_col: str = 'confidence_rating',
    split_col: Optional[str] = None,
    train_split_value: Any = 'train'
) -> Dict[str, float]:
    """
    Compute meta-d' (Type-2 AUC) and related metrics from trial data.
    
    Parameters:
        trials: DataFrame containing trial data
        accuracy_col: Column name for binary accuracy
        confidence_col: Column name for confidence rating
        split_col: Optional column name indicating train/test split
        train_split_value: Value in split_col that indicates training data
    
    Returns:
        Dictionary containing:
            - type2_auc: Type-2 AUC value
            - meta_d_prime: meta-d' estimate (simplified as AUC * 2 for approximation)
            - n_trials: Number of trials used
            - mean_accuracy: Mean accuracy in training set
    """
    # Compute Type-2 AUC
    type2_auc = compute_type2_auc(
        trials, 
        accuracy_col, 
        confidence_col, 
        split_col, 
        train_split_value
    )
    
    # Simple approximation of meta-d' from Type-2 AUC
    # Note: Full meta-d' calculation requires more complex modeling
    # This is a simplified version for initial analysis
    meta_d_prime = type2_auc * 2  # Approximation
    
    # Calculate additional metrics
    if split_col is not None and split_col in trials.columns:
        train_data = trials[trials[split_col] == train_split_value]
    else:
        train_data = trials
    
    mean_accuracy = float(train_data[accuracy_col].mean())
    
    return {
        'type2_auc': type2_auc,
        'meta_d_prime': meta_d_prime,
        'n_trials': len(train_data),
        'mean_accuracy': mean_accuracy
    }

def calculate_trial_accuracy(
    trials: pd.DataFrame,
    response_col: str = 'participant_response',
    target_col: str = 'source_label',
    target_value: Any = 'internal'
) -> pd.DataFrame:
    """
    Add an accuracy column to the trials DataFrame based on response vs target.
    
    Parameters:
        trials: Input DataFrame
        response_col: Column name for participant response
        target_col: Column name for source label
        target_value: The value in target_col that represents the correct "signal"
    
    Returns:
        DataFrame with additional 'accuracy' column (1=correct, 0=incorrect)
    """
    df = trials.copy()
    
    # Determine correctness
    # Assuming response 'present' matches target 'internal' for correct detection
    # This logic should be adjusted based on actual experimental design
    df['accuracy'] = (
        (df[response_col].apply(lambda x: str(x).lower() in ['present', 'yes', '1', 'true'])) == 
        (df[target_col] == target_value)
    ).astype(int)
    
    return df

def validate_trial_data(
    trials: pd.DataFrame,
    required_columns: list = None
) -> bool:
    """
    Validate that the trial DataFrame contains required columns for SDT analysis.
    
    Parameters:
        trials: DataFrame to validate
        required_columns: List of required column names
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    if required_columns is None:
        required_columns = ['participant_response', 'source_label', 'confidence_rating']
    
    missing = [col for col in required_columns if col not in trials.columns]
    if missing:
        raise ValueError(f"Missing required columns for SDT analysis: {missing}")
    
    return True

def compute_group_sdt_metrics(
    trials: pd.DataFrame,
    group_col: str = 'participant_id',
    response_col: str = 'participant_response',
    target_col: str = 'source_label',
    target_value: Any = 'internal'
) -> pd.DataFrame:
    """
    Compute d' and criterion for each participant/group in the data.
    
    Parameters:
        trials: DataFrame with trial data
        group_col: Column name for grouping (e.g., participant_id)
        response_col: Column name for participant response
        target_col: Column name for source label
        target_value: Target value representing "signal present"
    
    Returns:
        DataFrame with d' and criterion for each group
    """
    results = []
    
    for group_id, group_data in trials.groupby(group_col):
        d_prime, criterion = compute_sdt_from_trials(
            group_data,
            response_col=response_col,
            target_col=target_col,
            target_value=target_value
        )
        
        results.append({
            group_col: group_id,
            'd_prime': d_prime,
            'criterion': criterion,
            'n_trials': len(group_data)
        })
    
    return pd.DataFrame(results)