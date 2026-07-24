import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class TrajectoryEntry(BaseModel):
    """Schema for a single cycle's trajectory data."""
    cycle_number: int
    timestamp: float
    status: str = Field(..., description="completed, timeout, failed")
    partial: bool = Field(False, description="True if metrics are incomplete due to timeout/failure")
    
    training_time: float = Field(..., description="Total wall-clock time in seconds")
    steps_completed: int = Field(..., description="Number of training steps completed")
    avg_loss: Optional[float] = Field(None, description="Average training loss")
    
    param_count: Optional[int] = Field(None, description="Total parameters in model")
    flops: Optional[int] = Field(None, description="Estimated FLOPs")
    
    # Evaluation metrics (can be None if timeout occurred before evaluation)
    gsm8k_accuracy: Optional[float] = Field(None)
    arc_accuracy: Optional[float] = Field(None)
    wikitext2_ece: Optional[float] = Field(None)

def write_trajectory(config: PathConfig, entry_data: Dict[str, Any]) -> None:
    """
    Appends a new entry to results/trajectory.json.
    Creates the file if it doesn't exist.
    """
    trajectory_path = config.trajectory_path
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(trajectory_path), exist_ok=True)
    
    # Load existing data
    trajectory_data = []
    if os.path.exists(trajectory_path):
        with open(trajectory_path, 'r') as f:
            try:
                trajectory_data = json.load(f)
            except json.JSONDecodeError:
                trajectory_data = []
    
    # Create new entry
    entry = TrajectoryEntry(**entry_data)
    trajectory_data.append(entry.model_dump())
    
    # Write back
    with open(trajectory_path, 'w') as f:
        json.dump(trajectory_data, f, indent=2)

def read_trajectory(config: PathConfig) -> List[Dict[str, Any]]:
    """Reads the entire trajectory file."""
    trajectory_path = config.trajectory_path
    if not os.path.exists(trajectory_path):
        return []
    
    with open(trajectory_path, 'r') as f:
        return json.load(f)

def get_latest_entry(config: PathConfig) -> Optional[Dict[str, Any]]:
    """Returns the most recent cycle entry."""
    data = read_trajectory(config)
    if not data:
        return None
    return data[-1]
