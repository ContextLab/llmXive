"""
Data models and serialization utilities for the extraction pipeline.
"""
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
from utils.exceptions import SerializationException

@dataclass
class MethodSignature:
    """Represents a method signature extracted from AST."""
    name: str
    signature: str
    params: List[str] = field(default_factory=list)
    file_path: str = ""
    line_number: Optional[int] = None

@dataclass
class DocstringPair:
    """Pairs a method signature with its human-written and generated docstrings."""
    method_name: str
    signature: str
    file_path: str
    ast_params: List[str] = field(default_factory=list)
    human_docstring: Optional[str] = None
    generated_docstring: Optional[str] = None
    coverage_score: Optional[float] = None
    semantic_similarity: Optional[float] = None
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'method_name': self.method_name,
            'signature': self.signature,
            'file_path': self.file_path,
            'ast_params': self.ast_params,
            'human_docstring': self.human_docstring,
            'generated_docstring': self.generated_docstring,
            'coverage_score': self.coverage_score,
            'semantic_similarity': self.semantic_similarity,
            'needs_review': self.needs_review
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocstringPair':
        """Create instance from dictionary."""
        return cls(
            method_name=data.get('method_name', ''),
            signature=data.get('signature', ''),
            file_path=data.get('file_path', ''),
            ast_params=data.get('ast_params', []),
            human_docstring=data.get('human_docstring'),
            generated_docstring=data.get('generated_docstring'),
            coverage_score=data.get('coverage_score'),
            semantic_similarity=data.get('semantic_similarity'),
            needs_review=data.get('needs_review', False)
        )

def serialize_pairs_to_json(pairs: List[DocstringPair], output_path: Path) -> None:
    """
    Serialize a list of DocstringPair objects to a JSON file.
    
    Args:
        pairs: List of DocstringPair objects
        output_path: Path to output JSON file
        
    Raises:
        SerializationException: If serialization fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [pair.to_dict() for pair in pairs]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        raise SerializationException(f"Failed to serialize pairs to {output_path}: {e}")

def deserialize_pairs_from_json(input_path: Path) -> List[DocstringPair]:
    """
    Deserialize a JSON file to a list of DocstringPair objects.
    
    Args:
        input_path: Path to input JSON file
        
    Returns:
        List of DocstringPair objects
        
    Raises:
        SerializationException: If deserialization fails
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [DocstringPair.from_dict(item) for item in data]
        
    except Exception as e:
        raise SerializationException(f"Failed to deserialize pairs from {input_path}: {e}")

def compute_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()