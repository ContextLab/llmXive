"""
Contract for Trajectory Logs.

This module defines the expected structure (contract) for trajectory logs
used in the agentic pipeline. It aligns with
specs/001-llmxive-interleave-structure-vs-modality/contracts/trajectory.schema.yaml.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class TrajectoryContract:
    """
    Contract defining the structure of a Trajectory Log.
    
    Expected fields:
    - steps: List of step dictionaries (timestamp, agent, action, input, output, score)
    - session_id: Unique identifier for the session
    - metadata: Run configuration details
    """
    
    REQUIRED_KEYS = ["steps", "session_id"]
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> None:
        """
        Validate that the input data conforms to the Trajectory Contract.
        
        Args:
            data: The dictionary to validate.
            
        Raises:
            ValueError: If the data does not conform to the contract.
        """
        if not isinstance(data, dict):
            raise ValueError("Trajectory data must be a dictionary.")
        
        for key in TrajectoryContract.REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"Missing required key in Trajectory Contract: '{key}'")
        
        if not isinstance(data["steps"], list):
            raise ValueError("'steps' must be a list.")
        
        if not isinstance(data["session_id"], str):
            raise ValueError("'session_id' must be a string.")
        
        # Validate step structure
        for i, step in enumerate(data["steps"]):
            if not isinstance(step, dict):
                raise ValueError(f"Step at index {i} must be a dictionary.")
            required_step_keys = ["agent", "action", "timestamp"]
            for key in required_step_keys:
                if key not in step:
                    raise ValueError(f"Step at index {i} missing key: '{key}'")
    
    @staticmethod
    def get_example() -> Dict[str, Any]:
        """Return an example conforming to the contract."""
        return {
            "session_id": "session_001",
            "steps": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": "planner",
                    "action": "generate_intent",
                    "input": {"prompt": "A cat on a mat"},
                    "output": {"intent": "Describe scene"},
                    "score": 0.9
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": "generator",
                    "action": "construct_scene",
                    "input": {"intent": "Describe scene"},
                    "output": {"objects": []},
                    "score": 0.85
                }
            ],
            "metadata": {"config": "default"}
        }
