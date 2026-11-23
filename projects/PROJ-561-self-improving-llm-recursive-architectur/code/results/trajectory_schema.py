import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from config import get_config

class TrajectoryEntry(BaseModel):
    cycle_number: int
    param_count: int
    gsm8k_accuracy: float
    arc_challenge_accuracy: float
    boolq_ece: float
    flops: int
    training_time: float
    slope: float
    intercept: float
    r_squared: float
    trend_direction: str
    timed_out: Optional[bool] = False

def write_trajectory(path: str, entry: TrajectoryEntry) -> None:
    """
    Appends a trajectory entry to the JSON file.
    Creates the file if it doesn't exist.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    data = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    
    data.append(entry.model_dump())
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def read_trajectory(path: str) -> List[TrajectoryEntry]:
    """Reads the trajectory file and returns a list of entries."""
    if not os.path.exists(path):
        return []
    
    with open(path, "r") as f:
        data = json.load(f)
    
    return [TrajectoryEntry(**item) for item in data]

def get_latest_entry(path: str) -> Optional[TrajectoryEntry]:
    """Returns the most recent entry."""
    entries = read_trajectory(path)
    return entries[-1] if entries else None