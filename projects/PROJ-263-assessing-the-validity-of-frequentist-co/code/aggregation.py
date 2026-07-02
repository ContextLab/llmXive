import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from data_models.schemas import AggregateReport, validate_aggregate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRATICAL_SIGNIFICANCE_THRESHOLD = 0.01  # 1.0% deviation threshold (FR-011)

def load_coverage_records(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load coverage records from a JSON file."""
    if filepath is None:
        filepath = "data/processed/coverage_records.json"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Coverage records file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_population_means(filepath: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """Load population means from a JSON file."""
    if filepath is None:
        filepath = "data/processed/population_means.json"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Population means file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_mean_deviation(
    coverage_records: List[Dict[str, Any]],
    nominal_level: float = 0.95
) -> Dict[str, float]:
    """
    Calculate the mean deviation from nominal coverage across multiple UCI datasets.
    
    Args:
        coverage_records: List of coverage records from simulation
        nominal_level: The nominal confidence level (default 0.95)
    
    Returns:
        Dictionary mapping (dataset_id, sample_size, interval_type) to mean deviation
    """
    deviations = {}
    
    # Group records by dataset, sample size, and interval type
    groups = {}
    for record in coverage_records:
        key = (
            record['dataset_id'],
            record['sample_size'],
            record['interval_type']
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(record['contains_mean'])
    
    # Calculate mean deviation for each group
    for key, records in groups.items():
        empirical_coverage = sum(records) / len(records)
        deviation = empirical_coverage - nominal_level
        deviations[key] = deviation
    
    return deviations

def apply_bonferroni_correction(
    p_values: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Dict[str, float]]:
    """
    Apply Bonferroni correction for family-wise error rate.
    
    Args:
        p_values: Dictionary of p-values for each test
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {}
    
    corrected_alpha = alpha / n_tests
    results = {}
    
    for key, p_val in p_values.items():
        corrected_p = min(p_val * n_tests, 1.0)
        results[key] = {
            'original_p': p_val,
            'corrected_p': corrected_p,
            'is_significant': corrected_p < alpha
        }
    
    return results

def is_practically_significant(deviation: float) -> bool:
    """
    Flag if a deviation is "practically significant" based on FR-011.
    
    A deviation is practically significant if |deviation| > 1.0% (0.01).
    
    Args:
        deviation: The deviation from nominal coverage
    
    Returns:
        True if the deviation exceeds the 1.0% threshold
    """
    return abs(deviation) > PRATICAL_SIGNIFICANCE_THRESHOLD

def create_aggregate_report(
    coverage_records: List[Dict[str, Any]],
    population_means: Dict[str, Dict[str, float]],
    nominal_level: float = 0.95,
    alpha: float = 0.05
) -> AggregateReport:
    """
    Create an aggregate report with coverage rates, deviations, and significance tests.
    
    Args:
        coverage_records: List of coverage records from simulation
        population_means: Dictionary of population means for each dataset/variable
        nominal_level: The nominal confidence level
        alpha: Significance level for statistical tests
    
    Returns:
        AggregateReport object with summary statistics
    """
    # Calculate mean deviations
    deviations = calculate_mean_deviation(coverage_records, nominal_level)
    
    # Calculate empirical coverage rates
    coverage_rates = {}
    for key, records in deviations.items():
        # We need to recalculate coverage rate from records
        # Re-group to get coverage rates
        pass
    
    # Re-group records to calculate coverage rates
    groups = {}
    for record in coverage_records:
        key = (
            record['dataset_id'],
            record['sample_size'],
            record['interval_type']
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(record['contains_mean'])
    
    coverage_rates = {}
    for key, records in groups.items():
        empirical_coverage = sum(records) / len(records)
        coverage_rates[key] = empirical_coverage
    
    # Prepare summary data
    summary_data = []
    for key, coverage in coverage_rates.items():
        dataset_id, sample_size, interval_type = key
        deviation = deviations[key]
        is_sig = is_practically_significant(deviation)
        
        summary_data.append({
            'dataset_id': dataset_id,
            'sample_size': sample_size,
            'interval_type': interval_type,
            'nominal_coverage': nominal_level,
            'empirical_coverage': coverage,
            'deviation': deviation,
            'is_practically_significant': is_sig,
            'practical_significance_flag': "YES" if is_sig else "NO"
        })
    
    # Create the report
    report = {
        'nominal_coverage_level': nominal_level,
        'practical_significance_threshold': PRATICAL_SIGNIFICANCE_THRESHOLD,
        'summary': summary_data,
        'total_records_analyzed': len(coverage_records),
        'datasets_analyzed': list(set(r['dataset_id'] for r in coverage_records)),
        'sample_sizes_analyzed': list(set(r['sample_size'] for r in coverage_records)),
        'interval_types_analyzed': list(set(r['interval_type'] for r in coverage_records))
    }
    
    # Validate against schema
    if not validate_aggregate_report(report):
        logger.warning("Aggregate report failed schema validation")
    
    return report

def save_aggregate_report(report: Dict[str, Any], filepath: Optional[str] = None) -> str:
    """Save the aggregate report to a JSON file."""
    if filepath is None:
        filepath = "outputs/aggregate_report.json"
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Aggregate report saved to {filepath}")
    return str(path)

def run_aggregation_workflow(
    coverage_records_path: Optional[str] = None,
    population_means_path: Optional[str] = None,
    output_path: Optional[str] = None,
    nominal_level: float = 0.95,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full aggregation workflow.
    
    Args:
        coverage_records_path: Path to coverage records JSON
        population_means_path: Path to population means JSON
        output_path: Path for output report
        nominal_level: Nominal confidence level
        alpha: Significance level
    
    Returns:
        The generated aggregate report
    """
    logger.info("Starting aggregation workflow")
    
    # Load data
    coverage_records = load_coverage_records(coverage_records_path)
    population_means = load_population_means(population_means_path)
    
    logger.info(f"Loaded {len(coverage_records)} coverage records")
    logger.info(f"Loaded population means for {len(population_means)} datasets")
    
    # Create report
    report = create_aggregate_report(
        coverage_records,
        population_means,
        nominal_level,
        alpha
    )
    
    # Save report
    save_path = save_aggregate_report(report, output_path)
    
    logger.info("Aggregation workflow completed")
    return report

def main():
    """Main entry point for the aggregation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate coverage results")
    parser.add_argument(
        "--coverage-records",
        type=str,
        default="data/processed/coverage_records.json",
        help="Path to coverage records JSON file"
    )
    parser.add_argument(
        "--population-means",
        type=str,
        default="data/processed/population_means.json",
        help="Path to population means JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/aggregate_report.json",
        help="Path for output report"
    )
    parser.add_argument(
        "--nominal-level",
        type=float,
        default=0.95,
        help="Nominal confidence level"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for tests"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_aggregation_workflow(
            coverage_records_path=args.coverage_records,
            population_means_path=args.population_means,
            output_path=args.output,
            nominal_level=args.nominal_level,
            alpha=args.alpha
        )
        
        # Print summary
        print("\n=== Aggregation Summary ===")
        print(f"Nominal Coverage Level: {report['nominal_coverage_level']}")
        print(f"Practical Significance Threshold: {report['practical_significance_threshold']}")
        print(f"Total Records Analyzed: {report['total_records_analyzed']}")
        print(f"Datasets Analyzed: {', '.join(report['datasets_analyzed'])}")
        print(f"Sample Sizes Analyzed: {', '.join(map(str, report['sample_sizes_analyzed']))}")
        
        print("\n--- Practical Significance Flags (|deviation| > 1.0%) ---")
        for item in report['summary']:
            flag = "SIGNIFICANT" if item['is_practically_significant'] else "not significant"
            print(f"{item['dataset_id']} (n={item['sample_size']}, {item['interval_type']}): "
                  f"dev={item['deviation']:.4f} ({flag})")
                
    except Exception as e:
        logger.error(f"Aggregation workflow failed: {e}")
        raise

if __name__ == "__main__":
    main()