"""
Statistical testing utilities for the llmXive pipeline.

This module provides statistical analysis tools, specifically the Wilcoxon
signed-rank test for paired samples, to compare human-written docstrings
against LLM-generated ones.
"""

import logging
from typing import List, Tuple, Optional

from scipy import stats

logger = logging.getLogger(__name__)


class StatsException(Exception):
    """Base exception for statistical operations."""
    pass


class SampleSizeException(StatsException):
    """Raised when the sample size is insufficient for statistical testing."""
    pass


def run_wilcoxon_test(
    human_scores: List[float],
    llm_scores: List[float],
    min_sample_size: int = 30
) -> Tuple[float, float, dict]:
    """
    Perform a Wilcoxon signed-rank test to compare paired human and LLM scores.

    This function implements the Wilcoxon signed-rank test (Wikipedia: Wilcoxon
    signed-rank test, https://en.wikipedia.org/wiki/Wilcoxon_signed-rank_test)
    to determine if there is a statistically significant difference between
    two related samples (human vs. LLM docstring coverage scores).

    Args:
        human_scores: List of float scores from human-written docstrings.
        llm_scores: List of float scores from LLM-generated docstrings.
        min_sample_size: Minimum required sample size to proceed. Defaults to 30.

    Returns:
        Tuple containing:
            - statistic (float): The Wilcoxon test statistic (W).
            - p_value (float): The two-sided p-value.
            - metadata (dict): Additional information including sample size and warning.

    Raises:
        SampleSizeException: If either score list has fewer than min_sample_size items.
        StatsException: If lists are not of equal length or contain invalid data.
    """
    if len(human_scores) != len(llm_scores):
        raise StatsException(
            f"Score lists must be of equal length. "
            f"Got {len(human_scores)} human scores and {len(llm_scores)} LLM scores."
        )

    if len(human_scores) < 2:
        raise StatsException("At least 2 samples are required for the Wilcoxon test.")

    # Log warning if sample size is below recommended threshold but proceed
    warning_msg = ""
    if len(human_scores) < min_sample_size:
        warning_msg = (
            f"Sample size ({len(human_scores)}) is below recommended minimum "
            f"({min_sample_size}). Results may lack statistical power."
        )
        logger.warning(warning_msg)

    try:
        # Perform the Wilcoxon signed-rank test
        # Returns: statistic, pvalue
        statistic, p_value = stats.wilcoxon(human_scores, llm_scores)
    except ValueError as e:
        raise StatsException(f"Wilcoxon test failed due to invalid input values: {e}")
    except Exception as e:
        raise StatsException(f"Wilcoxon test failed with unexpected error: {e}")

    metadata = {
        "sample_size": len(human_scores),
        "warning": warning_msg,
        "test_type": "wilcoxon_signed_rank",
        "alternative": "two-sided"
    }

    logger.info(
        f"Wilcoxon test completed: W={statistic:.4f}, p={p_value:.6f}, "
        f"n={len(human_scores)}"
    )

    return statistic, p_value, metadata