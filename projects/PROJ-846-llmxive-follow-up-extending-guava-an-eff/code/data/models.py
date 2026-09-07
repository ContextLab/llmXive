"""
Data models for the Symbolic-Guava pipeline.

Defines Pydantic models for:
- SymbolicObservation: Per-frame object detection and state representation.
- Trajectory: A sequence of observations and metadata for a single task attempt.
- TaskOutcome: The final result of a task execution (success/failure details).
- PerceptionLog: Detailed logging of perception performance (latency, ground truth).
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class FailureType(str, Enum):
    """Categorization of failure modes."""
    GEOMETRIC = "geometric"
    SEMANTIC = "semantic"
    PERCEPTION = "perception"
    LATENCY = "latency"
    UNKNOWN = "unknown"


class PerceptionQuality(str, Enum):
    """Quality rating for perception events."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MISSING = "missing"


class SymbolicObservation(BaseModel):
    """
    Represents a single symbolic observation of the environment.
    Contains detected objects with bounding boxes, classes, and attributes.
    No raw pixel data is included.
    """
    timestamp_ms: float = Field(..., description="Timestamp in milliseconds since start")
    frame_id: int = Field(..., description="Unique frame identifier")
    objects: List[Dict[str, Any]] = Field(
        ..., 
        description="List of detected objects with class, bbox, centroid, color_histogram"
    )
    scene_empty: bool = Field(False, description="True if no objects were detected")
    perception_latency_ms: float = Field(..., description="Time taken to process this frame")
    
    @field_validator('objects')
    @classmethod
    def validate_objects(cls, v):
        for obj in v:
            if 'class' not in obj:
                raise ValueError("Each object must have a 'class' field")
            if 'bbox' not in obj:
                raise ValueError("Each object must have a 'bbox' field [x, y, w, h]")
            if 'centroid' not in obj:
                raise ValueError("Each object must have a 'centroid' field [cx, cy]")
        return v


class Trajectory(BaseModel):
    """
    Represents a complete trajectory of observations for a single task attempt.
    Includes metadata about the task and the sequence of symbolic observations.
    """
    trajectory_id: str = Field(..., description="Unique identifier for the trajectory")
    task_name: str = Field(..., description="Name of the task being performed")
    task_description: str = Field(..., description="Natural language description of the task")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    observations: List[SymbolicObservation] = Field(
        ..., 
        description="Ordered list of symbolic observations"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def duration_ms(self) -> float:
        """Calculate total duration in milliseconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0


class TaskOutcome(BaseModel):
    """
    Represents the final outcome of a task execution.
    Includes success status, failure details if applicable, and performance metrics.
    """
    trajectory_id: str = Field(..., description="Reference to the trajectory")
    success: bool = Field(..., description="Whether the task was completed successfully")
    failure_type: Optional[FailureType] = None
    failure_description: Optional[str] = Field(
        None, 
        description="Detailed description of the failure if applicable"
    )
    is_latency_induced: bool = Field(
        False, 
        description="True if failure was caused by exceeding latency threshold"
    )
    steps_taken: int = Field(..., description="Number of steps/actions taken")
    total_time_ms: float = Field(..., description="Total execution time in milliseconds")
    success_rate_at_step: Optional[float] = Field(
        None, 
        description="Estimated success probability at the final step"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('failure_type')
    @classmethod
    def validate_failure_type(cls, v, info):
        data = info.data
        if data.get('success', False) and v is not None:
            raise ValueError("Failure type cannot be set if task was successful")
        if not data.get('success', False) and v is None:
            raise ValueError("Failure type must be set if task was not successful")
        return v


class PerceptionLog(BaseModel):
    """
    Detailed log of perception performance for analysis and debugging.
    Tracks latency, ground truth comparison, and object detection quality.
    """
    trajectory_id: str = Field(..., description="Reference to the trajectory")
    frame_id: int = Field(..., description="Frame identifier")
    timestamp_ms: float = Field(..., description="Frame timestamp")
    latency_ms: float = Field(..., description="Perception latency in milliseconds")
    objects_detected: int = Field(..., description="Number of objects detected")
    objects_missing_if_visible: int = Field(
        0, 
        description="Count of objects that should have been detected but weren't"
    )
    quality_rating: PerceptionQuality = Field(..., description="Overall quality rating")
    ground_truth_available: bool = Field(
        False, 
        description="Whether ground truth data was available for comparison"
    )
    precision: Optional[float] = Field(None, description="Precision score if GT available")
    recall: Optional[float] = Field(None, description="Recall score if GT available")
    notes: Optional[str] = Field(None, description="Additional notes or warnings")
    
    @field_validator('precision', 'recall')
    @classmethod
    def validate_metrics(cls, v, info):
        data = info.data
        if data.get('ground_truth_available', False):
            if v is None:
                raise ValueError("Precision/Recall must be provided if ground truth is available")
            if not 0.0 <= v <= 1.0:
                raise ValueError("Precision/Recall must be between 0 and 1")
        elif v is not None:
            raise ValueError("Precision/Recall should be None if ground truth is not available")
        return v


# Helper functions for serialization
def serialize_trajectory(trajectory: Trajectory) -> Dict[str, Any]:
    """Convert a Trajectory object to a dictionary for JSON serialization."""
    return {
        "trajectory_id": trajectory.trajectory_id,
        "task_name": trajectory.task_name,
        "task_description": trajectory.task_description,
        "start_time": trajectory.start_time.isoformat(),
        "end_time": trajectory.end_time.isoformat() if trajectory.end_time else None,
        "observations": [obs.model_dump() for obs in trajectory.observations],
        "metadata": trajectory.metadata,
        "duration_ms": trajectory.duration_ms
    }

def serialize_outcome(outcome: TaskOutcome) -> Dict[str, Any]:
    """Convert a TaskOutcome object to a dictionary for JSON serialization."""
    return outcome.model_dump()

def serialize_perception_log(log: PerceptionLog) -> Dict[str, Any]:
    """Convert a PerceptionLog object to a dictionary for JSON serialization."""
    return log.model_dump()