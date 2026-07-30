"""
Analysis Service for Semantic Divergence Diagnostic.

Handles correlation analysis between divergence scores and simulated failure rates.
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

class CorrelationResult:
    """Data class to hold correlation analysis results."""
    def __init__(
        self,
        correlation: float,
        p_value: float,
        sample_size: int,
        is_significant: bool,
        is_negative: bool,
        flag: str
    ):
        self.correlation = correlation
        self.p_value = p_value
        self.sample_size = sample_size
        self.is_significant = is_significant
        self.is_negative = is_negative
        self.flag = flag

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation": self.correlation,
            "p_value": self.p_value,
            "sample_size": self.sample_size,
            "is_significant": self.is_significant,
            "is_negative": self.is_negative,
            "flag": self.flag
        }

class AnalysisReport:
    """Data class to hold the full analysis report."""
    def __init__(
        self,
        correlation_result: CorrelationResult,
        merged_data: List[Dict[str, Any]],
        threshold: float = 0.05
    ):
        self.correlation_result = correlation_result
        self.merged_data = merged_data
        self.threshold = threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_result": self.correlation_result.to_dict(),
            "threshold": self.threshold,
            "sample_count": len(self.merged_data)
        }

def load_divergence_scores(file_path: str) -> List[Dict[str, Any]]:
    """
    Load divergence scores from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing divergence scores.
        
    Returns:
        List of dictionaries containing divergence scores.
        
    Raises:
        AnalysisServiceError: If the file cannot be loaded or parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise AnalysisServiceError(f"Divergence scores file not found: {file_path}")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise AnalysisServiceError("Divergence scores file must contain a JSON list")
        return data
    except json.JSONDecodeError as e:
        raise AnalysisServiceError(f"Failed to parse divergence scores JSON: {e}")

def load_simulated_failure_rates(file_path: str) -> List[Dict[str, Any]]:
    """
    Load simulated failure rates from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing failure rates.
        
    Returns:
        List of dictionaries containing failure rates.
        
    Raises:
        AnalysisServiceError: If the file cannot be loaded or parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise AnalysisServiceError(f"Simulated failure rates file not found: {file_path}")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise AnalysisServiceError("Simulated failure rates file must contain a JSON list")
        return data
    except json.JSONDecodeError as e:
        raise AnalysisServiceError(f"Failed to parse failure rates JSON: {e}")

def merge_datasets(
    divergence_data: List[Dict[str, Any]],
    failure_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge divergence scores with failure rates by problem_id.
    
    Args:
        divergence_data: List of divergence score records.
        failure_data: List of failure rate records.
        
    Returns:
        List of merged records containing both scores and failure rates.
        
    Raises:
        AnalysisServiceError: If merging fails or required fields are missing.
    """
    # Create a lookup dictionary for failure data
    failure_lookup = {}
    for record in failure_data:
        if 'problem_id' not in record:
            logger.warning("Skipping failure record missing problem_id")
            continue
        failure_lookup[record['problem_id']] = record
    
    merged = []
    missing_count = 0
    
    for div_record in divergence_data:
        if 'problem_id' not in div_record:
            logger.warning("Skipping divergence record missing problem_id")
            continue
        
        problem_id = div_record['problem_id']
        if problem_id in failure_lookup:
            merged_record = {**div_record, **failure_lookup[problem_id]}
            merged.append(merged_record)
        else:
            missing_count += 1
            # Optionally log missing matches
            # logger.debug(f"No failure data for problem_id: {problem_id}")
    
    if missing_count > 0:
        logger.info(f"Merged {len(merged)} records; {missing_count} divergence records had no matching failure data")
    
    return merged

def validate_sample_size(merged_data: List[Dict[str, Any]], min_size: int = 30) -> None:
    """
    Validate that the merged dataset meets the minimum sample size requirement.
    
    Args:
        merged_data: List of merged records.
        min_size: Minimum required sample size (default 30).
        
    Raises:
        AnalysisServiceError: If sample size is insufficient.
    """
    n = len(merged_data)
    if n < min_size:
        raise AnalysisServiceError(
            f"Insufficient Sample Size for Power Analysis: N={n} < {min_size}. "
            f"Statistical Power Insufficient."
        )
    logger.info(f"Sample size validation passed: N={n} >= {min_size}")

def compute_pearson_correlation(
    x: List[float],
    y: List[float]
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p-value.
    
    Args:
        x: First variable (divergence scores).
        y: Second variable (failure rates).
        
    Returns:
        Tuple of (correlation coefficient, p-value).
        
    Raises:
        AnalysisServiceError: If computation fails.
    """
    if len(x) != len(y) or len(x) == 0:
        raise AnalysisServiceError("Input arrays must be non-empty and of equal length")
    
    try:
        corr, p_val = pearsonr(x, y)
        return float(corr), float(p_val)
    except Exception as e:
        raise AnalysisServiceError(f"Pearson correlation computation failed: {e}")

def analyze_correlation(
    merged_data: List[Dict[str, Any]],
    score_key: str = "semantic_divergence_score",
    failure_key: str = "simulated_failure_rate",
    alpha: float = 0.05
) -> CorrelationResult:
    """
    Analyze the correlation between divergence scores and failure rates.
    
    Implements SC-001: Flag "Significant Negative Correlation" if p < alpha and correlation < 0.
    
    Args:
        merged_data: List of merged records.
        score_key: Key for divergence scores in records.
        failure_key: Key for failure rates in records.
        alpha: Significance level (default 0.05).
        
    Returns:
        CorrelationResult object with analysis findings.
        
    Raises:
        AnalysisServiceError: If required fields are missing or analysis fails.
    """
    # Extract vectors
    scores = []
    failure_rates = []
    
    for record in merged_data:
        if score_key not in record or failure_key not in record:
            continue
        val_score = record[score_key]
        val_failure = record[failure_key]
        
        if val_score is not None and val_failure is not None:
            try:
                scores.append(float(val_score))
                failure_rates.append(float(val_failure))
            except (ValueError, TypeError):
                continue
    
    if len(scores) == 0:
        raise AnalysisServiceError("No valid data pairs found for correlation analysis")
    
    # Compute correlation
    corr, p_val = compute_pearson_correlation(scores, failure_rates)
    
    # Determine significance and direction
    is_significant = p_val < alpha
    is_negative = corr < 0
    
    # Apply SC-001 logic
    if is_significant and is_negative:
        flag = "Significant Negative Correlation"
    elif is_significant and not is_negative:
        flag = "Significant Positive Correlation"
    elif not is_significant and is_negative:
        flag = "Non-Significant Negative Correlation"
    else:
        flag = "Non-Significant Positive Correlation"
    
    logger.info(f"Correlation Analysis: r={corr:.4f}, p={p_val:.4f}, flag='{flag}'")
    
    return CorrelationResult(
        correlation=corr,
        p_value=p_val,
        sample_size=len(scores),
        is_significant=is_significant,
        is_negative=is_negative,
        flag=flag
    )

def run_analysis(
    divergence_file: str,
    failure_file: str,
    output_file: Optional[str] = None,
    score_key: str = "semantic_divergence_score",
    failure_key: str = "simulated_failure_rate",
    alpha: float = 0.05,
    min_sample_size: int = 30
) -> AnalysisReport:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        divergence_file: Path to divergence scores JSON.
        failure_file: Path to failure rates JSON.
        output_file: Optional path to save the report JSON.
        score_key: Key for divergence scores.
        failure_key: Key for failure rates.
        alpha: Significance level.
        min_sample_size: Minimum sample size requirement.
        
    Returns:
        AnalysisReport object with results.
        
    Raises:
        AnalysisServiceError: If any step fails.
    """
    logger.info("Starting correlation analysis...")
    
    # Load data
    divergence_data = load_divergence_scores(divergence_file)
    failure_data = load_simulated_failure_rates(failure_file)
    
    # Merge
    merged = merge_datasets(divergence_data, failure_data)
    
    # Validate sample size
    validate_sample_size(merged, min_sample_size)
    
    # Analyze
    result = analyze_correlation(
        merged,
        score_key=score_key,
        failure_key=failure_key,
        alpha=alpha
    )
    
    # Create report
    report = AnalysisReport(result, merged, threshold=alpha)
    
    # Save if path provided
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Analysis report saved to {output_file}")
    
    return report