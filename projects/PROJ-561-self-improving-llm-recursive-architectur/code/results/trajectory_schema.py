"""
Trajectory schema and writer for tracking self-improvement cycles.

This module defines the Pydantic model for a single trajectory entry
and provides a writer function to append entries to results/trajectory.json.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator
from config import PathConfig

# Initialize path config to get the results directory
_path_config = PathConfig()
TRAJECTORY_PATH = _path_config.results_dir / "trajectory.json"


class TrajectoryEntry(BaseModel):
    """
    Schema for a single refinement cycle result.

    Captures the state of the model after one cycle of modification,
    training, and evaluation.
    """
    cycle_number: int = Field(..., description="Sequential cycle number (1-based)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of cycle completion")
    param_count: int = Field(..., description="Total number of trainable parameters")
    
    # Benchmark metrics
    gsm8k_accuracy: float = Field(..., description="GSM8K accuracy (0.0 - 1.0)")
    arc_accuracy: float = Field(..., description="ARC-Challenge accuracy (0.0 - 1.0)")
    wikitext2_ece: float = Field(..., description="Wikitext-2 Expected Calibration Error")
    
    # Resource usage
    flops: int = Field(..., description="Total FLOPs consumed during training")
    training_time_seconds: float = Field(..., description="Wall-clock training time in seconds")
    
    # Metadata
    modification_type: Optional[str] = Field(None, description="Type of architectural modification applied")
    modification_magnitude: Optional[float] = Field(None, description="Magnitude of the modification")
    status: str = Field(default="completed", description="Cycle status: completed, failed, timeout")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid ISO timestamp: {v}")
        return v

    @field_validator('gsm8k_accuracy', 'arc_accuracy', 'wikitext2_ece')
    @classmethod
    def validate_metrics_range(cls, v: float) -> float:
        """Ensure metrics are within valid ranges."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Metric must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('flops', 'param_count')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure counts are non-negative."""
        if v < 0:
            raise ValueError(f"Count must be non-negative, got {v}")
        return v

    @field_validator('training_time_seconds')
    @classmethod
    def validate_time_positive(cls, v: float) -> float:
        """Ensure time is positive."""
        if v < 0:
            raise ValueError(f"Time must be non-negative, got {v}")
        return v


def write_trajectory(entries: List[TrajectoryEntry]) -> str:
    """
    Write a list of trajectory entries to results/trajectory.json.

    If the file exists, it loads existing entries and appends the new ones.
    If the file does not exist, it creates a new one.

    Args:
        entries: List of TrajectoryEntry objects to write.

    Returns:
        Path to the written file.
    """
    # Ensure results directory exists
    os.makedirs(_path_config.results_dir, exist_ok=True)

    # Load existing entries if file exists
    existing_entries = []
    if TRAJECTORY_PATH.exists():
        with open(TRAJECTORY_PATH, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    existing_entries = [TrajectoryEntry(**item) for item in data]
            except (json.JSONDecodeError, ValueError) as e:
                # If file is corrupted, start fresh but log warning
                print(f"Warning: Could not load existing trajectory, starting fresh. Error: {e}")
                existing_entries = []

    # Combine and write
    all_entries = existing_entries + entries
    output_data = [entry.model_dump() for entry in all_entries]

    with open(TRAJECTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return str(TRAJECTORY_PATH)


def read_trajectory() -> List[TrajectoryEntry]:
    """
    Read all entries from results/trajectory.json.

    Returns:
        List of TrajectoryEntry objects. Returns empty list if file doesn't exist.
    """
    if not TRAJECTORY_PATH.exists():
        return []

    with open(TRAJECTORY_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return [TrajectoryEntry(**item) for item in data]
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Failed to parse trajectory file: {e}")


def get_latest_entry() -> Optional[TrajectoryEntry]:
    """
    Get the most recent trajectory entry.

    Returns:
        The latest TrajectoryEntry or None if no entries exist.
    """
    entries = read_trajectory()
    return entries[-1] if entries else None
