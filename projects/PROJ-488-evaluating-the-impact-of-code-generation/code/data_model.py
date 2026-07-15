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
    aggregates: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricResult:
    metric_name: str
    human_mean: float
    human_median: float
    human_variance: float
    llm_mean: float
    llm_median: float
    llm_variance: float
    p_value: float
    effect_size: float
    significant: bool

def validate_metric_result(result: MetricResult) -> bool:
    """
    Validates a MetricResult object.
    
    Args:
        result: MetricResult object.
        
    Returns:
        True if valid, False otherwise.
    """
    if result.human_mean is None or result.llm_mean is None:
        return False
    if result.p_value is None or result.effect_size is None:
        return False
    return True

def main():
    """
    Main entry point for data model.
    """
    snippet = CodeSnippet(id="1", source="test", code="x=1", length=3, language="python")
    print(f"Snippet: {snippet}")

if __name__ == "__main__":
    main()
