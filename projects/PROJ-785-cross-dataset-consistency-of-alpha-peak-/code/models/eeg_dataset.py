"""
Data model for EEG Dataset entities.
Matches the schema expected by contracts and used throughout the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

@dataclass
class EEGDataset:
    """
    Represents a single EEG dataset (e.g., from OpenNeuro).
    
    Attributes:
        dataset_id: OpenNeuro dataset identifier (e.g., 'ds003775')
        subject_ids: List of subject identifiers present in the dataset
        raw_path: Path to the raw BIDS data directory
        derivative_path: Path to the preprocessed derivatives
        sampling_frequency: Sampling frequency in Hz
        channel_count: Number of EEG channels
        task: Task name (e.g., 'rest')
        metadata: Additional BIDS metadata
        created_at: Timestamp of entity creation
        sha256_checksum: SHA256 hash of the raw data for integrity verification
    """
    dataset_id: str
    subject_ids: List[str] = field(default_factory=list)
    raw_path: Optional[Path] = None
    derivative_path: Optional[Path] = None
    sampling_frequency: Optional[float] = None
    channel_count: Optional[int] = None
    task: str = "rest"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sha256_checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataset to a dictionary for serialization."""
        return {
            "dataset_id": self.dataset_id,
            "subject_ids": self.subject_ids,
            "raw_path": str(self.raw_path) if self.raw_path else None,
            "derivative_path": str(self.derivative_path) if self.derivative_path else None,
            "sampling_frequency": self.sampling_frequency,
            "channel_count": self.channel_count,
            "task": self.task,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "sha256_checksum": self.sha256_checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EEGDataset":
        """Create an EEGDataset instance from a dictionary."""
        raw_path = Path(data["raw_path"]) if data.get("raw_path") else None
        derivative_path = Path(data["derivative_path"]) if data.get("derivative_path") else None
        
        # Parse datetime if string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            dataset_id=data["dataset_id"],
            subject_ids=data.get("subject_ids", []),
            raw_path=raw_path,
            derivative_path=derivative_path,
            sampling_frequency=data.get("sampling_frequency"),
            channel_count=data.get("channel_count"),
            task=data.get("task", "rest"),
            metadata=data.get("metadata", {}),
            created_at=created_at or datetime.utcnow(),
            sha256_checksum=data.get("sha256_checksum"),
        )

    def save_json(self, path: Path) -> None:
        """Save the dataset metadata to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path) -> "EEGDataset":
        """Load a dataset instance from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
