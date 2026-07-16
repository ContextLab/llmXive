import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Compute the hash of a file's contents."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_string_hash(content: str, algorithm: str = "sha256") -> str:
    """Compute the hash of a string."""
    hash_func = hashlib.new(algorithm)
    hash_func.update(content.encode("utf-8"))
    return hash_func.hexdigest()

def compute_dict_hash(data: Dict[str, Any], algorithm: str = "sha256") -> str:
    """Compute the hash of a dictionary (sorted keys)."""
    content = json.dumps(data, sort_keys=True)
    return compute_string_hash(content, algorithm)

def save_hash(hash_value: str, output_path: Union[str, Path]) -> None:
    """Save a hash value to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(hash_value)

def load_hash(input_path: Union[str, Path]) -> str:
    """Load a hash value from a file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Hash file not found: {path}")
    with open(path, "r") as f:
        return f.read().strip()

def verify_file_hash(file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify a file's hash against an expected value."""
    computed = compute_file_hash(file_path, algorithm)
    return computed == expected_hash

def hash_state_artifact(artifact_path: Union[str, Path]) -> str:
    """Compute hash for a state artifact."""
    return compute_file_hash(artifact_path)

def verify_state_artifact(artifact_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify a state artifact's hash."""
    return verify_file_hash(artifact_path, expected_hash)

def main() -> None:
    """CLI entry point for hashing utilities."""
    print("Hashing utilities loaded.")

if __name__ == "__main__":
    main()