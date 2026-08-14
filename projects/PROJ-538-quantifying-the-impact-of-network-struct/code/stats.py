"""
Statistical correlation and significance testing.
"""
import numpy as np
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.power import FTestPower
from typing import List, Dict, Any
from .utils import get_logger

logger = get_logger(__name__)

class CorrelationAnalyzer:
    """
    Analyzes correlation between metrics and thermal conductivity.
    """
    def __init__(self):
        self.logger = logger

    def analyze(self, metrics_list: List[Dict[str, float]], conductivities: List[float]) -> Dict[str, Any]:
        """
        Performs Pearson/Spearman correlation and Bonferroni correction.
        """
        if len(metrics_list) < 2:
            return {"error": "Insufficient data"}

        # Flatten metrics
        metric_names = list(metrics_list[0].keys())
        results = {}

        for name in metric_names:
            x = [m.get(name, np.nan) for m in metrics_list]
            x = np.array(x)
            y = np.array(conductivities)

            # Handle NaNs
            mask = ~np.isnan(x) & ~np.isnan(y)
            if np.sum(mask) < 2:
                continue

            x_clean = x[mask]
            y_clean = y[mask]

            # Pearson
            r_pearson, p_pearson = pearsonr(x_clean, y_clean)
            # Spearman
            r_spearman, p_spearman = spearmanr(x_clean, y_clean)

            # Bonferroni correction
            n_tests = len(metric_names)
            p_corr_pearson = min(p_pearson * n_tests, 1.0)
            p_corr_spearman = min(p_spearman * n_tests, 1.0)

            results[name] = {
                "pearson": r_pearson,
                "p_value_pearson": p_pearson,
                "p_value_pearson_corrected": p_corr_pearson,
                "spearman": r_spearman,
                "p_value_spearman": p_spearman,
                "p_value_spearman_corrected": p_corr_spearman
            }

        # Power Analysis
        if len(x_clean) >= 20:
            f2 = (results[metric_names[0]]["pearson"] ** 2) / (1 - results[metric_names[0]]["pearson"] ** 2)
            power = FTestPower().power(effect_size=f2, nobs1=len(x_clean), alpha=0.05, df_num=1)
            results["power_analysis"] = {"power": power}
        else:
            results["power_analysis"] = {"warning": "N < 20, power analysis unreliable"}

        return results
