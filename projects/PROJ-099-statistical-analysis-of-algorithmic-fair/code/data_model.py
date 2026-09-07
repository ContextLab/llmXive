from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import hashlib
import json

@dataclass
class DatasetCharacteristic:
    name: str
    value: Any
    description: Optional[str] = None

@dataclass
class FairnessMetric:
    name: str
    value: float
    description: Optional[str] = None
    formula: Optional[str] = None

@dataclass
class Model:
    model_id: str
    model_type: str
    dataset_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[FairnessMetric] = field(default_factory=list)

@dataclass
class Dataset:
    dataset_id: str
    data: Any  # pandas DataFrame
    characteristics: List[DatasetCharacteristic] = field(default_factory=list)
    checksum: Optional[str] = None

def compute_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_state_file(state: Dict[str, Any], file_path: str) -> None:
    """Save state dictionary to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)

def load_state_file(file_path: str) -> Dict[str, Any]:
    """Load state dictionary from a JSON file."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)
