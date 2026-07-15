"""
Data Contracts Module

Defines and validates data schemas for the pipeline.
These contracts ensure that data flowing between stages
conforms to expected structures.

Contracts:
- CodeSnippetContract: Validates code snippet data structure
- MetricScoreContract: Validates metric score records
- DatasetGroupContract: Validates dataset groupings
- MetricResultContract: Validates metric result outputs
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from ..data_model import CodeSnippet, MetricScore, DatasetGroup, MetricResult
from ..logging_config import get_logger

logger = get_logger(__name__)


class CodeSnippetContract:
    """
    Contract for CodeSnippet data structure.
    
    Expected fields:
    - id: str (unique identifier)
    - source: str (dataset source name)
    - code: str (actual code content)
    - length: int (character or line count)
    - language: str (programming language)
    """
    
    REQUIRED_FIELDS = ['id', 'source', 'code', 'length', 'language']
    FIELD_TYPES = {
        'id': str,
        'source': str,
        'code': str,
        'length': int,
        'language': str
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validate a CodeSnippet dictionary against the contract."""
        missing = [f for f in cls.REQUIRED_FIELDS if f not in data]
        if missing:
            logger.error(f"CodeSnippet missing required fields: {missing}")
            return False
        
        for field, expected_type in cls.FIELD_TYPES.items():
            if not isinstance(data[field], expected_type):
                logger.error(f"CodeSnippet field '{field}' has wrong type: "
                             f"expected {expected_type}, got {type(data[field])}")
                return False
        
        return True
    
    @classmethod
    def from_model(cls, model: CodeSnippet) -> Dict[str, Any]:
        """Convert a CodeSnippet dataclass to dictionary."""
        return asdict(model)


class MetricScoreContract:
    """
    Contract for MetricScore data structure.
    
    Expected fields:
    - snippet_id: str (reference to code snippet)
    - metric_type: str (type of metric, e.g., 'cyclomatic_complexity')
    - score: float (numeric score value)
    - timestamp: str (ISO format timestamp)
    """
    
    REQUIRED_FIELDS = ['snippet_id', 'metric_type', 'score', 'timestamp']
    FIELD_TYPES = {
        'snippet_id': str,
        'metric_type': str,
        'score': (int, float),
        'timestamp': str
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validate a MetricScore dictionary against the contract."""
        missing = [f for f in cls.REQUIRED_FIELDS if f not in data]
        if missing:
            logger.error(f"MetricScore missing required fields: {missing}")
            return False
        
        for field, expected_type in cls.FIELD_TYPES.items():
            if not isinstance(data[field], expected_type):
                logger.error(f"MetricScore field '{field}' has wrong type: "
                             f"expected {expected_type}, got {type(data[field])}")
                return False
        
        # Additional validation: score must be non-negative
        if data['score'] < 0:
            logger.error(f"MetricScore '{field}' has negative value: {data['score']}")
            return False
        
        return True
    
    @classmethod
    def from_model(cls, model: MetricScore) -> Dict[str, Any]:
        """Convert a MetricScore dataclass to dictionary."""
        return asdict(model)


class DatasetGroupContract:
    """
    Contract for DatasetGroup data structure.
    
    Expected fields:
    - label: str (group identifier, e.g., 'human', 'llm-generated')
    - snippets: List[Dict] (list of code snippets)
    - aggregates: Dict (aggregated statistics)
    """
    
    REQUIRED_FIELDS = ['label', 'snippets', 'aggregates']
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validate a DatasetGroup dictionary against the contract."""
        missing = [f for f in cls.REQUIRED_FIELDS if f not in data]
        if missing:
            logger.error(f"DatasetGroup missing required fields: {missing}")
            return False
        
        if not isinstance(data['snippets'], list):
            logger.error("DatasetGroup 'snippets' must be a list")
            return False
        
        if not isinstance(data['aggregates'], dict):
            logger.error("DatasetGroup 'aggregates' must be a dict")
            return False
        
        # Validate each snippet
        for i, snippet in enumerate(data['snippets']):
            if not CodeSnippetContract.validate(snippet):
                logger.error(f"DatasetGroup snippet at index {i} failed validation")
                return False
        
        return True
    
    @classmethod
    def from_model(cls, model: DatasetGroup) -> Dict[str, Any]:
        """Convert a DatasetGroup dataclass to dictionary."""
        return asdict(model)


class MetricResultContract:
    """
    Contract for MetricResult data structure (CSV output schema).
    
    Expected fields:
    - metric_name: str (name of the metric)
    - group_label: str (human or llm-generated)
    - count: int (number of samples)
    - mean: float
    - median: float
    - std: float
    - min: float
    - max: float
    """
    
    REQUIRED_FIELDS = ['metric_name', 'group_label', 'count', 'mean', 'median', 'std', 'min', 'max']
    FIELD_TYPES = {
        'metric_name': str,
        'group_label': str,
        'count': int,
        'mean': (int, float),
        'median': (int, float),
        'std': (int, float),
        'min': (int, float),
        'max': (int, float)
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validate a MetricResult dictionary against the contract."""
        missing = [f for f in cls.REQUIRED_FIELDS if f not in data]
        if missing:
            logger.error(f"MetricResult missing required fields: {missing}")
            return False
        
        for field, expected_type in cls.FIELD_TYPES.items():
            if not isinstance(data[field], expected_type):
                logger.error(f"MetricResult field '{field}' has wrong type: "
                             f"expected {expected_type}, got {type(data[field])}")
                return False
        
        # Additional validation: count must be positive
        if data['count'] <= 0:
            logger.error(f"MetricResult 'count' must be positive: {data['count']}")
            return False
        
        return True
    
    @classmethod
    def from_model(cls, model: MetricResult) -> Dict[str, Any]:
        """Convert a MetricResult dataclass to dictionary."""
        return asdict(model)


def validate_data_contract(data_type: str, data: Dict[str, Any]) -> bool:
    """
    Generic data contract validator.
    
    Args:
        data_type: Type of data to validate ('code_snippet', 'metric_score', 
                   'dataset_group', 'metric_result')
        data: The data dictionary to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    contracts = {
        'code_snippet': CodeSnippetContract,
        'metric_score': MetricScoreContract,
        'dataset_group': DatasetGroupContract,
        'metric_result': MetricResultContract
    }
    
    if data_type not in contracts:
        logger.error(f"Unknown data type for validation: {data_type}")
        return False
    
    return contracts[data_type].validate(data)
