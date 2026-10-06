"""
Validation utilities for llmXive data schemas.

Provides dataclasses and validation functions for:
- TokenSequence
- ValidityLabel
- LayerEntropy
- EntropyProfile
"""
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
import logging

# Configure logger
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Dataclasses
# -----------------------------------------------------------------------------

@dataclass
class TokenSequence:
    """Represents a generated token sequence for a single prompt."""
    prompt_id: str
    task_type: str  # 'gsm8k' or 'minigrid'
    tokens: List[str]
    sequence_length: int
    source: str  # e.g., 'gsm8k-train', 'minigrid-train'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenSequence':
        required = ['prompt_id', 'task_type', 'tokens', 'sequence_length', 'source']
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"TokenSequence missing required fields: {missing}")
        return cls(**data)


@dataclass
class ValidityLabel:
    """Binary validity label for a token sequence."""
    prompt_id: str
    token_index: int  # 0-based index within the sequence
    is_valid: bool
    match_type: str  # 'exact_match' or 'path_member' or 'no_match'
    matched_ground_truth_id: Optional[str] = None  # Optional reference to matched GT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidityLabel':
        required = ['prompt_id', 'token_index', 'is_valid', 'match_type']
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"ValidityLabel missing required fields: {missing}")
        return cls(**data)


@dataclass
class LayerEntropy:
    """Entropy value for a specific layer at a specific token position."""
    layer_id: int
    entropy_value: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerEntropy':
        required = ['layer_id', 'entropy_value']
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"LayerEntropy missing required fields: {missing}")
        return cls(**data)


@dataclass
class EntropyProfile:
    """Full entropy profile for a token sequence across all layers."""
    prompt_id: str
    task_type: str
    token_index: int
    sequence_length: int
    layer_entropy_map: Dict[int, float]  # layer_id -> entropy_value

    def to_dict(self) -> Dict[str, Any]:
        # Convert layer_entropy_map to a standard dict for JSON serialization
        return {
            'prompt_id': self.prompt_id,
            'task_type': self.task_type,
            'token_index': self.token_index,
            'sequence_length': self.sequence_length,
            'layer_entropy_map': self.layer_entropy_map
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntropyProfile':
        required = ['prompt_id', 'task_type', 'token_index', 'sequence_length', 'layer_entropy_map']
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"EntropyProfile missing required fields: {missing}")
        
        # Ensure layer_entropy_map values are floats
        layer_map = data['layer_entropy_map']
        if not isinstance(layer_map, dict):
            raise ValueError("layer_entropy_map must be a dict")
        
        # Validate that all values are numeric
        for k, v in layer_map.items():
            if not isinstance(v, (int, float)):
                raise ValueError(f"Entropy value for layer {k} must be numeric, got {type(v)}")
        
        return cls(**data)


# -----------------------------------------------------------------------------
# Validation Functions
# -----------------------------------------------------------------------------

def validate_token_sequence(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a TokenSequence record.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ts = TokenSequence.from_dict(record)
        
        # Additional semantic checks
        if not ts.prompt_id or not isinstance(ts.prompt_id, str):
            return False, "prompt_id must be a non-empty string"
        
        if ts.task_type not in ['gsm8k', 'minigrid']:
            return False, f"task_type must be 'gsm8k' or 'minigrid', got '{ts.task_type}'"
        
        if not isinstance(ts.tokens, list) or len(ts.tokens) == 0:
            return False, "tokens must be a non-empty list"
        
        if ts.sequence_length != len(ts.tokens):
            return False, f"sequence_length ({ts.sequence_length}) must match len(tokens) ({len(ts.tokens)})"
        
        if not ts.source:
            return False, "source must be a non-empty string"
        
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_validity_label(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a ValidityLabel record.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        vl = ValidityLabel.from_dict(record)
        
        if not vl.prompt_id or not isinstance(vl.prompt_id, str):
            return False, "prompt_id must be a non-empty string"
        
        if not isinstance(vl.token_index, int) or vl.token_index < 0:
            return False, "token_index must be a non-negative integer"
        
        if not isinstance(vl.is_valid, bool):
            return False, "is_valid must be a boolean"
        
        if vl.match_type not in ['exact_match', 'path_member', 'no_match']:
            return False, f"match_type must be one of ['exact_match', 'path_member', 'no_match'], got '{vl.match_type}'"
        
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_entropy_profile(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates an EntropyProfile record.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ep = EntropyProfile.from_dict(record)
        
        if not ep.prompt_id or not isinstance(ep.prompt_id, str):
            return False, "prompt_id must be a non-empty string"
        
        if ep.task_type not in ['gsm8k', 'minigrid']:
            return False, f"task_type must be 'gsm8k' or 'minigrid', got '{ep.task_type}'"
        
        if not isinstance(ep.token_index, int) or ep.token_index < 0:
            return False, "token_index must be a non-negative integer"
        
        if not isinstance(ep.sequence_length, int) or ep.sequence_length <= 0:
            return False, "sequence_length must be a positive integer"
        
        if not ep.layer_entropy_map:
            return False, "layer_entropy_map cannot be empty"
        
        # Check that all entropy values are finite numbers
        for layer_id, entropy_val in ep.layer_entropy_map.items():
            if not isinstance(layer_id, int) or layer_id < 0:
                return False, f"layer_id must be a non-negative integer, got {layer_id}"
            
            if not isinstance(entropy_val, (int, float)):
                return False, f"entropy_value for layer {layer_id} must be numeric"
            
            if entropy_val != entropy_val:  # NaN check
                return False, f"entropy_value for layer {layer_id} cannot be NaN"
            
            if abs(entropy_val) == float('inf'):
                return False, f"entropy_value for layer {layer_id} cannot be infinite"
        
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_merged_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a merged record containing TokenSequence, ValidityLabel, and EntropyProfile data.
    
    Expected schema (partial):
    {
        "prompt_id": str,
        "task_type": str,
        "token_index": int,
        "sequence_length": int,
        "tokens": List[str],
        "is_valid": bool,
        "match_type": str,
        "layer_entropy_map": Dict[int, float]
    }
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = [
        'prompt_id', 'task_type', 'token_index', 'sequence_length',
        'tokens', 'is_valid', 'match_type', 'layer_entropy_map'
    ]
    
    missing = [f for f in required_fields if f not in record]
    if missing:
        return False, f"Merged record missing required fields: {missing}"
    
    # Validate basic types
    if not isinstance(record['prompt_id'], str) or not record['prompt_id']:
        return False, "prompt_id must be a non-empty string"
    
    if record['task_type'] not in ['gsm8k', 'minigrid']:
        return False, f"task_type must be 'gsm8k' or 'minigrid', got '{record['task_type']}'"
    
    if not isinstance(record['token_index'], int) or record['token_index'] < 0:
        return False, "token_index must be a non-negative integer"
    
    if not isinstance(record['sequence_length'], int) or record['sequence_length'] <= 0:
        return False, "sequence_length must be a positive integer"
    
    if not isinstance(record['tokens'], list) or len(record['tokens']) == 0:
        return False, "tokens must be a non-empty list"
    
    if record['sequence_length'] != len(record['tokens']):
        return False, f"sequence_length ({record['sequence_length']}) must match len(tokens) ({len(record['tokens'])})"
    
    if not isinstance(record['is_valid'], bool):
        return False, "is_valid must be a boolean"
    
    if record['match_type'] not in ['exact_match', 'path_member', 'no_match']:
        return False, f"match_type must be one of ['exact_match', 'path_member', 'no_match'], got '{record['match_type']}'"
    
    if not isinstance(record['layer_entropy_map'], dict) or not record['layer_entropy_map']:
        return False, "layer_entropy_map must be a non-empty dict"
    
    # Validate entropy values
    for layer_id, entropy_val in record['layer_entropy_map'].items():
        if not isinstance(layer_id, int) or layer_id < 0:
            return False, f"layer_id must be a non-negative integer, got {layer_id}"
        
        if not isinstance(entropy_val, (int, float)):
            return False, f"entropy_value for layer {layer_id} must be numeric"
        
        if entropy_val != entropy_val:  # NaN check
            return False, f"entropy_value for layer {layer_id} cannot be NaN"
        
        if abs(entropy_val) == float('inf'):
            return False, f"entropy_value for layer {layer_id} cannot be infinite"
    
    return True, None


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Simple JSON schema validator for basic type checking.
    
    Args:
        data: The data to validate
        schema: A dict describing the expected schema, e.g.:
                {
                    "type": "object",
                    "required": ["field1", "field2"],
                    "properties": {
                        "field1": {"type": "string"},
                        "field2": {"type": "integer", "minimum": 0}
                    }
                }
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return False, f"Expected object, got {type(data).__name__}"
        
        required = schema.get("required", [])
        missing = [f for f in required if f not in data]
        if missing:
            return False, f"Missing required fields: {missing}"
        
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in data:
                value = data[field_name]
                expected_type = field_schema.get("type")
                
                if expected_type == "string":
                    if not isinstance(value, str):
                        return False, f"Field '{field_name}' must be string, got {type(value).__name__}"
                elif expected_type == "integer":
                    if not isinstance(value, int):
                        return False, f"Field '{field_name}' must be integer, got {type(value).__name__}"
                elif expected_type == "number":
                    if not isinstance(value, (int, float)):
                        return False, f"Field '{field_name}' must be number, got {type(value).__name__}"
                elif expected_type == "boolean":
                    if not isinstance(value, bool):
                        return False, f"Field '{field_name}' must be boolean, got {type(value).__name__}"
                elif expected_type == "array":
                    if not isinstance(value, list):
                        return False, f"Field '{field_name}' must be array, got {type(value).__name__}"
        
        return True, None
    
    return False, "Unsupported schema type"


def load_and_validate_jsonl(
    file_path: Union[str, Path],
    validator_func,
    schema_name: str = "record"
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Loads a JSONL file and validates each record.
    
    Args:
        file_path: Path to the JSONL file
        validator_func: A function that takes a dict and returns (is_valid, error_message)
        schema_name: Name of the schema for error messages
    
    Returns:
        Tuple of (valid_records, error_messages)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    valid_records = []
    error_messages = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                error_messages.append(f"Line {line_num}: Invalid JSON - {e}")
                continue
            
            is_valid, error_msg = validator_func(record)
            if is_valid:
                valid_records.append(record)
            else:
                error_messages.append(f"Line {line_num}: {schema_name} validation failed - {error_msg}")
    
    return valid_records, error_messages