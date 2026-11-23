"""
Analysis Service for User Story 2: Correlation of Divergence with Simulated Failure Rates.

This module implements the logic to merge divergence scores with simulated failure rates,
validate sample sizes, and perform Pearson correlation analysis.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy.stats import pearsonr
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisServiceError(Exception):
    """Custom exception for analysis service errors."""
    pass

class CorrelationResult:
    """Data class to hold correlation analysis results."""
    def __init__(self, correlation: float, p_value: float, n_samples: int, significant: bool):
        self.correlation = correlation
        self.p_value = p_value
        self.n_samples = n_samples
        self.significant = significant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation": self.correlation,
            "p_value": self.p_value,
            "n_samples": self.n_samples,
            "significant": self.significant
        }

class AnalysisReport:
    """Data class to hold the full analysis report."""
    def __init__(self, correlation_result: CorrelationResult, hypothesis_flag: str, details: Dict[str, Any]):
        self.correlation_result = correlation_result
        self.hypothesis_flag = hypothesis_flag
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_result": self.correlation_result.to_dict(),
            "hypothesis_flag": self.hypothesis_flag,
            "details": self.details
        }

def load_divergence_scores(file_path: str) -> List[Dict[str, Any]]:
    """
    Load divergence scores from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing divergence scores.
        
    Returns:
        List of dictionaries containing divergence scores.
        
    Raises:
        AnalysisServiceError: If file not found or invalid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise AnalysisServiceError(f"Divergence scores file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise AnalysisServiceError(f"Invalid JSON in divergence scores file: {e}")
    
    if not isinstance(data, list):
        raise AnalysisServiceError(f"Expected a list of records in {file_path}, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} divergence score records from {file_path}")
    return data

def load_simulated_failure_rates(file_path: str) -> List[Dict[str, Any]]:
    """
    Load simulated failure rates from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing simulated failure rates.
        
    Returns:
        List of dictionaries containing simulated failure rates.
        
    Raises:
        AnalysisServiceError: If file not found or invalid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise AnalysisServiceError(f"Simulated failure rates file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise AnalysisServiceError(f"Invalid JSON in simulated failure rates file: {e}")
    
    if not isinstance(data, list):
        raise AnalysisServiceError(f"Expected a list of records in {file_path}, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} simulated failure rate records from {file_path}")
    return data

def merge_datasets(divergence_data: List[Dict[str, Any]], failure_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge divergence scores with simulated failure rates based on problem_id.
    
    Args:
        divergence_data: List of divergence score records.
        failure_data: List of simulated failure rate records.
        
    Returns:
        List of merged records containing both divergence scores and failure rates.
        
    Raises:
        AnalysisServiceError: If no common problem_ids are found.
    """
    # Create lookup dictionaries
    divergence_lookup = {record.get('problem_id'): record for record in divergence_data if record.get('problem_id')}
    failure_lookup = {record.get('problem_id'): record for record in failure_data if record.get('problem_id')}
    
    common_ids = set(divergence_lookup.keys()) & set(failure_lookup.keys())
    
    if not common_ids:
        raise AnalysisServiceError("No common problem_ids found between divergence and failure datasets")
    
    logger.info(f"Merging datasets: {len(common_ids)} common problem_ids found")
    
    merged_records = []
    for problem_id in common_ids:
        merged_record = {
            **divergence_lookup[problem_id],
            **failure_lookup[problem_id]
        }
        merged_records.append(merged_record)
    
    logger.info(f"Merged dataset contains {len(merged_records)} records")
    return merged_records

def validate_sample_size(merged_data: List[Dict[str, Any]], min_size: int = 30) -> None:
    """
    Validate that the merged dataset meets the minimum sample size requirement.
    
    Args:
        merged_data: List of merged records.
        min_size: Minimum required sample size (default: 30).
        
    Raises:
        AnalysisServiceError: If sample size is insufficient.
    """
    n_samples = len(merged_data)
    if n_samples < min_size:
        raise AnalysisServiceError(
            f"Statistical Power Insufficient: Sample size N={n_samples} is less than required minimum of {min_size}"
        )
    logger.info(f"Sample size validation passed: N={n_samples} >= {min_size}")

def compute_pearson_correlation(merged_data: List[Dict[str, Any]]) -> CorrelationResult:
    """
    Compute Pearson correlation coefficient between divergence scores and failure rates.
    
    Args:
        merged_data: List of merged records containing 'semantic_divergence_score' and 'simulated_failure_rate'.
        
    Returns:
        CorrelationResult object with correlation coefficient, p-value, sample size, and significance flag.
        
    Raises:
        AnalysisServiceError: If required fields are missing or data is invalid.
    """
    divergence_scores = []
    failure_rates = []
    
    for record in merged_data:
        if 'semantic_divergence_score' not in record or 'simulated_failure_rate' not in record:
            logger.warning(f"Skipping record missing required fields: {record.get('problem_id', 'unknown')}")
            continue
        
        try:
            score = float(record['semantic_divergence_score'])
            rate = float(record['simulated_failure_rate'])
            divergence_scores.append(score)
            failure_rates.append(rate)
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid numeric value in record {record.get('problem_id', 'unknown')}: {e}")
            continue
    
    if len(divergence_scores) < 2:
        raise AnalysisServiceError("Insufficient valid data points for correlation (need at least 2)")
    
    # Compute Pearson correlation
    correlation, p_value = pearsonr(divergence_scores, failure_rates)
    
    # Determine significance (p < 0.05)
    significant = p_value < 0.05
    
    logger.info(f"Pearson correlation: r={correlation:.4f}, p={p_value:.4f}, n={len(divergence_scores)}, significant={significant}")
    
    return CorrelationResult(
        correlation=correlation,
        p_value=p_value,
        n_samples=len(divergence_scores),
        significant=significant
    )

def analyze_correlation(correlation_result: CorrelationResult) -> str:
    """
    Analyze the correlation result and return a hypothesis flag.
    
    Args:
        correlation_result: CorrelationResult object from compute_pearson_correlation.
        
    Returns:
        String flag indicating the hypothesis status.
    """
    if correlation_result.significant and correlation_result.correlation < 0:
        return "Significant Negative Correlation"
    elif correlation_result.significant and correlation_result.correlation > 0:
        return "Significant Positive Correlation"
    elif not correlation_result.significant:
        return "No Significant Correlation"
    else:
        return "Unknown"

def run_analysis(
    divergence_file: str,
    failure_file: str,
    min_sample_size: int = 30
) -> AnalysisReport:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        divergence_file: Path to divergence scores JSON file.
        failure_file: Path to simulated failure rates JSON file.
        min_sample_size: Minimum required sample size.
        
    Returns:
        AnalysisReport object with full analysis results.
    """
    logger.info("Starting correlation analysis pipeline")
    
    # Load data
    divergence_data = load_divergence_scores(divergence_file)
    failure_data = load_simulated_failure_rates(failure_file)
    
    # Merge datasets
    merged_data = merge_datasets(divergence_data, failure_data)
    
    # Validate sample size
    validate_sample_size(merged_data, min_sample_size)
    
    # Compute correlation
    correlation_result = compute_pearson_correlation(merged_data)
    
    # Analyze hypothesis
    hypothesis_flag = analyze_correlation(correlation_result)
    
    # Build report details
    details = {
        "divergence_file": divergence_file,
        "failure_file": failure_file,
        "divergence_records_loaded": len(divergence_data),
        "failure_records_loaded": len(failure_data),
        "merged_records": len(merged_data),
        "min_sample_size_required": min_sample_size
    }
    
    report = AnalysisReport(
        correlation_result=correlation_result,
        hypothesis_flag=hypothesis_flag,
        details=details
    )
    
    logger.info(f"Analysis complete: {hypothesis_flag}")
    return report

def save_analysis_report(report: AnalysisReport, output_path: str) -> None:
    """
    Save the analysis report to a JSON file.
    
    Args:
        report: AnalysisReport object to save.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"Analysis report saved to {output_path}")