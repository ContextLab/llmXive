from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class SimulationRun:
    dataset_id: str
    sample_size: int
    n_replications: int
    confidence_level: float
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"

@dataclass
class CoverageRecord:
    dataset_id: str
    sample_size: int
    interval_type: str
    interval_lower: float
    interval_upper: float
    contains_mean: bool
    confidence_level: float
    replication_id: int

@dataclass
class AggregateReport:
    dataset_id: str
    sample_size: int
    interval_type: str
    coverage_rate: float
    nominal_rate: float
    deviation: float
    count: int
    timestamp: str

def validate_coverage_record(record: Dict[str, Any]) -> bool:
    """Validate a coverage record dictionary."""
    required_fields = ['dataset_id', 'sample_size', 'interval_type', 
                       'interval_lower', 'interval_upper', 'contains_mean', 'confidence_level']
    return all(field in record for field in required_fields)

def validate_aggregate_report(report: Dict[str, Any]) -> bool:
    """Validate an aggregate report dictionary."""
    required_fields = ['dataset_id', 'sample_size', 'interval_type', 
                       'coverage_rate', 'nominal_rate', 'deviation', 'count']
    return all(field in report for field in required_fields)

def main():
    """Test schemas module."""
    record = {
        'dataset_id': 'wine',
        'sample_size': 10,
        'interval_type': 't',
        'interval_lower': 0.1,
        'interval_upper': 0.9,
        'contains_mean': True,
        'confidence_level': 0.95
    }
    print(f"Valid record: {validate_coverage_record(record)}")

if __name__ == "__main__":
    main()