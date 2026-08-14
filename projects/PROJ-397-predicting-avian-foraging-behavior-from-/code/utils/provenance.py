import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA256 hash of a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_data_hash(data: Any) -> str:
    """
    Computes the SHA256 hash of data (serialized to JSON).
    """
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()

def generate_provenance_record(step_name: str, input_files: List[Path], output_files: List[Path], metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generates a provenance record for a step.
    """
    record = {
        "step_name": step_name,
        "timestamp": datetime.now().isoformat(),
        "input_files": [str(f) for f in input_files],
        "output_files": [str(f) for f in output_files],
        "input_hashes": {str(f): compute_file_hash(f) for f in input_files if f.exists()},
        "output_hashes": {str(f): compute_file_hash(f) for f in output_files if f.exists()},
        "metadata": metadata or {}
    }
    return record

def save_provenance_record(record: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Saves a provenance record to a YAML file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(record, f, default_flow_style=False)

def log_step(step_name: str, input_files: List[Path], output_files: List[Path], metadata: Optional[Dict] = None, provenance_dir: Optional[Path] = None) -> Path:
    """
    Logs a step's provenance record.
    """
    record = generate_provenance_record(step_name, input_files, output_files, metadata)
    
    if provenance_dir is None:
        provenance_dir = Path("provenance")
    provenance_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = provenance_dir / f"{step_name}_provenance.yaml"
    save_provenance_record(record, output_path)
    return output_path

def verify_data_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verifies the integrity of a file by comparing its hash to an expected hash.
    """
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash
