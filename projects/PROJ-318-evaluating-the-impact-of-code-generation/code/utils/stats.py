import logging
from typing import List, Tuple, Optional
from scipy import stats
from utils.exceptions import StatsException

logger = logging.getLogger(__name__)

class SampleSizeException(StatsException):
    """Raised when sample size is insufficient for statistical power, but allows continuation with warning."""
    pass

def run_wilcoxon_test(human_scores: List[float], llm_scores: List[float]) -> Tuple[float, float, bool]:
    """
    Perform a Wilcoxon signed-rank test to compare paired human and LLM coverage scores.
    
    Args:
        human_scores: List of human docstring coverage scores.
        llm_scores: List of LLM docstring coverage scores.
        
    Returns:
        Tuple of (statistic, p_value, warning_issued)
        
    Raises:
        StatsException: If inputs are empty or lengths mismatch.
        SampleSizeException: If n < 30 (raised to trigger logging logic in caller, 
                             but this function returns the result anyway per T035a requirements).
    """
    if not human_scores or not llm_scores:
        raise StatsException("Cannot run Wilcoxon test: input lists are empty.")
    
    if len(human_scores) != len(llm_scores):
        raise StatsException(f"Length mismatch: human_scores ({len(human_scores)}) != llm_scores ({len(llm_scores)})")
    
    n = len(human_scores)
    warning_issued = False
    
    if n < 30:
        warning_msg = "Statistical power may be low (n < 30)"
        logger.warning(warning_msg)
        warning_issued = True
        # We do NOT raise here to stop execution; we log and proceed as per T035a
    
    try:
        # scipy.stats.wilcoxon returns (statistic, pvalue)
        statistic, p_value = stats.wilcoxon(human_scores, llm_scores)
        return float(statistic), float(p_value), warning_issued
    except Exception as e:
        raise StatsException(f"Wilcoxon test failed: {str(e)}") from e
