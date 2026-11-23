"""
Explainable Interface Renderer for the XAI Accessibility Study.

This module implements the `ExplainableInterface` class, which renders a
traditional gene regulation task interface augmented with XAI overlays.
It adheres to the schema defined in `contracts/session.schema.yaml` for
data logging and integrates with the `XAIOverlayGenerator` for dynamic
explanation rendering.

Key Features:
- Renders UI elements (genes, regulators) with visual overlays.
- Tracks user interaction time for explanation engagement.
- Provides a deterministic state for simulation and real-time interaction.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import random

from utils.logger import get_logger
from utils.seed import set_seed, seeded_generator
from simulator.xai_generator import XAIOverlayGenerator

logger = get_logger(__name__)

@dataclass
class XAIOverlay:
    """Represents a single XAI overlay element."""
    element_id: str
    type: str  # e.g., 'heatmap', 'feature_importance', 'counterfactual'
    intensity: float  # 0.0 to 1.0
    explanation_text: str
    position: Dict[str, float]  # {'x': 0.5, 'y': 0.5} relative to element

@dataclass
class ExplainableInterfaceState:
    """Tracks the state of the explainable interface during a session."""
    session_id: str
    participant_id: str
    interface_type: str = "explainable"
    sequence: str = "traditional_explainable"
    current_task_id: int = 0
    overlays_active: List[XAIOverlay] = None
    explanation_engagement_start: Optional[datetime] = None
    explanation_engagement_end: Optional[datetime] = None
    explanation_engagement_time_seconds: float = 0.0
    total_interaction_time_seconds: float = 0.0
    errors: List[Dict[str, Any]] = None
    completed: bool = False

    def __post_init__(self):
        if self.overlays_active is None:
            self.overlays_active = []
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dictionary for logging."""
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "interface_type": self.interface_type,
            "sequence": self.sequence,
            "current_task_id": self.current_task_id,
            "overlays_active": [asdict(o) for o in self.overlays_active],
            "explanation_engagement_time_seconds": self.explanation_engagement_time_seconds,
            "total_interaction_time_seconds": self.total_interaction_time_seconds,
            "errors": self.errors,
            "completed": self.completed
        }

class ExplainableInterface:
    """
    Renders the Explainable Interface with XAI overlays.

    This class manages the rendering logic for the explainable variant of the
    gene regulation task. It integrates with the XAI generator to produce
    deterministic overlays based on task difficulty and tracks user engagement
    with these explanations.
    """

    def __init__(self, session_id: str, participant_id: str, seed: int = 42):
        """
        Initialize the Explainable Interface.

        Args:
            session_id: Unique identifier for the session.
            participant_id: Unique identifier for the participant.
            seed: Random seed for deterministic behavior in simulation.
        """
        self.session_id = session_id
        self.participant_id = participant_id
        self.seed = seed
        set_seed(seed)
        
        self.state = ExplainableInterfaceState(
            session_id=session_id,
            participant_id=participant_id,
            interface_type="explainable",
            sequence="explainable_traditional" # Default, can be overridden
        )
        
        self.xai_generator = XAIOverlayGenerator(seed=seed)
        self.logger = get_logger(__name__)

    def render_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render a task with XAI overlays.

        Args:
            task_config: Dictionary containing task parameters (difficulty, genes, etc.)

        Returns:
            Dictionary containing the rendered UI state and active overlays.
        """
        if not task_config:
            raise ValueError("Task configuration cannot be empty.")

        self.state.current_task_id = task_config.get("task_id", 0)
        
        # Generate XAI overlays based on task difficulty
        overlays = self.xai_generator.generate_overlays(task_config)
        self.state.overlays_active = [XAIOverlay(**o) if isinstance(o, dict) else o for o in overlays]
        
        # Log engagement start
        self.state.explanation_engagement_start = datetime.now()
        
        return {
            "task_id": self.state.current_task_id,
            "interface_type": "explainable",
            "elements": task_config.get("elements", []),
            "overlays": [asdict(o) for o in self.state.overlays_active],
            "status": "active"
        }

    def record_interaction(self, action: str, details: Dict[str, Any] = None):
        """
        Record a user interaction.

        Args:
            action: The type of action (e.g., 'click', 'hover', 'submit').
            details: Additional details about the action.
        """
        if details is None:
            details = {}
        
        timestamp = datetime.now()
        
        # Calculate engagement time if an explanation was viewed
        if self.state.explanation_engagement_start and action in ['submit', 'next_task']:
            self.state.explanation_engagement_end = timestamp
            engagement_duration = (self.state.explanation_engagement_end - self.state.explanation_engagement_start).total_seconds()
            self.state.explanation_engagement_time_seconds += engagement_duration
            self.state.explanation_engagement_start = None
            self.state.explanation_engagement_end = None

        interaction_log = {
            "timestamp": timestamp.isoformat(),
            "action": action,
            "details": details,
            "task_id": self.state.current_task_id
        }
        
        self.state.errors.append(interaction_log) # Storing interactions as errors for now to match schema structure if needed, or separate list
        self.logger.debug(f"Interaction recorded: {action} for task {self.state.current_task_id}")

    def record_error(self, error_type: str, message: str):
        """
        Record a user error.

        Args:
            error_type: Type of error (e.g., 'timeout', 'invalid_input').
            message: Description of the error.
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "task_id": self.state.current_task_id
        }
        self.state.errors.append(error_entry)
        self.logger.warning(f"Error recorded: {error_type} - {message}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current metrics for the session.

        Returns:
            Dictionary containing session metrics.
        """
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "interface_type": "explainable",
            "explanation_engagement_time_seconds": self.state.explanation_engagement_time_seconds,
            "total_interaction_time_seconds": self.state.total_interaction_time_seconds,
            "error_count": len(self.state.errors),
            "completed": self.state.completed
        }

    def complete_session(self):
        """Mark the session as complete."""
        self.state.completed = True
        self.logger.info(f"Session {self.session_id} completed for participant {self.participant_id}")

def main():
    """
    Main entry point for testing the Explainable Interface.
    """
    logger.info("Running Explainable Interface test.")
    
    # Initialize interface
    interface = ExplainableInterface(
        session_id="test_session_001",
        participant_id="test_participant_001",
        seed=42
    )
    
    # Simulate a task
    task_config = {
        "task_id": 1,
        "difficulty": 0.7,
        "elements": [
            {"id": "gene_A", "type": "regulator"},
            {"id": "gene_B", "type": "target"}
        ]
    }
    
    rendered = interface.render_task(task_config)
    print(f"Rendered Task: {json.dumps(rendered, indent=2)}")
    
    # Simulate interaction
    interface.record_interaction("submit", {"result": "success"})
    
    # Get metrics
    metrics = interface.get_metrics()
    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    
    interface.complete_session()

if __name__ == "__main__":
    main()