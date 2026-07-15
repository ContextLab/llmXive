"""
Data Contracts: Definitions and validators for input/output schemas.

These contracts enforce the structure of data moving between pipeline stages,
ensuring compatibility with the `code/data_model.py` definitions.
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..data_model import CodeSnippet, MetricScore, DatasetGroup, MetricResult
from ..logging_config import get_logger

logger = get_logger("contracts.data")

class CodeSnippetContract:
    """Contract for CodeSnippet input data."""
    
    REQUIRED_FIELDS = {'id', 'source', 'code', 'length', 'language'}
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validates that a dictionary matches the CodeSnippet schema."""
        if not isinstance(data, dict):
            logger.error(f"CodeSnippetContract: Expected dict, got {type(data)}")
            return False
        
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            logger.error(f"CodeSnippetContract: Missing fields {missing}")
            return False
        
        if not isinstance(data.get('code'), str):
            logger.error("CodeSnippetContract: 'code' must be a string")
            return False
        
        if not isinstance(data.get('id'), str):
            logger.error("CodeSnippetContract: 'id' must be a string")
            return False
            
        logger.debug("CodeSnippetContract: Validation passed")
        return True
        
    @classmethod
    def to_json(cls, obj: CodeSnippet) -> str:
        """Serializes a CodeSnippet object to JSON string."""
        return json.dumps(asdict(obj))
        
    @classmethod
    def from_json(cls, json_str: str) -> CodeSnippet:
        """Deserializes a JSON string to a CodeSnippet object."""
        data = json.loads(json_str)
        if not cls.validate(data):
            raise ValueError("Invalid CodeSnippet data")
        return CodeSnippet(**data)

class MetricScoreContract:
    """Contract for MetricScore data."""
    
    REQUIRED_FIELDS = {'snippet_id', 'metric_type', 'score', 'timestamp'}
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            logger.error(f"MetricScoreContract: Missing fields {missing}")
            return False
        
        if not isinstance(data.get('score'), (int, float)):
            logger.error("MetricScoreContract: 'score' must be numeric")
            return False
            
        return True

class DatasetGroupContract:
    """Contract for DatasetGroup data."""
    
    REQUIRED_FIELDS = {'label', 'snippets', 'aggregates'}
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            logger.error(f"DatasetGroupContract: Missing fields {missing}")
            return False
        
        if not isinstance(data.get('snippets'), list):
            logger.error("DatasetGroupContract: 'snippets' must be a list")
            return False
            
        return True

class MetricResultContract:
    """Contract for CSV output schema (MetricResult)."""
    
    REQUIRED_COLUMNS = ['snippet_id', 'metric_type', 'score', 'timestamp', 'group_label']
    
    @classmethod
    def validate_csv_header(cls, headers: List[str]) -> bool:
        """Validates that a CSV header contains all required columns."""
        missing = set(cls.REQUIRED_COLUMNS) - set(headers)
        if missing:
            logger.error(f"MetricResultContract: Missing CSV columns {missing}")
            return False
        return True
        
    @classmethod
    def validate_row(cls, row: Dict[str, Any]) -> bool:
        """Validates a single row dictionary."""
        return cls.validate_csv_header(list(row.keys()))
