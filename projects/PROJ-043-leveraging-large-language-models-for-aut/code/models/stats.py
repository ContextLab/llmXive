"""
Statistical validation module for the LLM refactoring pipeline.

Implements Paired T-Test (FR-005) to determine statistical significance
of refactoring improvements by comparing delta distributions against zero.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import numpy as np
from scipy import stats
from pydantic import BaseModel, Field

from utils.logging import get_logger, ValidationFailedError
from utils.schema_validation import OneSampleTTestResult, StatisticalTests

logger = get_logger(__name__)


class DeltaAnalysisResult(BaseModel):
    """Result container for delta analysis."""
    metric_name: str
    mean_delta: float
    std_delta: float
    t_statistic: float
    p_value: float
    significant: bool
    sample_size: int


def load_delta_data(data_path: Path) -> Dict[str, List[float]]:
    """
    Load refactoring results and extract delta distributions.
    
    Args:
        data_path: Path to refactoring_results.json
        
    Returns:
        Dictionary mapping metric names to lists of delta values.
        
    Raises:
        ValidationFailedError: If data file is missing or invalid.
    """
    if not data_path.exists():
        raise ValidationFailedError(f"Data file not found: {data_path}")
        
    import json
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        raise ValidationFailedError("Expected list of function results in data file")
        
    if len(data) == 0:
        raise ValidationFailedError("Data file is empty; cannot perform statistical analysis")
        
    # Extract delta values for each metric
    metrics = {
        'complexity_delta': [],
        'pylint_delta': [],
        'maintainability_delta': []
    }
    
    for record in data:
        if 'deltas' not in record:
            logger.warning(f"Record missing 'deltas' key: {record.get('hash', 'unknown')[:8]}...")
            continue
            
        deltas = record['deltas']
        for metric in metrics.keys():
            if metric in deltas and deltas[metric] is not None:
                try:
                    val = float(deltas[metric])
                    if not np.isnan(val) and not np.isinf(val):
                        metrics[metric].append(val)
                except (TypeError, ValueError):
                    logger.warning(f"Invalid delta value for {metric}: {deltas[metric]}")
                    
    # Validate we have sufficient data
    valid_metrics = {k: v for k, v in metrics.items() if len(v) > 0}
    
    if not valid_metrics:
        raise ValidationFailedError("No valid delta values found in data file")
        
    logger.info(f"Loaded delta data: { {k: len(v) for k, v in valid_metrics.items()} }")
    return valid_metrics


def perform_one_sample_ttest(
    delta_values: List[float],
    null_mean: float = 0.0,
    alpha: float = 0.05
) -> OneSampleTTestResult:
    """
    Perform a one-sample t-test comparing delta values against a null mean.
    
    This is mathematically equivalent to a paired t-test when testing
    the difference (delta) against zero.
    
    Args:
        delta_values: List of delta values (refactored - original).
        null_mean: The hypothesized mean under the null hypothesis (default: 0.0).
        alpha: Significance level for determining significance.
        
    Returns:
        OneSampleTTestResult with t-statistic, p-value, and significance flag.
        
    Raises:
        ValidationFailedError: If insufficient data points for analysis.
    """
    if len(delta_values) < 2:
        raise ValidationFailedError(
            f"Insufficient data points ({len(delta_values)}) for t-test; "
            "minimum 2 required"
        )
        
    delta_array = np.array(delta_values)
    
    # Check for zero variance (all values identical)
    if np.std(delta_array) == 0:
        logger.warning("Delta values have zero variance; t-test may be undefined")
        # If all deltas are exactly zero, t-statistic is undefined (0/0)
        # We handle this by returning p=1.0 (no evidence against null)
        if np.all(delta_array == null_mean):
            return OneSampleTTestResult(
                t_statistic=0.0,
                p_value=1.0,
                significant=False,
                sample_size=len(delta_values),
                mean_delta=float(np.mean(delta_array)),
                std_delta=0.0
            )
    
    # Perform one-sample t-test
    t_stat, p_value = stats.ttest_1samp(delta_array, popmean=null_mean)
    
    significant = p_value < alpha
    
    logger.info(
        f"T-Test Results: t={t_stat:.4f}, p={p_value:.4f}, "
        f"significant={significant} (alpha={alpha})"
    )
    
    return OneSampleTTestResult(
        t_statistic=float(t_stat),
        p_value=float(p_value),
        significant=significant,
        sample_size=len(delta_values),
        mean_delta=float(np.mean(delta_array)),
        std_delta=float(np.std(delta_array, ddof=1))
    )


def analyze_delta_distributions(
    data_path: Path,
    alpha: float = 0.05
) -> StatisticalTests:
    """
    Perform comprehensive statistical analysis on refactoring deltas.
    
    This function:
    1. Loads delta data from refactoring results
    2. Performs one-sample t-tests for each metric against zero
    3. Aggregates results into a StatisticalTests object
    
    Args:
        data_path: Path to refactoring_results.json
        alpha: Significance level (default: 0.05)
        
    Returns:
        StatisticalTests object containing results for all metrics.
        
    Raises:
        ValidationFailedError: If data loading or analysis fails.
    """
    logger.info(f"Starting statistical analysis on {data_path}")
    
    # Load delta data
    delta_data = load_delta_data(data_path)
    
    # Perform t-tests for each metric
    results = {}
    for metric_name, values in delta_data.items():
        logger.info(f"Analyzing {metric_name} (n={len(values)})")
        results[metric_name] = perform_one_sample_ttest(values, alpha=alpha)
        
    # Construct StatisticalTests object
    # Map our metric names to the expected schema field names
    ttest_results = {
        'complexity': results.get('complexity_delta'),
        'pylint': results.get('pylint_delta'),
        'maintainability': results.get('maintainability_delta')
    }
    
    # Filter out None values (metrics that weren't present in data)
    ttest_results = {k: v for k, v in ttest_results.items() if v is not None}
    
    if not ttest_results:
        raise ValidationFailedError("No valid t-test results to report")
        
    statistical_tests = StatisticalTests(**ttest_results)
    
    logger.info("Statistical analysis completed successfully")
    return statistical_tests


def run_statistical_tests(
    data_path: Path,
    output_path: Optional[Path] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Main entry point for running statistical tests on refactoring results.
    
    Args:
        data_path: Path to refactoring_results.json
        output_path: Optional path to save results JSON
        alpha: Significance level (default: 0.05)
        
    Returns:
        Dictionary containing test results and summary statistics.
    """
    logger.info("Running statistical tests...")
    
    # Perform analysis
    statistical_tests = analyze_delta_distributions(data_path, alpha=alpha)
    
    # Convert to dictionary for output
    results_dict = statistical_tests.model_dump()
    
    # Add summary
    significant_count = sum(1 for r in results_dict.values() if r and r.get('significant'))
    total_tests = len([r for r in results_dict.values() if r is not None])
    
    results_dict['summary'] = {
        'total_tests': total_tests,
        'significant_results': significant_count,
        'alpha': alpha,
        'interpretation': (
            f"Found {significant_count}/{total_tests} metrics with statistically "
            f"significant improvement (p < {alpha})"
        )
    }
    
    # Save to file if output path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        
    return results_dict


def main():
    """CLI entry point for statistical analysis."""
    import argparse
    from utils.logging import setup_logging
    
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Perform statistical tests on refactoring deltas"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/refactoring_results.json"),
        help="Path to refactoring results JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/statistical_tests.json"),
        help="Path to save test results"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_statistical_tests(
            data_path=args.input,
            output_path=args.output,
            alpha=args.alpha
        )
        
        # Print summary
        summary = results.get('summary', {})
        print(f"\nStatistical Analysis Summary:")
        print(f"  Total Tests: {summary.get('total_tests', 0)}")
        print(f"  Significant Results: {summary.get('significant_results', 0)}")
        print(f"  Alpha: {summary.get('alpha', 0.05)}")
        print(f"  Interpretation: {summary.get('interpretation', 'N/A')}")
        
        return 0
        
    except ValidationFailedError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during statistical analysis: {e}")
        raise


if __name__ == "__main__":
    import sys
    sys.exit(main())
