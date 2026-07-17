import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

@dataclass
class ValidityLabel:
    sequence_id: str
    is_valid: bool
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TokenSequence:
    sequence_id: str
    tokens: List[str]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EntropyProfile:
    sequence_id: str
    entropy_values: List[float]
    layer_indices: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)

def validate_token_sequence(seq: TokenSequence) -> bool:
    if not isinstance(seq, TokenSequence):
        raise TypeError("Input must be a TokenSequence")
    if not seq.sequence_id:
        raise ValueError("sequence_id is required")
    if not isinstance(seq.tokens, list) or len(seq.tokens) == 0:
        raise ValueError("tokens must be a non-empty list")
    return True

def validate_validity_label(label: ValidityLabel) -> bool:
    if not isinstance(label, ValidityLabel):
        raise TypeError("Input must be a ValidityLabel")
    if not label.sequence_id:
        raise ValueError("sequence_id is required")
    if not isinstance(label.is_valid, bool):
        raise ValueError("is_valid must be a boolean")
    return True

def validate_entropy_profile(profile: EntropyProfile) -> bool:
    if not isinstance(profile, EntropyProfile):
        raise TypeError("Input must be an EntropyProfile")
    if not profile.sequence_id:
        raise ValueError("sequence_id is required")
    if not profile.entropy_values:
        raise ValueError("entropy_values cannot be empty")
    return True

def validate_json_schema(record: Dict, schema: Dict):
    """Simple schema validator."""
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    return True

def load_and_validate_jsonl(file_path: Path, validator_func) -> List[Any]:
    records = []
    with open(file_path, "r") as f:
        for line in f:
            data = json.loads(line)
            # Convert dict to dataclass if needed, or just validate dict
            # For this implementation, we assume the validator handles dicts or we convert
            # Here we just validate the dict structure if validator_func expects dict
            validator_func(data)
            records.append(data)
    return records
