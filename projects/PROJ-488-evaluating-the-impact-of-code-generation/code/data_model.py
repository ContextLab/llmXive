"""
Data Model Definitions.
Defines schemas for Code Snippets, Metric Scores, and Results.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
from pathlib import Path

@dataclass
class CodeSnippet:
    id: str
    source: str
    code: str
    length: int
    language: str

@dataclass
class MetricScore:
    snippet_id: str
    metric_type: str
    score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DatasetGroup:
    label: str
    snippets: List[CodeSnippet] = field(default_factory=list)
    aggregates: Dict[str, float] = field(default_factory=dict)

@dataclass
class MetricResult:
    snippet_id: str
    source: str
    metric_type: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

def validate_metric_result(data: Dict[str, Any]) -> bool:
    """
    Validate a dictionary against the MetricResult schema.
    Returns True if valid, False otherwise.
    """
    logger = logging.getLogger("data_model")
    required_fields = ["snippet_id", "source", "metric_type", "value"]
    
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False
            
    if not isinstance(data["snippet_id"], str):
        logger.error("snippet_id must be a string")
        return False
        
    if not isinstance(data["source"], str):
        logger.error("source must be a string")
        return False
        
    if not isinstance(data["metric_type"], str):
        logger.error("metric_type must be a string")
        return False
        
    if not isinstance(data["value"], (int, float)):
        logger.error("value must be a number")
        return False
        
    return True

def main():
    """Example usage."""
    logger = logging.getLogger("data_model")
    logger.info("Data model loaded.")
    
    # Test validation
    valid_data = {
        "snippet_id": "123",
        "source": "test",
        "metric_type": "cc",
        "value": 5.0
    }
    print(f"Validation test: {validate_metric_result(valid_data)}")

if __name__ == "__main__":
    main()