"""
Data models for method signatures and docstring pairs.
Provides serialization/deserialization and checksum utilities.
"""
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


class SerializationException(Exception):
    """Raised when serialization or deserialization fails."""
    pass


@dataclass
class MethodSignature:
    """
    Represents a parsed method signature from source code.
    """
    method_name: str
    class_name: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_annotation: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    source_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MethodSignature":
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class DocstringPair:
    """
    Represents a pair of human-written and generated docstrings
    for a specific method signature.
    """
    method_signature: MethodSignature
    human_docstring: Optional[str] = None
    generated_docstring: Optional[str] = None
    parameter_coverage_score: Optional[float] = None
    semantic_similarity: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        result["method_signature"] = self.method_signature.to_dict()
        result["human_docstring"] = self.human_docstring
        result["generated_docstring"] = self.generated_docstring
        result["parameter_coverage_score"] = self.parameter_coverage_score
        result["semantic_similarity"] = self.semantic_similarity
        result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocstringPair":
        """Create instance from dictionary."""
        sig_data = data.get("method_signature", {})
        if isinstance(sig_data, dict):
            method_sig = MethodSignature.from_dict(sig_data)
        else:
            raise SerializationException("method_signature must be a dictionary")

        return cls(
            method_signature=method_sig,
            human_docstring=data.get("human_docstring"),
            generated_docstring=data.get("generated_docstring"),
            parameter_coverage_score=data.get("parameter_coverage_score"),
            semantic_similarity=data.get("semantic_similarity"),
            metadata=data.get("metadata", {})
        )


def serialize_pairs_to_json(pairs: List[DocstringPair], output_path: str) -> None:
    """
    Serialize a list of DocstringPair objects to a JSON file.

    Args:
        pairs: List of DocstringPair objects to serialize.
        output_path: Path to the output JSON file.

    Raises:
        SerializationException: If serialization fails.
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [pair.to_dict() for pair in pairs]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        raise SerializationException(f"Failed to serialize pairs to {output_path}: {e}")


def deserialize_pairs_from_json(input_path: str) -> List[DocstringPair]:
    """
    Deserialize a list of DocstringPair objects from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of DocstringPair objects.

    Raises:
        SerializationException: If deserialization fails or file is invalid.
    """
    try:
        path = Path(input_path)
        if not path.exists():
            raise SerializationException(f"File not found: {input_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise SerializationException("JSON root must be a list of pairs")

        pairs = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise SerializationException(f"Item at index {i} is not a dictionary")
            pairs.append(DocstringPair.from_dict(item))

        return pairs

    except json.JSONDecodeError as e:
        raise SerializationException(f"Invalid JSON in {input_path}: {e}")
    except Exception as e:
        raise SerializationException(f"Failed to deserialize pairs from {input_path}: {e}")


def compute_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        SerializationException: If file cannot be read.
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise SerializationException(f"Failed to compute checksum for {file_path}: {e}")