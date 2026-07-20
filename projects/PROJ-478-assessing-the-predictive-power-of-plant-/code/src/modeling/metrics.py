import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Union, List
from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve
from src.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_auc(y_true: Union[np.ndarray, pd.Series], y_score: Union[np.ndarray, pd.Series]) -> float:
    """
    Calculate the Area Under the Receiver Operating Characteristic Curve (AUC).
    
    Args:
        y_true: True binary labels (0 or 1).
        y_score: Target scores (probability estimates).
        
    Returns:
        float: AUC value between 0 and 1.
        
    Raises:
        ValueError: If inputs are empty or invalid.
    """
    if len(y_true) == 0 or len(y_score) == 0:
        raise ValueError("Input arrays cannot be empty for AUC calculation.")
    
    try:
        auc_val = roc_auc_score(y_true, y_score)
        logger.info(f"AUC calculated successfully: {auc_val:.4f}")
        return float(auc_val)
    except ValueError as e:
        logger.error(f"Failed to calculate AUC: {e}")
        raise

def calculate_tss(y_true: Union[np.ndarray, pd.Series], y_pred: Union[np.ndarray, pd.Series], threshold: float = 0.5) -> float:
    """
    Calculate the True Skill Statistic (TSS).
    
    TSS = Sensitivity + Specificity - 1
    Sensitivity = TP / (TP + FN)
    Specificity = TN / (TN + FP)
    
    Args:
        y_true: True binary labels.
        y_pred: Predicted binary labels (0 or 1).
        threshold: Threshold used to convert probabilities to classes (if y_pred is probabilities).
        
    Returns:
        float: TSS value between -1 and 1.
    """
    # If y_pred is probabilities, convert to binary using threshold
    if np.max(y_pred) > 1.0 or np.min(y_pred) < 0.0:
        # Assume already binary
        pass
    else:
        y_pred = (np.array(y_pred) >= threshold).astype(int)
        
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    tss_val = sensitivity + specificity - 1.0
    logger.info(f"TSS calculated: Sensitivity={sensitivity:.4f}, Specificity={specificity:.4f}, TSS={tss_val:.4f}")
    
    return float(tss_val)

def find_optimal_threshold(y_true: Union[np.ndarray, pd.Series], y_score: Union[np.ndarray, pd.Series]) -> Tuple[float, float]:
    """
    Find the optimal threshold that maximizes the True Skill Statistic (TSS).
    
    Args:
        y_true: True binary labels.
        y_score: Target scores (probability estimates).
        
    Returns:
        Tuple[float, float]: (optimal_threshold, max_tss_value)
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    
    # Sensitivity = TPR, Specificity = 1 - FPR
    # TSS = Sensitivity + Specificity - 1 = TPR + (1 - FPR) - 1 = TPR - FPR
    tss_values = tpr - fpr
    
    optimal_idx = np.argmax(tss_values)
    optimal_threshold = thresholds[optimal_idx]
    max_tss = tss_values[optimal_idx]
    
    logger.info(f"Optimal threshold found: {optimal_threshold:.4f} (Max TSS: {max_tss:.4f})")
    
    return float(optimal_threshold), float(max_tss)

def evaluate_model(y_true: Union[np.ndarray, pd.Series], y_score: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
    """
    Evaluate a model using AUC and TSS (with optimal threshold).
    
    Args:
        y_true: True binary labels.
        y_score: Target scores (probability estimates).
        
    Returns:
        Dict[str, float]: Dictionary containing 'auc' and 'tss' values.
    """
    auc_val = calculate_auc(y_true, y_score)
    optimal_threshold, tss_val = find_optimal_threshold(y_true, y_score)
    
    return {
        'auc': auc_val,
        'tss': tss_val,
        'optimal_threshold': optimal_threshold
    }

def generate_metrics_report(results: List[Dict[str, any]], output_path: str) -> None:
    """
    Generate a summary report of metrics across multiple species/evaluations.
    
    Args:
        results: List of dictionaries containing metrics per species (e.g., {'species': 'X', 'auc': 0.8, 'tss': 0.6}).
        output_path: Path to save the CSV report.
    """
    if not results:
        logger.warning("No results provided for report generation.")
        return
        
    df = pd.DataFrame(results)
    
    # Ensure numeric columns
    numeric_cols = ['auc', 'tss']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate summary statistics
    summary = df[numeric_cols].describe()
    
    # Save detailed results
    df.to_csv(output_path, index=False)
    logger.info(f"Metrics report saved to {output_path}")
    
    # Log summary
    logger.info(f"Summary Statistics:\n{summary}")
    
    return summary