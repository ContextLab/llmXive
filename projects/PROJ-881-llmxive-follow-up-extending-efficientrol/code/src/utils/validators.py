"""
Schema validation utilities for llmXive pipeline.

Provides dataclasses and validation functions for:
- TokenSequence: Raw generated token sequences
- ValidityLabel: Binary validity labels against ground truth
- LayerEntropy: Entropy values per layer for a token
- EntropyProfile: Combined entropy profile across layers
"""
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
import logging

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class TokenSequence:
    """Represents a generated token sequence."""
    prompt_id: str
    tokens: List[str]
    task_type: str  # 'gsm8k' or 'minigrid'
    sequence_length: int
    
    def __post_init__(self):
        if not isinstance(self.prompt_id, str) or not self.prompt_id:
            raise ValueError("prompt_id must be a non-empty string")
        if not isinstance(self.tokens, list):
            raise TypeError("tokens must be a list of strings")
        if not all(isinstance(t, str) for t in self.tokens):
            raise TypeError("All tokens must be strings")
        if self.task_type not in ['gsm8k', 'minigrid']:
            raise ValueError("task_type must be 'gsm8k' or 'minigrid'")
        if self.sequence_length != len(self.tokens):
            raise ValueError("sequence_length must match len(tokens)")

@dataclass
class ValidityLabel:
    """Binary validity label for a token sequence."""
    prompt_id: str
    token_index: int
    validity: bool  # True if valid, False otherwise
    match_details: Optional[str] = None  # Optional explanation of match/mismatch
    
    def __post_init__(self):
        if not isinstance(self.prompt_id, str) or not self.prompt_id:
            raise ValueError("prompt_id must be a non-empty string")
        if not isinstance(self.token_index, int) or self.token_index < 0:
            raise ValueError("token_index must be a non-negative integer")
        if not isinstance(self.validity, bool):
            raise TypeError("validity must be a boolean")

@dataclass
class LayerEntropy:
    """Entropy value for a specific layer."""
    layer_id: int
    entropy_value: float
    
    def __post_init__(self):
        if not isinstance(self.layer_id, int) or self.layer_id < 0:
            raise ValueError("layer_id must be a non-negative integer")
        if not isinstance(self.entropy_value, (int, float)):
            raise TypeError("entropy_value must be a number")
        if self.entropy_value < 0:
            raise ValueError("entropy_value must be non-negative")

@dataclass
class EntropyProfile:
    """Combined entropy profile across all layers for a token position."""
    prompt_id: str
    token_index: str  # Stored as string for JSON compatibility in some contexts
    sequence_length: int
    task_type: str
    layer_entropy_map: Dict[int, float]  # layer_id -> entropy_value
    
    def __post_init__(self):
        if not isinstance(self.prompt_id, str) or not self.prompt_id:
            raise ValueError("prompt_id must be a non-empty string")
        if not isinstance(self.token_index, int) or self.token_index < 0:
            raise ValueError("token_index must be a non-negative integer")
        if not isinstance(self.sequence_length, int) or self.sequence_length <= 0:
            raise ValueError("sequence_length must be a positive integer")
        if self.task_type not in ['gsm8k', 'minigrid']:
            raise ValueError("task_type must be 'gsm8k' or 'minigrid'")
        if not isinstance(self.layer_entropy_map, dict):
            raise TypeError("layer_entropy_map must be a dictionary")
        for layer_id, entropy_val in self.layer_entropy_map.items():
            if not isinstance(layer_id, int) or layer_id < 0:
                raise ValueError(f"layer_id {layer_id} must be a non-negative integer")
            if not isinstance(entropy_val, (int, float)):
                raise TypeError(f"entropy_value for layer {layer_id} must be a number")
            if entropy_val < 0:
                raise ValueError(f"entropy_value for layer {layer_id} must be non-negative")

def validate_token_sequence(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a dictionary against TokenSchema.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'tokens', 'task_type', 'sequence_length']
        for field_name in required_fields:
            if field_name not in data:
                return False, f"Missing required field: {field_name}"
        
        # Type checks
        if not isinstance(data['prompt_id'], str) or not data['prompt_id']:
            return False, "prompt_id must be a non-empty string"
        
        if not isinstance(data['tokens'], list):
            return False, "tokens must be a list"
        
        if not all(isinstance(t, str) for t in data['tokens']):
            return False, "All tokens must be strings"
        
        if data['task_type'] not in ['gsm8k', 'minigrid']:
            return False, "task_type must be 'gsm8k' or 'minigrid'"
        
        if not isinstance(data['sequence_length'], int) or data['sequence_length'] <= 0:
            return False, "sequence_length must be a positive integer"
        
        if data['sequence_length'] != len(data['tokens']):
            return False, "sequence_length must match len(tokens)"
        
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_validity_label(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a dictionary against ValidityLabel schema.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'validity']
        for field_name in required_fields:
            if field_name not in data:
                return False, f"Missing required field: {field_name}"
        
        # Type checks
        if not isinstance(data['prompt_id'], str) or not data['prompt_id']:
            return False, "prompt_id must be a non-empty string"
        
        if not isinstance(data['token_index'], int) or data['token_index'] < 0:
            return False, "token_index must be a non-negative integer"
        
        if not isinstance(data['validity'], bool):
            return False, "validity must be a boolean"
        
        # Optional field check
        if 'match_details' in data and data['match_details'] is not None:
            if not isinstance(data['match_details'], str):
                return False, "match_details must be a string or None"
        
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_entropy_profile(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a dictionary against EntropyProfile schema.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'sequence_length', 'task_type', 'layer_entropy_map']
        for field_name in required_fields:
            if field_name not in data:
                return False, f"Missing required field: {field_name}"
        
        # Type checks
        if not isinstance(data['prompt_id'], str) or not data['prompt_id']:
            return False, "prompt_id must be a non-empty string"
        
        if not isinstance(data['token_index'], int) or data['token_index'] < 0:
            return False, "token_index must be a non-negative integer"
        
        if not isinstance(data['sequence_length'], int) or data['sequence_length'] <= 0:
            return False, "sequence_length must be a positive integer"
        
        if data['task_type'] not in ['gsm8k', 'minigrid']:
            return False, "task_type must be 'gsm8k' or 'minigrid'"
        
        if not isinstance(data['layer_entropy_map'], dict):
            return False, "layer_entropy_map must be a dictionary"
        
        if len(data['layer_entropy_map']) == 0:
            return False, "layer_entropy_map cannot be empty"
        
        # Validate layer_entropy_map contents
        for layer_id, entropy_val in data['layer_entropy_map'].items():
            if not isinstance(layer_id, int) or layer_id < 0:
                return False, f"layer_id {layer_id} must be a non-negative integer"
            if not isinstance(entropy_val, (int, float)):
                return False, f"entropy_value for layer {layer_id} must be a number"
            if entropy_val < 0:
                return False, f"entropy_value for layer {layer_id} must be non-negative"
            # Check for None values (explicit requirement)
            if entropy_val is None:
                return False, f"entropy_value for layer {layer_id} cannot be None"
        
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_merged_record(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a merged record containing both generation and validity/entropy data.
    
    Expected schema:
    {
        "prompt_id": str,
        "token_index": int,
        "tokens": List[str],
        "task_type": str,
        "sequence_length": int,
        "validity": bool,
        "layer_entropy_map": Dict[int, float]
    }
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        required_fields = ['prompt_id', 'token_index', 'tokens', 'task_type', 'sequence_length', 'validity', 'layer_entropy_map']
        for field_name in required_fields:
            if field_name not in data:
                return False, f"Missing required field: {field_name}"
        
        # Basic type checks
        if not isinstance(data['prompt_id'], str) or not data['prompt_id']:
            return False, "prompt_id must be a non-empty string"
        
        if not isinstance(data['token_index'], int) or data['token_index'] < 0:
            return False, "token_index must be a non-negative integer"
        
        if not isinstance(data['tokens'], list) or not all(isinstance(t, str) for t in data['tokens']):
            return False, "tokens must be a list of strings"
        
        if data['task_type'] not in ['gsm8k', 'minigrid']:
            return False, "task_type must be 'gsm8k' or 'minigrid'"
        
        if not isinstance(data['sequence_length'], int) or data['sequence_length'] <= 0:
            return False, "sequence_length must be a positive integer"
        
        if data['sequence_length'] != len(data['tokens']):
            return False, "sequence_length must match len(tokens)"
        
        if not isinstance(data['validity'], bool):
            return False, "validity must be a boolean"
        
        if not isinstance(data['layer_entropy_map'], dict):
            return False, "layer_entropy_map must be a dictionary"
        
        # Validate layer_entropy_map
        for layer_id, entropy_val in data['layer_entropy_map'].items():
            if not isinstance(layer_id, int) or layer_id < 0:
                return False, f"layer_id {layer_id} must be a non-negative integer"
            if not isinstance(entropy_val, (int, float)) or entropy_val is None:
                return False, f"entropy_value for layer {layer_id} must be a non-null number"
            if entropy_val < 0:
                return False, f"entropy_value for layer {layer_id} must be non-negative"
        
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_json_schema(data: Dict[str, Any], schema_type: str) -> Tuple[bool, Optional[str]]:
    """
    Generic JSON schema validator dispatching to specific validators.
    
    Args:
        data: Dictionary to validate
        schema_type: One of 'token_sequence', 'validity_label', 'entropy_profile', 'merged_record'
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        'token_sequence': validate_token_sequence,
        'validity_label': validate_validity_label,
        'entropy_profile': validate_entropy_profile,
        'merged_record': validate_merged_record
    }
    
    if schema_type not in validators:
        return False, f"Unknown schema type: {schema_type}. Must be one of {list(validators.keys())}"
    
    return validators[schema_type](data)

def load_and_validate_jsonl(file_path: Union[str, Path], schema_type: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load a JSONL file and validate each record against a schema.
    
    Args:
        file_path: Path to the JSONL file
        schema_type: Schema type to validate against
        
    Returns:
        Tuple of (valid_records, invalid_records_with_errors)
        valid_records: List of dicts that passed validation
        invalid_records_with_errors: List of dicts with 'record' and 'error' keys
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    valid_records = []
    invalid_records = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                is_valid, error_msg = validate_json_schema(record, schema_type)
                
                if is_valid:
                    valid_records.append(record)
                else:
                    invalid_records.append({
                        'line': line_num,
                        'record': record,
                        'error': error_msg
                    })
                    logger.warning(f"Invalid record at line {line_num}: {error_msg}")
                    
            except json.JSONDecodeError as e:
                invalid_records.append({
                    'line': line_num,
                    'record': None,
                    'error': f"JSON decode error: {str(e)}"
                })
                logger.error(f"JSON decode error at line {line_num}: {str(e)}")
    
    return valid_records, invalid_records