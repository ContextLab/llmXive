"""
Tukey's Honest Significant Difference (HSD) Post-hoc Test.

Implements Tukey's HSD test for pairwise comparisons between group means
after a significant ANOVA result. This test controls the family-wise error rate
by adjusting for multiple comparisons.

This module uses `statsmodels` which is already pinned in `code/requirements.txt` (T002).
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import logging

# We assume statsmodels is available as per T002 requirements
try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    from statsmodels.stats.anova import AnovaRM
except ImportError:
    raise ImportError("Tukey HSD requires 'statsmodels'. Please ensure it is installed (T002).")

logger = logging.getLogger(__name__)


class TukeyHSDError(Exception):
    """Custom exception for Tukey HSD failures."""
    pass


def perform_tukey_hsd(values: Union[List[float], np.ndarray],
                      groups: Union[List[str], np.ndarray],
                      alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Tukey's HSD test for pairwise comparisons.

    Args:
        values: Array of numeric values (dependent variable).
        groups: Array of group labels (independent variable).
        alpha: Significance level for the test.

    Returns:
        Dictionary containing:
        - 'summary_table': String representation of the Tukey HSD summary.
        - 'reject_matrix': 2D array of booleans indicating significant differences.
        - 'p_values': 2D array of p-values for pairwise comparisons.
        - 'mean_diff': 2D array of mean differences.
        - 'groups': List of unique group names sorted.
    """
    if len(values) != len(groups):
        raise TukeyHSDError("Values and groups must have the same length.")

    if len(np.unique(groups)) < 2:
        raise TukeyHSDError("At least two distinct groups are required for Tukey HSD.")

    try:
        # Create a DataFrame for statsmodels
        data = pd.DataFrame({'value': values, 'group': groups})

        # Run Tukey HSD
        tukey = pairwise_tukeyhsd(endog=data['value'],
                                  groups=data['group'],
                                  alpha=alpha)

        # Extract results
        # tukey.test has attributes: mean_diff, pvals, reject, confint
        mean_diff = tukey.test.mean_diff
        pvals = tukey.test.pvals
        reject = tukey.test.reject

        # Get unique groups sorted to reconstruct matrix shape if needed,
        # but pairwise_tukeyhsd returns a condensed format (upper triangle).
        # We will return the raw arrays from the test object which are ordered
        # by the combinations of groups.
        groups_unique = sorted(tukey.groupsunique)

        # Construct a summary string
        summary_str = str(tukey)

        return {
            'summary_table': summary_str,
            'reject': reject.tolist(),
            'p_values': pvals.tolist(),
            'mean_diff': mean_diff.tolist(),
            'groups': groups_unique,
            'alpha': alpha
        }

    except Exception as e:
        logger.error(f"Tukey HSD test failed: {e}")
        raise TukeyHSDError(f"Failed to perform Tukey HSD: {e}") from e


def run_tukey_posthoc(data: Dict[str, List[float]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run Tukey HSD on a dictionary of group data.

    Args:
        data: Dictionary mapping group names to lists of values.
              Example: {'strategy_A': [1.2, 1.5], 'strategy_B': [2.1, 2.3]}
        alpha: Significance level.

    Returns:
        Dictionary containing Tukey HSD results.
    """
    if not data:
        raise TukeyHSDError("Data dictionary is empty.")

    values = []
    groups = []

    for group_name, group_values in data.items():
        if not group_values:
            logger.warning(f"Group '{group_name}' is empty and will be skipped.")
            continue
        values.extend(group_values)
        groups.extend([group_name] * len(group_values))

    if len(set(groups)) < 2:
        raise TukeyHSDError("Need at least two groups with data to run Tukey HSD.")

    return perform_tukey_hsd(values, groups, alpha)
