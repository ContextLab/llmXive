import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Union
from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve

from src.utils.logging import get_logger

logger = get_logger()

def calculate_auc(y_true: Union[np.ndarray, pd.Series], y_score: Union[np.ndarray, pd.Series]) -> float:
    return roc_auc_score(y_true, y_score)

def calculate_tss(y_true: Union[np.ndarray, pd.Series], y_pred: Union[np.ndarray, pd.Series]) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)
    return sensitivity + specificity - 1

def find_optimal_threshold(y_true: Union[np.ndarray, pd.Series], y_score: Union[np.ndarray, pd.Series]) -> float:
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    # Maximize TSS = Sensitivity + Specificity - 1
    # Specificity = 1 - FPR
    # TSS = TPR + (1 - FPR) - 1 = TPR - FPR
    tss = tpr - fpr
    idx = np.argmax(tss)
    return thresholds[idx]

def evaluate_model(
    y_true: Union[np.ndarray, pd.Series],
    y_score: Union[np.ndarray, pd.Series],
    y_pred: Optional[Union[np.ndarray, pd.Series]] = None
) -> Dict[str, float]:
    auc = calculate_auc(y_true, y_score)
    
    if y_pred is None:
        optimal_thresh = find_optimal_threshold(y_true, y_score)
        y_pred = (y_score >= optimal_thresh).astype(int)
    
    tss = calculate_tss(y_true, y_pred)
    
    return {
        "auc": auc,
        "tss": tss,
        "optimal_threshold": optimal_thresh if y_pred is None else None,
    }

def generate_metrics_report(results: Dict[str, Dict[str, float]]) -> str:
    lines = ["Metrics Report"]
    lines.append("=" * 20)
    for species, metrics in results.items():
        lines.append(f"Species: {species}")
        lines.append(f"  AUC: {metrics['auc']:.4f}")
        lines.append(f"  TSS: {metrics['tss']:.4f}")
    return "\n".join(lines)
