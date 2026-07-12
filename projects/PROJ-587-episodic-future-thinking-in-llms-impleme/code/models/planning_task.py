"""
Pydantic models for Episodic Future Thinking planning tasks.

This module defines the core data structures representing a planning problem
within the episodic memory framework, including dependencies on past experiences.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4
from datetime import datetime

class PlanningTask(BaseModel):
    """
    Represents a specific planning task to be solved using episodic future thinking.

    Attributes:
        task_id: Unique identifier for the task.
        initial_state: Description of the starting configuration or state.
        goal_state: Description of the desired target configuration.
        required_steps: Ordered list of high-level actions or sub-goals required.
        episodic_dependencies: List of task IDs from the episodic memory that
                             are relevant to solving this current task.
        created_at: Timestamp of creation.
    """
    
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    initial_state: str = Field(..., description="Description of the initial state")
    goal_state: str = Field(..., description="Description of the goal state")
    required_steps: List[str] = Field(default_factory=list, description="List of required steps")
    episodic_dependencies: List[str] = Field(
        default_factory=list, 
        description="List of IDs of episodic memories relevant to this task"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('required_steps')
    @classmethod
    def validate_steps_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("required_steps cannot be empty for a valid planning task")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "initial_state": self.initial_state,
            "goal_state": self.goal_state,
            "required_steps": self.required_steps,
            "episodic_dependencies": self.episodic_dependencies,
            "created_at": self.created_at.isoformat()
        }