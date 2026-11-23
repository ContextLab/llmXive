"""
Analysis Service: Correlation and statistical analysis.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy.stats import pearsonr
import numpy as np
from lib.config import RESULTS_ROOT

logger = logging.getLogger(__name__)

class AnalysisServiceError(Exception):
    """Custom exception for analysis service errors."""
    pass

def load_divergence_scores(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load divergence scores from JSON file."""
    if file_path is None:
        file_path = RESULTS_ROOT / "divergence_scores.json"
    
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise AnalysisServiceError(f"Divergence scores file not found: {path_obj}")
    
    with open(path_obj, "r") as f:
        return json.load(f)

def load_simulated_failure_rates(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load simulated failure rates from JSON file."""
    if file_path is None:
        file_path = RESULTS_ROOT / "simulated_failures.json"
    
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise AnalysisServiceError(f"Simulated failures file not found: {path_obj}")
    
    with open(path_obj, "r") as f:
        return json.load(f)

def merge_datasets(divergence_data: List[Dict], failure_data: List[Dict]) -> List[Dict]:
    """Merge divergence scores with failure rates by problem_id."""
    failure_map = {item["problem_id"]: item for item in failure_data}
    merged = []
    
    for div_item in divergence_data:
        pid = div_item.get("problem_id")
        if pid in failure_map:
            merged_item = {**div_item, **failure_map[pid]}
            merged.append(merged_item)
        else:
            logger.warning(f"Problem ID {pid} not found in failure data, skipping.")
    
    return merged

def validate_sample_size(data: List[Dict], min_n: int = 30) -> bool:
    """Check if sample size is sufficient."""
    n = len(data)
    if n < min_n:
        logger.error(f"Insufficient sample size: {n} < {min_n}")
        return False
    return True

def compute_pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson correlation and p-value."""
    if len(x) != len(y):
        raise AnalysisServiceError("Input arrays must have same length.")
    
    if len(x) < 2:
        return 0.0, 1.0
    
    corr, p_val = pearsonr(x, y)
    return float(corr), float(p_val)

def analyze_correlation(merged_data: List[Dict]) -> Dict[str, Any]:
    """
    Analyze correlation between semantic divergence and failure rate.
    """
    if not validate_sample_size(merged_data):
        raise AnalysisServiceError("Sample size insufficient for correlation analysis.")
    
    # Extract vectors
    divergences = [item.get("semantic_divergence_score", 0.0) for item in merged_data]
    failure_rates = [item.get("simulated_failure_rate", 0.0) for item in merged_data]
    
    corr, p_val = compute_pearson_correlation(divergences, failure_rates)
    
    result = {
        "correlation": corr,
        "p_value": p_val,
        "sample_size": len(merged_data),
        "significant_negative": (p_val < 0.05 and corr < 0)
    }
    
    logger.info(f"Correlation: {corr:.4f}, p-value: {p_val:.4f}, Significant Negative: {result['significant_negative']}")
    return result

def run_analysis(divergence_file: Optional[str] = None, failure_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Full pipeline: Load, merge, validate, and analyze.
    """
    div_data = load_divergence_scores(divergence_file)
    fail_data = load_simulated_failure_rates(failure_file)
    
    merged = merge_datasets(div_data, fail_data)
    report = analyze_correlation(merged)
    
    return report
