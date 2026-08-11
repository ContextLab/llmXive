import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from config import get_config

class TrajectoryEntry(BaseModel):
    """Schema for a single trajectory entry."""
    cycle_number: int = Field(..., description="Cycle number")
    param_count: int = Field(..., description="Number of parameters in model")
    GSM8K: float = Field(..., description="GSM8K benchmark accuracy")
    ARC: float = Field(..., description="ARC-Challenge benchmark accuracy")
    BoolQ: float = Field(..., description="BoolQ benchmark ECE")
    FLOPs: int = Field(..., description="FLOPs count for the cycle")
    training_time: float = Field(..., description="Training time in seconds")
    
    @field_validator('GSM8K', 'ARC', 'BoolQ')
    @classmethod
    def validate_metrics(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Benchmark metrics must be between 0 and 1, got {v}")
        return v

def write_trajectory(entry: TrajectoryEntry) -> str:
    """Write a trajectory entry to the trajectory file."""
    config = get_config()
    trajectory_path = os.path.join(config.paths.results_dir, "trajectory.json")
    
    os.makedirs(os.path.dirname(trajectory_path), exist_ok=True)
    
    # Read existing entries if file exists
    entries = []
    if os.path.exists(trajectory_path):
        with open(trajectory_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    # Append new entry
    entries.append(entry.model_dump())
    
    # Write all entries
    with open(trajectory_path, 'w') as f:
        for entry_data in entries:
            f.write(json.dumps(entry_data) + "\n")
    
    return trajectory_path

def read_trajectory() -> List[Dict[str, Any]]:
    """Read all trajectory entries from the file."""
    config = get_config()
    trajectory_path = os.path.join(config.paths.results_dir, "trajectory.json")
    
    if not os.path.exists(trajectory_path):
        return []
    
    entries = []
    with open(trajectory_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return entries

def get_latest_entry() -> Optional[Dict[str, Any]]:
    """Get the latest trajectory entry."""
    entries = read_trajectory()
    return entries[-1] if entries else None