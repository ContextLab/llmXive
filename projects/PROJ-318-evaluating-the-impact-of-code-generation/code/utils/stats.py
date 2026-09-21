import logging
from typing import List, Tuple, Optional
from scipy import stats
from utils.exceptions import StatsException

logger = logging.getLogger(__name__)

class StatsException(Exception):
    """Exception raised for statistical analysis errors."""
    pass

class SampleSizeException(StatsException):
    """Exception raised when sample size is critically low."""
    pass

def run_wilcoxon_test(human_scores: List[float], llm_scores: List[float]) -> Tuple[float, float]:
    """
    Perform a Wilcoxon signed-rank test on paired human vs. LLM coverage scores.

    Args:
        human_scores: List of human coverage scores.
        llm_scores: List of LLM coverage scores.

    Returns:
        Tuple of (statistic, p-value).

    Raises:
        StatsException: If inputs are invalid or test cannot be performed.
        SampleSizeException: If sample size is too small (but test proceeds with warning).
    """
    if len(human_scores) != len(llm_scores):
        raise StatsException("Human and LLM score lists must be of equal length.")
    
    if len(human_scores) == 0:
        raise StatsException("Score lists cannot be empty.")

    n = len(human_scores)
    
    # Log warning if sample size is small, but proceed
    if n < 30:
        warning_msg = f"Statistical power may be low (n < 30) [n={n}]. Proceeding with calculation."
        logger.warning(warning_msg)

    try:
        statistic, p_value = stats.wilcoxon(human_scores, llm_scores)
        logger.info(f"Wilcoxon test completed: statistic={statistic}, p-value={p_value}")
        return statistic, p_value
    except Exception as e:
        raise StatsException(f"Wilcoxon test failed: {str(e)}") from e
