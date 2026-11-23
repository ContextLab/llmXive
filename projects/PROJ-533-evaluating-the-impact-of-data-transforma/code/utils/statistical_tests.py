"""
Utility statistical test functions used across the pipeline.
Provides minimal implementations for t-test, one-way ANOVA, Shapiro-Wilk,
and Friedman tests. These functions are deliberately lightweight – they
rely only on the standard scientific Python stack (scipy, numpy) which is
already available in the execution environment.
"""
import logging
from typing import Sequence, Tuple, List, Any

import numpy as np
from scipy import stats

# Set up a module‑level logger; the pipeline configures root logging.
log = logging.getLogger(__name__)


def t_test(group1: Sequence[float], group2: Sequence[float], equal_var: bool = True) -> Tuple[float, float]:
    """
    Perform an independent two‑sample t‑test.

    Parameters
    ----------
    group1, group2 : array‑like
        Samples from the two groups.
    equal_var : bool, default True
        Assume equal population variances.

    Returns
    -------
    statistic, pvalue : float
        t statistic and two‑tailed p‑value.
    """
    try:
        stat, p = stats.ttest_ind(group1, group2, equal_var=equal_var, nan_policy='omit')
        return float(stat), float(p)
    except Exception as e:
        log.error(f"t_test failed: {e}")
        raise


def anova_one_way(*groups: Sequence[float]) -> Tuple[float, float]:
    """
    One‑way ANOVA across two or more groups.

    Parameters
    ----------
    *groups : sequence of float arrays
        Each argument represents a group.

    Returns
    -------
    statistic, pvalue : float
        F statistic and p‑value.
    """
    try:
        # Convert each group to a NumPy array, dropping NaNs
        cleaned = [np.asarray(g, dtype=float)[~np.isnan(g)] for g in groups]
        stat, p = stats.f_oneway(*cleaned)
        return float(stat), float(p)
    except Exception as e:
        log.error(f"anova_one_way failed: {e}")
        raise


def shapiro_test(data: Sequence[float]) -> Tuple[float, float]:
    """
    Shapiro‑Wilk normality test.

    Returns
    -------
    statistic, pvalue : float
        Test statistic and p‑value.
    """
    try:
        stat, p = stats.shapiro(data)
        return float(stat), float(p)
    except Exception as e:
        log.error(f"shapiro_test failed: {e}")
        raise


def friedman_test(*samples: Sequence[float]) -> Tuple[float, float]:
    """
    Friedman chi‑square test for repeated measures.

    Parameters
    ----------
    *samples : sequence of float arrays
        Each array corresponds to a condition (e.g., baseline,
        box‑cox, yeo‑johnson, rank‑normal). All arrays must have the
        same length.

    Returns
    -------
    statistic, pvalue : float
        Friedman chi‑square statistic and p‑value.
    """
    try:
        # Ensure all samples have the same length
        lengths = [len(s) for s in samples]
        if len(set(lengths)) != 1:
            raise ValueError("All samples must have the same length for Friedman test")

        # Convert to list of arrays for scipy
        arrays = [np.asarray(s, dtype=float) for s in samples]
        stat, p = stats.friedmanchisquare(*arrays)
        return float(stat), float(p)
    except Exception as e:
        log.error(f"friedman_test failed: {e}")
        raise


__all__: List[str] = [
    "t_test",
    "anova_one_way",
    "shapiro_test",
    "friedman_test",
]
