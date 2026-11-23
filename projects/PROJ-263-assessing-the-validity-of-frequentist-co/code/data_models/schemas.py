from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import logging

# Configure logging for schema validation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SimulationRun:
    """
    Schema for a single Monte Carlo simulation run configuration and metadata.
    Corresponds to the operational parameters of one simulation execution.
    """
    run_id: str
    dataset_id: str
    variable_name: str
    sample_size: int
    confidence_level: float
    n_replications: int
    method: str  # 't_interval' or 'bootstrap_percentile'
    seed: int
    timestamp: str
    start_time: float
    end_time: float
    status: str  # 'success', 'failed', 'skipped'
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRun':
        return cls(**data)

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Basic validation of required fields."""
        required_fields = ['run_id', 'dataset_id', 'variable_name', 'sample_size',
                         'confidence_level', 'n_replications', 'method', 'seed',
                         'timestamp', 'status']
        for field_name in required_fields:
            if field_name not in data:
                logger.error(f"Missing required field: {field_name}")
                return False
        
        # Type checks
        if not isinstance(data['sample_size'], int) or data['sample_size'] <= 0:
            logger.error(f"Invalid sample_size: {data['sample_size']}")
            return False
        
        if not isinstance(data['confidence_level'], (int, float)) or not (0 < data['confidence_level'] < 1):
            logger.error(f"Invalid confidence_level: {data['confidence_level']}")
            return False
        
        if data['method'] not in ['t_interval', 'bootstrap_percentile']:
            logger.error(f"Invalid method: {data['method']}")
            return False
        
        return True

@dataclass
class CoverageRecord:
    """
    Schema for a single coverage record generated during simulation.
    Stores the interval bounds and whether they contained the population mean.
    """
    dataset_id: str
    variable_name: str
    sample_size: int
    confidence_level: float
    method: str
    iteration: int
    interval_lower: float
    interval_upper: float
    population_mean: float
    contains_mean: bool
    run_id: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoverageRecord':
        return cls(**data)

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Basic validation of required fields."""
        required_fields = ['dataset_id', 'variable_name', 'sample_size', 'confidence_level',
                         'method', 'iteration', 'interval_lower', 'interval_upper',
                         'population_mean', 'contains_mean', 'run_id', 'timestamp']
        for field_name in required_fields:
            if field_name not in data:
                logger.error(f"Missing required field in CoverageRecord: {field_name}")
                return False
        
        # Type checks
        if not isinstance(data['contains_mean'], bool):
            logger.error(f"Invalid contains_mean type: {type(data['contains_mean'])}")
            return False
        
        if not isinstance(data['iteration'], int) or data['iteration'] < 0:
            logger.error(f"Invalid iteration: {data['iteration']}")
            return False
        
        return True

@dataclass
class AggregateReport:
    """
    Schema for the aggregated report containing summary statistics across
    multiple datasets, sample sizes, and methods.
    """
    report_id: str
    generated_at: str
    nominal_coverage: float
    datasets_analyzed: List[str]
    sample_sizes_analyzed: List[int]
    methods_analyzed: List[str]
    results: List[Dict[str, Any]]  # List of aggregated results per configuration
    statistical_tests: Dict[str, Any]  # Bonferroni corrected p-values, etc.
    conclusion: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AggregateReport':
        return cls(**data)

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Basic validation of required fields."""
        required_fields = ['report_id', 'generated_at', 'nominal_coverage',
                         'datasets_analyzed', 'sample_sizes_analyzed',
                         'methods_analyzed', 'results', 'statistical_tests', 'conclusion']
        for field_name in required_fields:
            if field_name not in data:
                logger.error(f"Missing required field in AggregateReport: {field_name}")
                return False
        
        # Type checks
        if not isinstance(data['datasets_analyzed'], list):
            logger.error("datasets_analyzed must be a list")
            return False
        
        if not isinstance(data['results'], list):
            logger.error("results must be a list")
            return False
        
        return True

def validate_coverage_record(data: Dict[str, Any]) -> bool:
    """Convenience function to validate a CoverageRecord dictionary."""
    return CoverageRecord.validate(data)

def validate_aggregate_report(data: Dict[str, Any]) -> bool:
    """Convenience function to validate an AggregateReport dictionary."""
    return AggregateReport.validate(data)

def main():
    """
    Main entry point for schema validation tests.
    Runs basic validation on example data to ensure schemas work correctly.
    """
    logger.info("Testing schema definitions...")

    # Test SimulationRun
    sim_run_data = {
        "run_id": "test-001",
        "dataset_id": "wine",
        "variable_name": "alcohol",
        "sample_size": 10,
        "confidence_level": 0.95,
        "n_replications": 1000,
        "method": "t_interval",
        "seed": 42,
        "timestamp": datetime.now().isoformat(),
        "start_time": 0.0,
        "end_time": 1.5,
        "status": "success"
    }

    if SimulationRun.validate(sim_run_data):
        logger.info("SimulationRun validation passed")
        run = SimulationRun.from_dict(sim_run_data)
        logger.info(f"Created SimulationRun: {run.run_id}")
    else:
        logger.error("SimulationRun validation failed")

    # Test CoverageRecord
    coverage_data = {
        "dataset_id": "wine",
        "variable_name": "alcohol",
        "sample_size": 10,
        "confidence_level": 0.95,
        "method": "t_interval",
        "iteration": 1,
        "interval_lower": 10.5,
        "interval_upper": 13.2,
        "population_mean": 12.8,
        "contains_mean": True,
        "run_id": "test-001",
        "timestamp": datetime.now().isoformat()
    }

    if CoverageRecord.validate(coverage_data):
        logger.info("CoverageRecord validation passed")
        record = CoverageRecord.from_dict(coverage_data)
        logger.info(f"Created CoverageRecord: {record.dataset_id} - {record.variable_name}")
    else:
        logger.error("CoverageRecord validation failed")

    # Test AggregateReport
    aggregate_data = {
        "report_id": "report-001",
        "generated_at": datetime.now().isoformat(),
        "nominal_coverage": 0.95,
        "datasets_analyzed": ["wine", "ionosphere"],
        "sample_sizes_analyzed": [10, 20, 30],
        "methods_analyzed": ["t_interval", "bootstrap_percentile"],
        "results": [
            {
                "dataset_id": "wine",
                "sample_size": 10,
                "method": "t_interval",
                "empirical_coverage": 0.94,
                "deviation": -0.01
            }
        ],
        "statistical_tests": {
            "bonferroni_p_value": 0.05,
            "significant": False
        },
        "conclusion": "T-intervals show acceptable coverage for n=30."
    }

    if AggregateReport.validate(aggregate_data):
        logger.info("AggregateReport validation passed")
        report = AggregateReport.from_dict(aggregate_data)
        logger.info(f"Created AggregateReport: {report.report_id}")
    else:
        logger.error("AggregateReport validation failed")

    logger.info("Schema tests completed.")

if __name__ == "__main__":
    main()