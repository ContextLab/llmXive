import numpy as np
from scipy import stats
from typing import Tuple, Union

def pearson_r(y_true, y_pred):
    """Calculate Pearson correlation coefficient."""
    return stats.pearsonr(y_true, y_pred)[0]

def r_squared(y_true, y_pred):
    """Calculate R² score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def pearson_pvalue(y_true, y_pred):
    """Calculate p-value for Pearson correlation."""
    return stats.pearsonr(y_true, y_pred)[1]

def calculate_metrics(y_true, y_pred) -> Tuple[float, float, float]:
    """Calculate all metrics at once."""
    r = pearson_r(y_true, y_pred)
    r2 = r_squared(y_true, y_pred)
    p = pearson_pvalue(y_true, y_pred)
    return r, r2, p
