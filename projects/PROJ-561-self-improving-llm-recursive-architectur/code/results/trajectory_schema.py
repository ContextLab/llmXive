import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

from config import PathConfig


class TrajectoryEntry(BaseModel):
    """
    Schema for a single cycle's trajectory data.
    Captures the state and metrics after one refinement cycle.
    """
    cycle_number: int = Field(..., description="The 1-based index of the cycle")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of when the cycle completed"
    )
    param_count: int = Field(..., description="Total number of trainable parameters in the model")
    
    # Benchmark metrics
    gsm8k_accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy on GSM8K benchmark")
    arc_challenge_accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy on ARC-Challenge benchmark")
    wikitext2_ece: float = Field(..., ge=0.0, description="Expected Calibration Error on Wikitext-2")
    
    # Resource metrics
    flops: float = Field(..., description="Total FLOPs consumed during training")
    training_time_seconds: float = Field(..., ge=0.0, description="Wall-clock time for training in seconds")
    
    # Modification details
    modification_type: Optional[str] = Field(None, description="Type of architectural modification applied")
    modification_magnitude: Optional[float] = Field(None, description="Magnitude of the modification")
    
    # Status
    status: str = Field(default="completed", description="Status of the cycle: completed, failed, timeout")
    error_message: Optional[str] = Field(None, description="Error message if status is not completed")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        # Ensure ISO format
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Timestamp must be in ISO 8601 format")
        return v


class TrajectoryData(BaseModel):
    """
    Container for the full trajectory history.
    """
    version: str = Field(default="1.0", description="Schema version")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of when the trajectory file was created"
    )
    entries: List[TrajectoryEntry] = Field(default_factory=list, description="List of cycle entries")

    def add_entry(self, entry: TrajectoryEntry) -> None:
        """Add a new trajectory entry."""
        self.entries.append(entry)

    def get_latest_entry(self) -> Optional[TrajectoryEntry]:
        """Return the most recent entry, or None if empty."""
        if not self.entries:
            return None
        return self.entries[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "entries": [entry.dict() for entry in self.entries]
        }


def write_trajectory(trajectory: TrajectoryData, output_path: Optional[str] = None) -> str:
    """
    Write the trajectory data to a JSON file.
    
    Args:
        trajectory: The TrajectoryData object to write.
        output_path: Optional path to write to. If None, uses config default.
        
    Returns:
        The path where the file was written.
    """
    if output_path is None:
        config = PathConfig()
        output_path = os.path.join(config.results_dir, "trajectory.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write JSON with indentation for readability
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trajectory.to_dict(), f, indent=2)
    
    return output_path


def read_trajectory(input_path: Optional[str] = None) -> TrajectoryData:
    """
    Read trajectory data from a JSON file.
    
    Args:
        input_path: Optional path to read from. If None, uses config default.
        
    Returns:
        TrajectoryData object populated with file contents.
    """
    if input_path is None:
        config = PathConfig()
        input_path = os.path.join(config.results_dir, "trajectory.json")
    
    if not os.path.exists(input_path):
        # Return empty trajectory if file doesn't exist
        return TrajectoryData()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return TrajectoryData(**data)


def get_latest_entry(input_path: Optional[str] = None) -> Optional[TrajectoryEntry]:
    """
    Helper to get the latest entry from the trajectory file.
    
    Args:
        input_path: Optional path to read from. If None, uses config default.
        
    Returns:
        The latest TrajectoryEntry or None if no entries exist.
    """
    trajectory = read_trajectory(input_path)
    return trajectory.get_latest_entry()