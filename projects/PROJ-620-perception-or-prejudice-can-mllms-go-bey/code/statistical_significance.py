#!/usr/bin/env python3
"""Statistical significance testing for model comparisons."""
import numpy as np
from scipy import stats

def paired_ttest(model1_scores, model2_scores):
    """Perform paired t-test for model comparison."""
    t_stat, p_value = stats.ttest_rel(model1_scores, model2_scores)
    return t_stat, p_value

def mcnemar_test(confusion_matrix):
    """Perform McNemar's test for paired nominal data."""
    b = confusion_matrix[0, 1]
    c = confusion_matrix[1, 0]
    chi2 = (b - c)**2 / (b + c) if (b + c) > 0 else 0
    p_value = 1 - stats.chi2.cdf(chi2, df=1)
    return chi2, p_value

def report_significance(model1_scores, model2_scores, test_type="ttest"):
    """Report significance testing results for top-model comparisons."""
    if test_type == "ttest":
        t_stat, p_value = paired_ttest(model1_scores, model2_scores)
        return f"Paired t-test: t={t_stat:.4f}, p={p_value:.4f}"
    else:
        raise ValueError(f"Unknown test type: {test_type}")
