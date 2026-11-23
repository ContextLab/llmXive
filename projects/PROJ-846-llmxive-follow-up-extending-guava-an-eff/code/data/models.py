from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class FailureType(str, Enum):
    """Types of failures in the execution pipeline."""
    GEOMETRIC = "geometric"
    SEMANTIC = "semantic"
    PERCEPTION = "perception"
    LATENCY = "latency"
    OTHER = "other"

class PerceptionQuality(str, Enum):
    """Quality levels of perception output."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MISSING = "missing"

class SymbolicObservation(BaseModel):
    """
    Symbolic representation of an observation.
    Contains detected objects, their properties, and scene context.
    """
    timestamp: float = Field(..., description="Timestamp of the observation")
    trajectory_id: str = Field(..., description="ID of the trajectory this observation belongs to")
    frame_index: int = Field(..., description="Index of the frame within the trajectory")
    detected_objects: List[Dict[str, Any]] = Field(
        ...,
        description="List of detected objects with class, bbox, centroid, and color_hist"
    )
    scene_empty: bool = Field(False, description="True if no objects were detected")
    perception_quality: PerceptionQuality = Field(
        PerceptionQuality.MEDIUM,
        description="Quality assessment of the perception output"
    )

    @field_validator("detected_objects")
    @classmethod
    def validate_objects(cls, v):
        for obj in v:
            if "class" not in obj:
                raise ValueError("Each object must have a 'class' field")
            if "bbox" not in obj or len(obj["bbox"]) != 4:
                raise ValueError("Each object must have a 'bbox' field with 4 integers")
            if "centroid" not in obj or len(obj["centroid"]) != 2:
                raise ValueError("Each object must have a 'centroid' field with 2 floats")
        return v

class Trajectory(BaseModel):
    """
    A sequence of symbolic observations representing a task execution.
    """
    trajectory_id: str = Field(..., description="Unique identifier for the trajectory")
    task_id: str = Field(..., description="ID of the task being executed")
    observations: List[SymbolicObservation] = Field(
        ...,
        description="Ordered list of symbolic observations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the trajectory"
    )

class TaskOutcome(BaseModel):
    """
    Result of executing a task with an agent.
    """
    trajectory_id: str = Field(..., description="ID of the trajectory")
    success: bool = Field(..., description="Whether the task was completed successfully")
    failure_type: Optional[FailureType] = Field(
        None,
        description="Type of failure if the task was not successful"
    )
    steps_executed: int = Field(..., description="Number of steps executed")
    latency_induced: bool = Field(
        False,
        description="True if failure was due to latency exceeding threshold"
    )
    completion_time: float = Field(..., description="Total time to complete the task in seconds")

class PerceptionLog(BaseModel):
    """
    Log entry for perception ground-truth comparison.
    """
    timestamp: float = Field(..., description="Timestamp of the log entry")
    detected_objects: List[Dict[str, Any]] = Field(
        ...,
        description="Objects detected by the perception model"
    )
    confidence_scores: List[float] = Field(
        ...,
        description="Confidence scores for each detected object"
    )
    object_missing_if_visible: bool = Field(
        ...,
        description="True if an object that should be visible was not detected"
    )

def serialize_trajectory(trajectory: Trajectory) -> Dict[str, Any]:
    """
    Serialize a Trajectory object to a dictionary.
    
    Args:
        trajectory: Trajectory object to serialize
        
    Returns:
        Dictionary representation
    """
    return {
        "trajectory_id": trajectory.trajectory_id,
        "task_id": trajectory.task_id,
        "observations": [obs.model_dump() for obs in trajectory.observations],
        "metadata": trajectory.metadata
    }

def serialize_outcome(outcome: TaskOutcome) -> Dict[str, Any]:
    """
    Serialize a TaskOutcome object to a dictionary.
    
    Args:
        outcome: TaskOutcome object to serialize
        
    Returns:
        Dictionary representation
    """
    return {
        "trajectory_id": outcome.trajectory_id,
        "success": outcome.success,
        "failure_type": outcome.failure_type.value if outcome.failure_type else None,
        "steps_executed": outcome.steps_executed,
        "latency_induced": outcome.latency_induced,
        "completion_time": outcome.completion_time
    }

def serialize_perception_log(log: PerceptionLog) -> Dict[str, Any]:
    """
    Serialize a PerceptionLog object to a dictionary.
    
    Args:
        log: PerceptionLog object to serialize
        
    Returns:
        Dictionary representation
    """
    return {
        "timestamp": log.timestamp,
        "detected_objects": log.detected_objects,
        "confidence_scores": log.confidence_scores,
        "object_missing_if_visible": log.object_missing_if_visible
    }
