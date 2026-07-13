import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Tuple, Dict, Any, Optional
import logging

def compute_sdt_metrics(hits, misses, false_alarms, correct_rejections):
    """Compute d' and criterion."""
    hit_rate = hits / (hits + misses)
    fa_rate = false_alarms / (false_alarms + correct_rejections)
    
    hit_rate = np.clip(hit_rate, 0.001, 0.999)
    fa_rate = np.clip(fa_rate, 0.001, 0.999)
    
    d_prime = norm.ppf(hit_rate) - norm.ppf(fa_rate)
    criterion = -0.5 * (norm.ppf(hit_rate) + norm.ppf(fa_rate))
    
    return d_prime, criterion

def compute_sdt_from_trials(responses, labels):
    """Compute d' from trial-wise responses and labels."""
    hits = ((responses == 1) & (labels == 1)).sum()
    misses = ((responses == 0) & (labels == 1)).sum()
    false_alarms = ((responses == 1) & (labels == 0)).sum()
    correct_rejections = ((responses == 0) & (labels == 0)).sum()
    
    return compute_sdt_metrics(hits, misses, false_alarms, correct_rejections)

def compute_type2_auc(accuracy, confidence):
    """
    Compute Type-2 AUC (meta-d') approximation.
    Simplified implementation for pipeline demonstration.
    """
    # In a real implementation, this would calculate the area under the Type-2 ROC curve.
    # Here we use a heuristic based on correlation between accuracy and confidence.
    if len(accuracy) != len(confidence):
        raise ValueError("Accuracy and confidence must be same length")
    
    corr = np.corrcoef(accuracy, confidence)[0, 1]
    if np.isnan(corr):
        return 0.5
    return 0.5 + (corr * 0.5)

def compute_meta_d_prime(accuracy, confidence):
    """Compute meta-d' (simplified)."""
    auc = compute_type2_auc(accuracy, confidence)
    return auc * 2 # Placeholder scaling

def calculate_trial_accuracy(responses, labels):
    """Calculate accuracy from trial responses."""
    return (responses == labels).mean()

def validate_trial_data(df):
    """Validate that required columns exist."""
    required = ['participant_response', 'source_label', 'confidence_rating']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return True

def compute_group_sdt_metrics(df):
    """Compute group-level SDT metrics."""
    responses = df['participant_response'].values
    labels = df['source_label'].values
    return compute_sdt_from_trials(responses, labels)