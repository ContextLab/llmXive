"""
Data model definitions for the code evaluation pipeline.
Defines dataclasses for CodeSnippet, MetricScore, DatasetGroup, and MetricResult.
Includes validation logic for MetricResult schema compliance.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)

@dataclass
class CodeSnippet:
    """Represents a single code snippet (human-written or LLM-generated)."""
    id: str
    source: str  # 'codesearchnet' or 'codegen'
    code: str
    length: int  # Number of lines or characters
    language: str = "python"
    repository: Optional[str] = None
    original_file: Optional[str] = None
    parsed_successfully: bool = True

@dataclass
class MetricScore:
    """Represents a single metric score for a snippet."""
    snippet_id: str
    metric_type: str  # e.g., 'cyclomatic_complexity', 'maintainability_index', 'pylint_bug_count'
    score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool: str = "radon"  # or 'pylint'

@dataclass
class DatasetGroup:
    """Represents a group of snippets (e.g., Human vs LLM)."""
    label: str  # e.g., 'human', 'llm'
    snippets: List[CodeSnippet] = field(default_factory=list)
    aggregates: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricResult:
    """
    Schema for metric output CSV rows.
    Conforms to the specification for T024.
    Fields:
      - snippet_id: str
      - group: str (human/llm)
      - metric_name: str (e.g., 'cyclomatic_complexity')
      - value: float
      - source_tool: str ('radon' or 'pylint')
      - timestamp: str (ISO format)
    """
    snippet_id: str
    group: str
    metric_name: str
    value: float
    source_tool: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass instance to a dictionary for CSV serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricResult':
        """Creates a MetricResult instance from a dictionary."""
        # Ensure required fields exist
        required_fields = ['snippet_id', 'group', 'metric_name', 'value', 'source_tool']
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Handle timestamp default if missing
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            
        return cls(**data)

def validate_metric_result(result: MetricResult) -> bool:
    """
    Validates that a MetricResult object conforms to the schema.
    Returns True if valid, False otherwise. Logs errors.
    """
    if not isinstance(result, MetricResult):
        logger.error(f"Invalid type: expected MetricResult, got {type(result)}")
        return False

    # Validate field types
    if not isinstance(result.snippet_id, str) or not result.snippet_id:
        logger.error(f"Invalid snippet_id: {result.snippet_id}")
        return False

    if not isinstance(result.group, str) or result.group not in ['human', 'llm']:
        logger.error(f"Invalid group: {result.group}. Must be 'human' or 'llm'")
        return False

    if not isinstance(result.metric_name, str) or not result.metric_name:
        logger.error(f"Invalid metric_name: {result.metric_name}")
        return False

    if not isinstance(result.value, (int, float)):
        logger.error(f"Invalid value type: {type(result.value)}")
        return False

    if not isinstance(result.source_tool, str) or result.source_tool not in ['radon', 'pylint']:
        logger.error(f"Invalid source_tool: {result.source_tool}. Must be 'radon' or 'pylint'")
        return False

    # Validate timestamp format (basic check)
    try:
        datetime.fromisoformat(result.timestamp)
    except ValueError:
        logger.error(f"Invalid timestamp format: {result.timestamp}")
        return False

    return True

def main():
    """
    Entry point for testing the data model schema.
    Runs a quick validation of a sample MetricResult.
    """
    print("Testing MetricResult schema validation...")
    
    sample = MetricResult(
        snippet_id="test-001",
        group="human",
        metric_name="cyclomatic_complexity",
        value=5.0,
        source_tool="radon"
    )
    
    if validate_metric_result(sample):
        print("Validation passed for sample MetricResult.")
        print(f"Serialized: {sample.to_dict()}")
    else:
        print("Validation failed.")
        return 1
    
    # Test invalid group
    invalid_sample = MetricResult(
        snippet_id="test-002",
        group="invalid_group",
        metric_name="test_metric",
        value=1.0,
        source_tool="radon"
    )
    
    if not validate_metric_result(invalid_sample):
        print("Correctly rejected invalid group.")
    else:
        print("ERROR: Should have rejected invalid group.")
        return 1

    print("All schema tests passed.")
    return 0

if __name__ == "__main__":
    exit(main())