"""
Base entity models for the Audio Hallucination Analysis pipeline.

This module defines the core data structures: AudioSample and ModelInstance.
These classes provide type safety, validation, and serialization methods
for the research pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import hashlib
from datetime import datetime

from config import get_audio_config


@dataclass
class AudioSample:
    """
    Represents a single audio sample used in the analysis.

    Attributes:
        sample_id: Unique identifier for the sample.
        domain: Category of the audio (e.g., 'speech', 'music', 'env').
        source_dataset: Name of the dataset this sample originated from.
        file_path: Path to the audio file on disk.
        duration_sec: Duration of the audio in seconds.
        sample_rate: Audio sampling rate in Hz.
        ground_truth_text: Reference text or label for the audio.
        checksum: SHA-256 hash of the file content for integrity verification.
        metadata: Additional arbitrary metadata.
    """
    sample_id: str
    domain: str
    source_dataset: str
    file_path: str
    duration_sec: float
    sample_rate: int
    ground_truth_text: str
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and compute checksum if not provided."""
        if not self.domain:
            raise ValueError("Domain cannot be empty")
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        
        # Validate domain against known categories if strict mode is desired
        # For now, we accept any string but log a warning if unknown
        valid_domains = {'speech', 'music', 'env'}
        if self.domain.lower() not in valid_domains:
            # In a real pipeline, we might raise an error or log a warning
            pass 

        # Compute checksum if missing
        if self.checksum is None:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Calculate SHA-256 checksum of the file."""
        path = Path(self.file_path)
        if not path.exists():
            return "missing_file"
        
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return "error_computing_checksum"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary for serialization."""
        return {
            "sample_id": self.sample_id,
            "domain": self.domain,
            "source_dataset": self.source_dataset,
            "file_path": self.file_path,
            "duration_sec": self.duration_sec,
            "sample_rate": self.sample_rate,
            "ground_truth_text": self.ground_truth_text,
            "checksum": self.checksum,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioSample':
        """Create an AudioSample instance from a dictionary."""
        return cls(
            sample_id=data["sample_id"],
            domain=data["domain"],
            source_dataset=data["source_dataset"],
            file_path=data["file_path"],
            duration_sec=data["duration_sec"],
            sample_rate=data["sample_rate"],
            ground_truth_text=data["ground_truth_text"],
            checksum=data.get("checksum"),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the sample to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'AudioSample':
        """Deserialize a JSON string to an AudioSample instance."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ModelInstance:
    """
    Represents a Large Audio Language Model (LALM) instance configured for inference.

    Attributes:
        model_id: Unique identifier for the model (e.g., HF repo ID).
        model_name: Human-readable name of the model.
        architecture: Model architecture type (e.g., 'transformer', 'conformer').
        parameters_millions: Estimated parameter count in millions.
        training_data_volume: Estimated total training data volume (hours/tokens).
        training_domains: List of domains the model was trained on.
        is_excluded: Flag indicating if the model should be excluded from analysis
                     based on training data overlap with test sets.
        exclusion_reason: Reason for exclusion if is_excluded is True.
        loaded: Flag indicating if the model is currently loaded in memory.
        config: Additional model-specific configuration.
    """
    model_id: str
    model_name: str
    architecture: str = "unknown"
    parameters_millions: Optional[float] = None
    training_data_volume: Optional[float] = None
    training_domains: List[str] = field(default_factory=list)
    is_excluded: bool = False
    exclusion_reason: Optional[str] = None
    loaded: bool = False
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate model attributes."""
        if not self.model_id:
            raise ValueError("Model ID cannot be empty")
        if not self.model_name:
            raise ValueError("Model name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "architecture": self.architecture,
            "parameters_millions": self.parameters_millions,
            "training_data_volume": self.training_data_volume,
            "training_domains": self.training_domains,
            "is_excluded": self.is_excluded,
            "exclusion_reason": self.exclusion_reason,
            "loaded": self.loaded,
            "config": self.config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInstance':
        """Create a ModelInstance from a dictionary."""
        return cls(
            model_id=data["model_id"],
            model_name=data["model_name"],
            architecture=data.get("architecture", "unknown"),
            parameters_millions=data.get("parameters_millions"),
            training_data_volume=data.get("training_data_volume"),
            training_domains=data.get("training_domains", []),
            is_excluded=data.get("is_excluded", False),
            exclusion_reason=data.get("exclusion_reason"),
            loaded=data.get("loaded", False),
            config=data.get("config", {})
        )

    def mark_excluded(self, reason: str) -> None:
        """Mark the model as excluded with a specific reason."""
        self.is_excluded = True
        self.exclusion_reason = reason

    def to_json(self) -> str:
        """Serialize the model instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelInstance':
        """Deserialize a JSON string to a ModelInstance."""
        data = json.loads(json_str)
        return cls.from_dict(data)