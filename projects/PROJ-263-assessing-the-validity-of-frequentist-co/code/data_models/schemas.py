"""
Data model schemas for the Monte Carlo simulation pipeline.

Defines TypedDict and dataclass structures for:
- SimulationRun: Metadata for a single simulation execution
- CoverageRecord: Individual interval coverage results
- AggregateReport: Summary statistics across multiple runs/datasets

These schemas ensure data integrity and type safety across the pipeline.
"""

from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationRun(TypedDict, total=False):
    """
    Schema for a single simulation run metadata.
    
    Attributes:
        run_id: Unique identifier for the simulation run
        dataset_id: Identifier for the source dataset
        sample_size: Number of samples drawn (n)
        confidence_level: Nominal confidence level (e.g., 0.95)
        interval_type: Type of interval calculated ('t' or 'bootstrap')
        seed: Random seed used for reproducibility
        start_time: ISO format timestamp of run start
        end_time: ISO format timestamp of run end
        status: Status of the run ('completed', 'failed', 'partial')
        error_message: Optional error details if status is 'failed'
    """
    run_id: str
    dataset_id: str
    sample_size: int
    confidence_level: float
    interval_type: str
    seed: int
    start_time: str
    end_time: str
    status: str
    error_message: Optional[str]

class CoverageRecord(TypedDict, total=False):
    """
    Schema for a single coverage record (one interval check).
    
    Attributes:
        record_id: Unique identifier for the record
        run_id: Reference to the parent simulation run
        dataset_id: Identifier for the source dataset
        variable_name: Name of the variable being analyzed
        sample_size: Sample size used for this interval
        confidence_level: Nominal confidence level
        interval_type: Type of interval ('t' or 'bootstrap')
        interval_lower: Lower bound of the calculated interval
        interval_upper: Upper bound of the calculated interval
        population_mean: The true population mean (full dataset mean)
        contains_mean: Boolean indicating if interval contains the mean
        replication_id: Index of this replication within the run
        timestamp: ISO format timestamp of record creation
    """
    record_id: str
    run_id: str
    dataset_id: str
    variable_name: str
    sample_size: int
    confidence_level: float
    interval_type: str
    interval_lower: float
    interval_upper: float
    population_mean: float
    contains_mean: bool
    replication_id: int
    timestamp: str

class AggregateReport(TypedDict, total=False):
    """
    Schema for an aggregated coverage report.
    
    Attributes:
        report_id: Unique identifier for the report
        generated_at: ISO format timestamp of report generation
        total_runs: Total number of simulation runs included
        total_records: Total number of coverage records included
        datasets: List of dataset identifiers included
        sample_sizes: List of sample sizes included
        confidence_levels: List of confidence levels included
        coverage_rates: Dictionary mapping (dataset, n, type) to coverage rate
        deviation_rates: Dictionary mapping (dataset, n, type) to deviation from nominal
        is_practically_significant: Dictionary indicating practical significance flags
        bonferroni_corrected: Boolean indicating if Bonferroni correction was applied
        p_values: Optional dictionary of p-values for significance tests
        notes: Optional notes about the analysis
        method: Description of the aggregation method used
    """
    report_id: str
    generated_at: str
    total_runs: int
    total_records: int
    datasets: List[str]
    sample_sizes: List[int]
    confidence_levels: List[float]
    coverage_rates: Dict[str, float]
    deviation_rates: Dict[str, float]
    is_practically_significant: Dict[str, bool]
    bonferroni_corrected: bool
    p_values: Optional[Dict[str, float]]
    notes: Optional[str]
    method: str

def validate_coverage_record(record: Dict[str, Any]) -> bool:
    """
    Validate that a dictionary conforms to the CoverageRecord schema.
    
    Args:
        record: Dictionary to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = [
        'record_id', 'run_id', 'dataset_id', 'variable_name',
        'sample_size', 'confidence_level', 'interval_type',
        'interval_lower', 'interval_upper', 'population_mean',
        'contains_mean', 'replication_id', 'timestamp'
    ]
    
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    
    # Type checks
    if not isinstance(record['sample_size'], int):
        raise ValueError("sample_size must be an integer")
    if not isinstance(record['confidence_level'], (int, float)):
        raise ValueError("confidence_level must be a number")
    if not isinstance(record['interval_lower'], (int, float)):
        raise ValueError("interval_lower must be a number")
    if not isinstance(record['interval_upper'], (int, float)):
        raise ValueError("interval_upper must be a number")
    if not isinstance(record['population_mean'], (int, float)):
        raise ValueError("population_mean must be a number")
    if not isinstance(record['contains_mean'], bool):
        raise ValueError("contains_mean must be a boolean")
    if not isinstance(record['replication_id'], int):
        raise ValueError("replication_id must be an integer")
    if record['interval_type'] not in ['t', 'bootstrap']:
        raise ValueError("interval_type must be 't' or 'bootstrap'")
        
    return True

def validate_aggregate_report(report: Dict[str, Any]) -> bool:
    """
    Validate that a dictionary conforms to the AggregateReport schema.
    
    Args:
        report: Dictionary to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = [
        'report_id', 'generated_at', 'total_runs', 'total_records',
        'datasets', 'sample_sizes', 'confidence_levels',
        'coverage_rates', 'deviation_rates', 'is_practically_significant',
        'bonferroni_corrected', 'method'
    ]
    
    for field in required_fields:
        if field not in report:
            raise ValueError(f"Missing required field: {field}")
    
    # Type checks
    if not isinstance(report['total_runs'], int):
        raise ValueError("total_runs must be an integer")
    if not isinstance(report['total_records'], int):
        raise ValueError("total_records must be an integer")
    if not isinstance(report['datasets'], list):
        raise ValueError("datasets must be a list")
    if not isinstance(report['sample_sizes'], list):
        raise ValueError("sample_sizes must be a list")
    if not isinstance(report['confidence_levels'], list):
        raise ValueError("confidence_levels must be a list")
    if not isinstance(report['coverage_rates'], dict):
        raise ValueError("coverage_rates must be a dictionary")
    if not isinstance(report['bonferroni_corrected'], bool):
        raise ValueError("bonferroni_corrected must be a boolean")
        
    return True

def main():
    """
    Main entry point for schema validation tests.
    """
    logger.info("Testing schema definitions...")
    
    # Test CoverageRecord
    test_record: CoverageRecord = {
        'record_id': 'rec-001',
        'run_id': 'run-001',
        'dataset_id': 'wine',
        'variable_name': 'alcohol',
        'sample_size': 10,
        'confidence_level': 0.95,
        'interval_type': 't',
        'interval_lower': 12.5,
        'interval_upper': 13.2,
        'population_mean': 12.8,
        'contains_mean': True,
        'replication_id': 42,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        validate_coverage_record(test_record)
        logger.info("CoverageRecord validation: PASSED")
    except ValueError as e:
        logger.error(f"CoverageRecord validation: FAILED - {e}")
        return False
    
    # Test AggregateReport
    test_report: AggregateReport = {
        'report_id': 'rep-001',
        'generated_at': datetime.now().isoformat(),
        'total_runs': 10,
        'total_records': 1000,
        'datasets': ['wine', 'ionosphere'],
        'sample_sizes': [10, 20, 30],
        'confidence_levels': [0.95],
        'coverage_rates': {'wine-10-t': 0.94},
        'deviation_rates': {'wine-10-t': 0.01},
        'is_practically_significant': {'wine-10-t': False},
        'bonferroni_corrected': False,
        'method': 'simple_aggregation'
    }
    
    try:
        validate_aggregate_report(test_report)
        logger.info("AggregateReport validation: PASSED")
    except ValueError as e:
        logger.error(f"AggregateReport validation: FAILED - {e}")
        return False
    
    logger.info("All schema tests passed.")
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)