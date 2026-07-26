import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy.stats import pearsonr
import numpy as np

from lib.config import RESULTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_divergence_scores(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load divergence scores from JSON file."""
    path = Path(file_path) if file_path else RESULTS_DIR / "divergence_scores.json"
    if not path.exists():
        raise FileNotFoundError(f"Divergence scores file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_simulated_failure_rates(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load simulated failure rates from JSON file."""
    # Placeholder for future simulation data
    # In a real scenario, this would load from results/cached_simulations.json
    logger.warning("Simulated failure rates not yet available. Returning empty list.")
    return []

def merge_datasets(divergence_data: List[Dict[str, Any]], failure_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge divergence scores with failure rates by problem_id."""
    failure_map = {item["problem_id"]: item for item in failure_data}
    merged = []
    
    for div_item in divergence_data:
        pid = div_item["problem_id"]
        if pid in failure_map:
            merged_item = {**div_item, **failure_map[pid]}
            merged.append(merged_item)
        else:
            # Include divergence data even if no failure data
            merged.append(div_item)
    
    return merged

def validate_sample_size(data: List[Dict[str, Any]], min_size: int = 30) -> bool:
    """
    Validate that the sample size is sufficient for statistical analysis.
    
    Args:
        data: List of records.
        min_size: Minimum required sample size.
        
    Returns:
        bool: True if sufficient, False otherwise.
    """
    if len(data) < min_size:
        logger.error(f"Insufficient sample size: {len(data)} < {min_size}")
        return False
    return True

def compute_pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p-value.
    
    Args:
        x: First variable.
        y: Second variable.
        
    Returns:
        Tuple[float, float]: (correlation, p-value)
    """
    return pearsonr(x, y)

def analyze_correlation(merged_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze correlation between divergence scores and failure rates.
    
    Args:
        merged_data: Merged dataset.
        
    Returns:
        Dict[str, Any]: Analysis results.
    """
    if not merged_data:
        return {"status": "no_data"}
    
    # Extract variables
    divergence_scores = [item["semantic_divergence_score"] for item in merged_data if "semantic_divergence_score" in item]
    failure_rates = [item["simulated_failure_rate"] for item in merged_data if "simulated_failure_rate" in item]
    
    if not divergence_scores or not failure_rates:
        logger.warning("Missing divergence scores or failure rates for correlation.")
        return {"status": "missing_variables"}
    
    if not validate_sample_size(merged_data):
        return {"status": "insufficient_sample_size"}
    
    corr, p_value = compute_pearson_correlation(divergence_scores, failure_rates)
    
    result = {
        "correlation": float(corr),
        "p_value": float(p_value),
        "sample_size": len(merged_data),
        "significant_negative": corr < 0 and p_value < 0.05
    }
    
    return result

def run_analysis(divergence_data: List[Dict[str, Any]], failure_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Run the full analysis pipeline.
    
    Args:
        divergence_data: Divergence scores.
        failure_data: Optional simulated failure rates.
        
    Returns:
        Dict[str, Any]: Analysis report.
    """
    if failure_data is None:
        failure_data = load_simulated_failure_rates()
    
    merged = merge_datasets(divergence_data, failure_data)
    analysis = analyze_correlation(merged)
    
    return analysis
