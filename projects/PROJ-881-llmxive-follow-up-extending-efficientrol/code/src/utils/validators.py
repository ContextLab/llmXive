"""
Schema validation utilities for llmXive entropy-guided validity prediction.

Provides dataclasses and validation functions for:
- TokenSequence: Raw token generation data
- ValidityLabel: Ground truth matching results
- LayerEntropy: Entropy values per layer
- EntropyProfile: Combined entropy metadata
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

@dataclass
class TokenSequence:
    """Represents a generated token sequence with metadata."""
    prompt_id: str
    token_index: int
    token_id: int
    token_text: str
    sequence_length: int
    task_type: str  # 'gsm8k' or 'minigrid'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenSequence':
        required_fields = ['prompt_id', 'token_index', 'token_id', 'token_text', 'sequence_length', 'task_type']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return cls(**data)

@dataclass
class ValidityLabel:
    """Represents a validity label for a token sequence."""
    prompt_id: str
    token_index: int
    validity: bool
    matched_path: Optional[str] = None  # Ground truth path that matched
    reason: Optional[str] = None  # Explanation for the label
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidityLabel':
        required_fields = ['prompt_id', 'token_index', 'validity']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return cls(**data)

@dataclass
class LayerEntropy:
    """Represents entropy values for a single layer."""
    layer_id: int
    entropy_value: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerEntropy':
        required_fields = ['layer_id', 'entropy_value']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return cls(**data)

@dataclass
class EntropyProfile:
    """Complete entropy profile for a token across all layers."""
    prompt_id: str
    token_index: int
    layer_entropy_map: Dict[int, float]  # layer_id -> entropy_value
    task_type: str
    sequence_length: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'prompt_id': self.prompt_id,
            'token_index': self.token_index,
            'layer_entropy_map': self.layer_entropy_map,
            'task_type': self.task_type,
            'sequence_length': self.sequence_length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntropyProfile':
        required_fields = ['prompt_id', 'token_index', 'layer_entropy_map', 'task_type', 'sequence_length']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate layer_entropy_map structure
        if not isinstance(data['layer_entropy_map'], dict):
            raise ValueError("layer_entropy_map must be a dictionary")
        
        for layer_id, entropy_val in data['layer_entropy_map'].items():
            if not isinstance(layer_id, int):
                raise ValueError(f"layer_id must be int, got {type(layer_id)}")
            if not isinstance(entropy_val, (int, float)):
                raise ValueError(f"entropy_value must be numeric, got {type(entropy_val)}")
            if entropy_val is None or (isinstance(entropy_val, float) and (entropy_val != entropy_val)):  # NaN check
                raise ValueError(f"entropy_value cannot be None or NaN at layer {layer_id}")
        
        return cls(**data)

def validate_token_sequence(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a TokenSequence record.
    
    Args:
        record: Dictionary containing token sequence data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'token_id', 'token_text', 'sequence_length', 'task_type']
        
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
        
        # Type checks
        if not isinstance(record['prompt_id'], str):
            return False, "prompt_id must be a string"
        if not isinstance(record['token_index'], int):
            return False, "token_index must be an integer"
        if not isinstance(record['token_id'], int):
            return False, "token_id must be an integer"
        if not isinstance(record['token_text'], str):
            return False, "token_text must be a string"
        if not isinstance(record['sequence_length'], int):
            return False, "sequence_length must be an integer"
        if record['task_type'] not in ['gsm8k', 'minigrid']:
            return False, "task_type must be 'gsm8k' or 'minigrid'"
        
        # Value constraints
        if record['token_index'] < 0:
            return False, "token_index must be non-negative"
        if record['sequence_length'] <= 0:
            return False, "sequence_length must be positive"
        
        # Try to instantiate the dataclass
        TokenSequence.from_dict(record)
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def validate_validity_label(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a ValidityLabel record.
    
    Args:
        record: Dictionary containing validity label data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'validity']
        
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
        
        # Type checks
        if not isinstance(record['prompt_id'], str):
            return False, "prompt_id must be a string"
        if not isinstance(record['token_index'], int):
            return False, "token_index must be an integer"
        if not isinstance(record['validity'], bool):
            return False, "validity must be a boolean"
        
        # Value constraints
        if record['token_index'] < 0:
            return False, "token_index must be non-negative"
        
        # Try to instantiate the dataclass
        ValidityLabel.from_dict(record)
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def validate_entropy_profile(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate an EntropyProfile record.
    
    Args:
        record: Dictionary containing entropy profile data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'layer_entropy_map', 'task_type', 'sequence_length']
        
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
        
        # Type checks
        if not isinstance(record['prompt_id'], str):
            return False, "prompt_id must be a string"
        if not isinstance(record['token_index'], int):
            return False, "token_index must be an integer"
        if not isinstance(record['layer_entropy_map'], dict):
            return False, "layer_entropy_map must be a dictionary"
        if record['task_type'] not in ['gsm8k', 'minigrid']:
            return False, "task_type must be 'gsm8k' or 'minigrid'"
        if not isinstance(record['sequence_length'], int):
            return False, "sequence_length must be an integer"
        
        # Value constraints
        if record['token_index'] < 0:
            return False, "token_index must be non-negative"
        if record['sequence_length'] <= 0:
            return False, "sequence_length must be positive"
        if len(record['layer_entropy_map']) == 0:
            return False, "layer_entropy_map cannot be empty"
        
        # Validate each layer entry
        for layer_id, entropy_val in record['layer_entropy_map'].items():
            if not isinstance(layer_id, int):
                return False, f"layer_id must be int, got {type(layer_id)}"
            if entropy_val is None:
                return False, f"entropy_value cannot be None at layer {layer_id}"
            if isinstance(entropy_val, float) and (entropy_val != entropy_val):  # NaN check
                return False, f"entropy_value cannot be NaN at layer {layer_id}"
            if entropy_val < 0:
                return False, f"entropy_value cannot be negative at layer {layer_id}"
        
        # Try to instantiate the dataclass
        EntropyProfile.from_dict(record)
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def validate_merged_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a merged record containing both sequence and profile data.
    
    Args:
        record: Dictionary containing merged data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check for required fields from both TokenSequence and EntropyProfile
        required_fields = [
            'prompt_id', 'token_index', 'token_id', 'token_text', 
            'sequence_length', 'task_type', 'layer_entropy_map', 'validity'
        ]
        
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
        
        # Validate as TokenSequence
        is_valid_seq, error_seq = validate_token_sequence(record)
        if not is_valid_seq:
            return False, f"TokenSequence validation failed: {error_seq}"
        
        # Validate as EntropyProfile (subset of fields)
        profile_fields = {
            'prompt_id': record['prompt_id'],
            'token_index': record['token_index'],
            'layer_entropy_map': record['layer_entropy_map'],
            'task_type': record['task_type'],
            'sequence_length': record['sequence_length']
        }
        is_valid_profile, error_profile = validate_entropy_profile(profile_fields)
        if not is_valid_profile:
            return False, f"EntropyProfile validation failed: {error_profile}"
        
        # Validate validity label
        validity_fields = {
            'prompt_id': record['prompt_id'],
            'token_index': record['token_index'],
            'validity': record['validity']
        }
        is_valid_label, error_label = validate_validity_label(validity_fields)
        if not is_valid_label:
            return False, f"ValidityLabel validation failed: {error_label}"
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def validate_json_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a record against a JSON schema definition.
    
    Args:
        record: Dictionary to validate
        schema: Schema definition with 'required' and 'properties' keys
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        # Check required fields
        for field in required:
            if field not in record:
                return False, f"Missing required field: {field}"
        
        # Check field types
        for field, value in record.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type:
                    type_map = {
                        'string': str,
                        'integer': int,
                        'number': (int, float),
                        'boolean': bool,
                        'array': list,
                        'object': dict
                    }
                    expected_python_type = type_map.get(expected_type)
                    if expected_python_type and not isinstance(value, expected_python_type):
                        return False, f"Field '{field}' should be {expected_type}, got {type(value).__name__}"
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def load_and_validate_jsonl(file_path: Union[str, Path], validator_func) -> List[Dict[str, Any]]:
    """
    Load and validate a JSONL file using a specific validator function.
    
    Args:
        file_path: Path to the JSONL file
        validator_func: Function that takes a record and returns (is_valid, error)
        
    Returns:
        List of valid records
        
    Raises:
        ValueError: If validation fails for any record
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    records = []
    errors = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                is_valid, error = validator_func(record)
                
                if is_valid:
                    records.append(record)
                else:
                    error_msg = f"Line {line_num}: {error}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            except json.JSONDecodeError as e:
                error_msg = f"Line {line_num}: Invalid JSON - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
    
    if errors:
        raise ValueError(f"Validation failed for {len(errors)} records:\n" + "\n".join(errors[:10]))
    
    logger.info(f"Successfully validated {len(records)} records from {file_path}")
    return records