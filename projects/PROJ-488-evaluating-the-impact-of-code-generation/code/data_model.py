from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeSnippet:
    """Represents a single code snippet."""
    id: str
    source: str
    code: str
    length: int
    language: str

@dataclass
class MetricScore:
    snippet_id: str
    metric_type: str  # e.g., 'cyclomatic_complexity', 'bug_count'
    score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DatasetGroup:
    """Represents a group of snippets (e.g., Human vs LLM)."""
    label: str
    snippets: List[CodeSnippet] = field(default_factory=list)
    aggregates: Dict[str, float] = field(default_factory=dict)

@dataclass
class MetricResult:
    """
    Schema for metric output conforming to statistical requirements.
    Used for CSV output and validation.
    """
    metric_type: str
    group_label: str
    mean: float
    median: float
    variance: float
    std_dev: float
    min_val: float
    max_val: float
    count: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON/CSV serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricResult':
        """Create MetricResult from dictionary."""
        return cls(**data)

def validate_metric_result(result: MetricResult) -> bool:
    """
    Validates that a MetricResult object conforms to the schema and
    contains logically consistent data.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(result, MetricResult):
        logger.error(f"Validation failed: Input is not a MetricResult instance. Got {type(result)}")
        return False

    # Check required fields are not None
    if result.metric_type is None or result.metric_type == "":
        logger.error("Validation failed: metric_type is missing or empty")
        return False

    if result.group_label is None or result.group_label == "":
        logger.error("Validation failed: group_label is missing or empty")
        return False

    # Check numeric fields
    numeric_fields = ['mean', 'median', 'variance', 'std_dev', 'min_val', 'max_val', 'count']
    for field_name in numeric_fields:
        val = getattr(result, field_name, None)
        if val is None:
            logger.error(f"Validation failed: {field_name} is None")
            return False
        if not isinstance(val, (int, float)):
            logger.error(f"Validation failed: {field_name} is not numeric: {type(val)}")
            return False
        if field_name != 'count' and (val != val):  # Check for NaN
            logger.error(f"Validation failed: {field_name} is NaN")
            return False
        if field_name == 'count' and val < 0:
            logger.error(f"Validation failed: count cannot be negative")
            return False

    # Logical consistency checks
    if result.count == 0 and (result.mean != 0.0 or result.median != 0.0):
        # Allow 0 mean/median if count is 0, but strictly speaking if count is 0 stats are undefined.
        # We'll allow 0 for simplicity in empty cases, but warn if non-zero stats exist for 0 count.
        logger.warning(f"Validation warning: count is 0 but stats are non-zero for {result.metric_type}")

    if result.variance < 0:
        logger.error(f"Validation failed: variance cannot be negative")
        return False

    if result.std_dev < 0:
        logger.error(f"Validation failed: std_dev cannot be negative")
        return False

    if result.min_val > result.max_val:
        logger.error(f"Validation failed: min_val ({result.min_val}) > max_val ({result.max_val})")
        return False

    if not (result.min_val <= result.mean <= result.max_val):
        logger.error(f"Validation failed: mean ({result.mean}) not within [min, max]")
        return False

    if not (result.min_val <= result.median <= result.max_val):
        logger.error(f"Validation failed: median ({result.median}) not within [min, max]")
        return False

    # Verify std_dev * std_dev approx equals variance (with tolerance for float precision)
    if abs(result.std_dev ** 2 - result.variance) > 1e-6:
        logger.warning(f"Validation warning: std_dev^2 ({result.std_dev**2}) does not match variance ({result.variance}) within tolerance")
        # Not a hard fail, just a warning for float precision issues

    return True

def main():
    """Main entry point for testing the data model."""
    logger.info("Running data_model self-test...")
    
    # Create a valid test instance
    test_result = MetricResult(
        metric_type="cyclomatic_complexity",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )

    if validate_metric_result(test_result):
        logger.info("Test passed: Valid MetricResult instance validated successfully.")
    else:
        logger.error("Test failed: Valid MetricResult instance failed validation.")
        return 1

    # Test invalid instance (negative variance)
    bad_result = MetricResult(
        metric_type="test",
        group_label="test",
        mean=1.0,
        median=1.0,
        variance=-1.0,
        std_dev=1.0,
        min_val=0.0,
        max_val=2.0,
        count=10
    )

    if not validate_metric_result(bad_result):
        logger.info("Test passed: Invalid MetricResult correctly rejected.")
    else:
        logger.error("Test failed: Invalid MetricResult was accepted.")
        return 1

    logger.info("All data_model tests passed.")
    return 0

if __name__ == "__main__":
    exit(main())
