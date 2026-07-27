"""
Validation utilities for llmXive data schemas.

This module provides dataclasses for schema definition and validation functions
for TokenSequence, ValidityLabel, LayerEntropy, and EntropyProfile entities.
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
    """Represents a generated token sequence with metadata."""
    sequence_id: str
    prompt_id: str
    task_type: str  # 'gsm8k' or 'minigrid'
    tokens: List[str]
    token_ids: Optional[List[int]] = None
    generation_time_ms: Optional[float] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenSequence':
        return cls(
            sequence_id=data['sequence_id'],
            prompt_id=data['prompt_id'],
            task_type=data['task_type'],
            tokens=data['tokens'],
            token_ids=data.get('token_ids'),
            generation_time_ms=data.get('generation_time_ms'),
            model_name=data.get('model_name'),
            temperature=data.get('temperature'),
            seed=data.get('seed')
        )


@dataclass
class ValidityLabel:
    """Represents validity labels for a token sequence."""
    sequence_id: str
    prompt_id: str
    labels: List[bool]  # True = valid, False = invalid
    validity_scores: Optional[List[float]] = None  # Optional confidence scores
    matching_path_id: Optional[str] = None  # ID of matched ground truth path
    is_ambiguous: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidityLabel':
        return cls(
            sequence_id=data['sequence_id'],
            prompt_id=data['prompt_id'],
            labels=data['labels'],
            validity_scores=data.get('validity_scores'),
            matching_path_id=data.get('matching_path_id'),
            is_ambiguous=data.get('is_ambiguous', False)
        )


@dataclass
class LayerEntropy:
    """Entropy values for a single layer at a specific token position."""
    layer_index: int
    entropy_value: float
    layer_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerEntropy':
        return cls(
            layer_index=data['layer_index'],
            entropy_value=data['entropy_value'],
            layer_name=data.get('layer_name')
        )


@dataclass
class EntropyProfile:
    """Complete entropy profile for a token sequence across all layers."""
    sequence_id: str
    prompt_id: str
    task_type: str
    token_index: int
    token_id: int
    token_text: str
    layer_entropies: List[LayerEntropy]
    mean_entropy: float
    max_entropy: float
    min_entropy: float
    entropy_std: float
    validity_label: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['layer_entropies'] = [le.to_dict() for le in self.layer_entropies]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntropyProfile':
        layer_entropies = [
            LayerEntropy.from_dict(le) for le in data['layer_entropies']
        ]
        return cls(
            sequence_id=data['sequence_id'],
            prompt_id=data['prompt_id'],
            task_type=data['task_type'],
            token_index=data['token_index'],
            token_id=data['token_id'],
            token_text=data['token_text'],
            layer_entropies=layer_entropies,
            mean_entropy=data['mean_entropy'],
            max_entropy=data['max_entropy'],
            min_entropy=data['min_entropy'],
            entropy_std=data['entropy_std'],
            validity_label=data.get('validity_label')
        )


def validate_token_sequence(seq: TokenSequence) -> Tuple[bool, List[str]]:
    """
    Validate a TokenSequence instance.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not seq.sequence_id or not isinstance(seq.sequence_id, str):
        errors.append("sequence_id must be a non-empty string")

    if not seq.prompt_id or not isinstance(seq.prompt_id, str):
        errors.append("prompt_id must be a non-empty string")

    if seq.task_type not in ['gsm8k', 'minigrid']:
        errors.append(f"task_type must be 'gsm8k' or 'minigrid', got '{seq.task_type}'")

    if not seq.tokens or not isinstance(seq.tokens, list):
        errors.append("tokens must be a non-empty list")

    if seq.token_ids is not None:
        if not isinstance(seq.token_ids, list):
            errors.append("token_ids must be a list or None")
        elif len(seq.token_ids) != len(seq.tokens):
            errors.append(f"token_ids length ({len(seq.token_ids)}) must match tokens length ({len(seq.tokens)})")

    if seq.generation_time_ms is not None and seq.generation_time_ms < 0:
        errors.append("generation_time_ms must be non-negative")

    if seq.temperature is not None and (seq.temperature < 0 or seq.temperature > 2.0):
        errors.append("temperature must be between 0.0 and 2.0")

    return len(errors) == 0, errors


def validate_validity_label(label: ValidityLabel) -> Tuple[bool, List[str]]:
    """
    Validate a ValidityLabel instance.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not label.sequence_id or not isinstance(label.sequence_id, str):
        errors.append("sequence_id must be a non-empty string")

    if not label.prompt_id or not isinstance(label.prompt_id, str):
        errors.append("prompt_id must be a non-empty string")

    if not label.labels or not isinstance(label.labels, list):
        errors.append("labels must be a non-empty list")

    if not all(isinstance(l, bool) for l in label.labels):
        errors.append("All labels must be boolean")

    if label.validity_scores is not None:
        if not isinstance(label.validity_scores, list):
            errors.append("validity_scores must be a list or None")
        elif len(label.validity_scores) != len(label.labels):
            errors.append(f"validity_scores length must match labels length")
        elif not all(isinstance(s, (int, float)) for s in label.validity_scores):
            errors.append("All validity_scores must be numeric")

    return len(errors) == 0, errors


def validate_entropy_profile(profile: EntropyProfile) -> Tuple[bool, List[str]]:
    """
    Validate an EntropyProfile instance.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not profile.sequence_id or not isinstance(profile.sequence_id, str):
        errors.append("sequence_id must be a non-empty string")

    if not profile.prompt_id or not isinstance(profile.prompt_id, str):
        errors.append("prompt_id must be a non-empty string")

    if profile.task_type not in ['gsm8k', 'minigrid']:
        errors.append(f"task_type must be 'gsm8k' or 'minigrid', got '{profile.task_type}'")

    if profile.token_index < 0:
        errors.append("token_index must be non-negative")

    if not isinstance(profile.token_id, int):
        errors.append("token_id must be an integer")

    if not profile.token_text or not isinstance(profile.token_text, str):
        errors.append("token_text must be a non-empty string")

    if not profile.layer_entropies or not isinstance(profile.layer_entropies, list):
        errors.append("layer_entropies must be a non-empty list")

    for i, le in enumerate(profile.layer_entropies):
        if not isinstance(le, LayerEntropy):
            errors.append(f"layer_entropies[{i}] must be a LayerEntropy instance")
            continue

        if le.layer_index < 0:
            errors.append(f"layer_entropies[{i}].layer_index must be non-negative")

        if not isinstance(le.entropy_value, (int, float)):
            errors.append(f"layer_entropies[{i}].entropy_value must be numeric")
        elif le.entropy_value < 0:
            errors.append(f"layer_entropies[{i}].entropy_value must be non-negative")

    # Validate aggregate statistics
    if not isinstance(profile.mean_entropy, (int, float)) or profile.mean_entropy < 0:
        errors.append("mean_entropy must be a non-negative number")

    if not isinstance(profile.max_entropy, (int, float)) or profile.max_entropy < 0:
        errors.append("max_entropy must be a non-negative number")

    if not isinstance(profile.min_entropy, (int, float)) or profile.min_entropy < 0:
        errors.append("min_entropy must be a non-negative number")

    if not isinstance(profile.entropy_std, (int, float)) or profile.entropy_std < 0:
        errors.append("entropy_std must be a non-negative number")

    return len(errors) == 0, errors


def validate_merged_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a merged record containing TokenSequence, ValidityLabel, and EntropyProfile data.

    Expected keys:
      - sequence_id (str)
      - prompt_id (str)
      - task_type (str)
      - tokens (List[str])
      - labels (List[bool])
      - layer_entropies (List[Dict]) or per-token entropy data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    required_fields = ['sequence_id', 'prompt_id', 'task_type', 'tokens', 'labels']
    for field_name in required_fields:
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")

    if 'sequence_id' in record and not isinstance(record['sequence_id'], str):
        errors.append("sequence_id must be a string")

    if 'prompt_id' in record and not isinstance(record['prompt_id'], str):
        errors.append("prompt_id must be a string")

    if 'task_type' in record and record['task_type'] not in ['gsm8k', 'minigrid']:
        errors.append(f"task_type must be 'gsm8k' or 'minigrid', got '{record['task_type']}'")

    if 'tokens' in record:
        if not isinstance(record['tokens'], list):
            errors.append("tokens must be a list")
        elif len(record['tokens']) == 0:
            errors.append("tokens cannot be empty")

    if 'labels' in record:
        if not isinstance(record['labels'], list):
            errors.append("labels must be a list")
        elif len(record['labels']) == 0:
            errors.append("labels cannot be empty")
        elif len(record['tokens']) > 0 and len(record['labels']) != len(record['tokens']):
            errors.append(f"labels length ({len(record['labels'])}) must match tokens length ({len(record['tokens'])})")

    return len(errors) == 0, errors


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dictionary against a simple JSON schema definition.

    Args:
        data: The dictionary to validate
        schema: Schema definition with 'type' and 'properties' keys

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not isinstance(data, dict):
        if schema.get('type') == 'object':
            errors.append("Expected a dictionary/object")
        return len(errors) == 0, errors

    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Check required fields
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check field types
    for field_name, field_schema in properties.items():
        if field_name not in data:
            continue

        value = data[field_name]
        expected_type = field_schema.get('type')

        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }

        if expected_type in type_map:
          expected_python_type = type_map[expected_type]
          if not isinstance(value, expected_python_type):
              errors.append(f"Field '{field_name}' must be of type {expected_type}, got {type(value).__name__}")

          # Special handling for arrays
          if expected_type == 'array' and 'items' in field_schema:
              item_schema = field_schema['items']
              item_type = item_schema.get('type')
              if item_type in type_map:
                  expected_item_type = type_map[item_type]
                  for i, item in enumerate(value):
                      if not isinstance(item, expected_item_type):
                          errors.append(f"Item {i} in '{field_name}' must be of type {item_type}")

    return len(errors) == 0, errors


def load_and_validate_jsonl(
    file_path: Union[str, Path],
    validator_func,
    schema: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load and validate a JSONL file.

    Args:
        file_path: Path to the JSONL file
        validator_func: A function that takes a dict and returns (is_valid, errors)
        schema: Optional JSON schema for additional validation

    Returns:
        Tuple of (valid_records, invalid_records_with_errors)
    """
    valid_records = []
    invalid_records = []

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                invalid_records.append({
                    'line': line_num,
                    'error': f"JSON decode error: {str(e)}",
                    'content': line
                })
                continue

            # Validate using the provided validator
            is_valid, errors = validator_func(record)

            if is_valid:
                # Additional schema validation if provided
                if schema:
                    schema_valid, schema_errors = validate_json_schema(record, schema)
                    if not schema_valid:
                        is_valid = False
                        errors.extend(schema_errors)

            if is_valid:
                valid_records.append(record)
            else:
                invalid_records.append({
                    'line': line_num,
                    'errors': errors,
                    'record': record
                })

    return valid_records, invalid_records
