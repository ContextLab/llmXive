"""
Trajectory schema and writer for the self-improving LLM pipeline.

This module defines the Pydantic model for recording cycle metrics and
provides functions to write and read the trajectory history to/from
`results/trajectory.json`.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

from config import get_config


class TrajectoryEntry(BaseModel):
    """
    Schema for a single cycle's recorded metrics.

    Attributes:
        cycle_number: The 1-based index of the refinement cycle.
        timestamp: ISO format timestamp when the cycle completed.
        param_count: Total number of parameters in the model after modification.
        gsm8k_accuracy: Accuracy score on the GSM8K benchmark.
        arc_accuracy: Accuracy score on the ARC-Challenge benchmark.
        wikitext2_ece: Expected Calibration Error on Wikitext-2.
        flops_total: Total FLOPs consumed during the training epoch.
        training_time_seconds: Wall-clock time taken for the training epoch.
        modification_type: Type of architectural change applied (e.g., 'layer_add').
        modification_magnitude: Magnitude of the change (e.g., number of layers added).
        distinctness_valid: Boolean indicating if the modification was distinct from history.
    """
    cycle_number: int = Field(..., ge=1, description="Cycle number (1-based)")
    timestamp: str = Field(..., description="ISO format timestamp")
    param_count: int = Field(..., gt=0, description="Total parameter count")
    gsm8k_accuracy: float = Field(..., ge=0.0, le=1.0, description="GSM8K accuracy")
    arc_accuracy: float = Field(..., ge=0.0, le=1.0, description="ARC-Challenge accuracy")
    wikitext2_ece: float = Field(..., ge=0.0, description="Wikitext-2 ECE")
    flops_total: float = Field(..., ge=0.0, description="Total FLOPs")
    training_time_seconds: float = Field(..., ge=0.0, description="Training duration in seconds")
    modification_type: str = Field(..., description="Type of modification")
    modification_magnitude: int = Field(..., ge=0, description="Magnitude of modification")
    distinctness_valid: bool = Field(True, description="Whether modification was distinct")

    @field_validator('timestamp')
    @classmethod
    def check_timestamp_format(cls, v: str) -> str:
        # Ensure it parses correctly, though we generate ISO format ourselves
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Timestamp must be in ISO format")
        return v


def write_trajectory(entries: List[TrajectoryEntry], filepath: Optional[str] = None) -> str:
    """
    Writes a list of TrajectoryEntry objects to a JSON file.

    Args:
        entries: List of trajectory entries to save.
        filepath: Optional path to the JSON file. Defaults to config trajectory path.

    Returns:
        The absolute path to the written file.
    """
    if filepath is None:
        config = get_config()
        filepath = config.trajectory_path

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Serialize to JSON with indentation for readability
    data = [entry.model_dump() for entry in entries]

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    return filepath


def read_trajectory(filepath: Optional[str] = None) -> List[TrajectoryEntry]:
    """
    Reads the trajectory JSON file and returns a list of TrajectoryEntry objects.

    Args:
        filepath: Optional path to the JSON file. Defaults to config trajectory path.

    Returns:
        List of TrajectoryEntry objects. Returns empty list if file does not exist.
    """
    if filepath is None:
        config = get_config()
        filepath = config.trajectory_path

    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [TrajectoryEntry(**entry) for entry in data]


def get_latest_entry(filepath: Optional[str] = None) -> Optional[TrajectoryEntry]:
    """
    Retrieves the most recent entry from the trajectory file.

    Args:
        filepath: Optional path to the JSON file. Defaults to config trajectory path.

    Returns:
        The latest TrajectoryEntry or None if the file is empty/missing.
    """
    entries = read_trajectory(filepath)
    if not entries:
        return None
    return entries[-1]
