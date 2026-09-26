import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
import numpy as np

from src.config import POSE_DEV_TOLERANCE_CM, ORIENT_DEV_TOLERANCE_DEG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SymbolicState:
    """
    Represents the discrete symbolic abstraction of a robot's state.
    
    Attributes:
        state_id: Unique identifier for this state instance.
        predicates: List of string predicates describing the current state (e.g., "object_on_table").
        affordances: Dictionary mapping objects to their possible actions (e.g., {"box": ["lift", "push"]}).
        connectivity: List of reachable neighboring state IDs.
        replan_support: Boolean flag indicating if the task metadata allows for replanning from this state.
    """
    state_id: str
    predicates: List[str] = field(default_factory=list)
    affordances: Dict[str, List[str]] = field(default_factory=dict)
    connectivity: List[str] = field(default_factory=list)
    replan_support: bool = False

@dataclass
class AffordanceGraph:
    """Graph structure representing state transitions and affordances."""
    nodes: Dict[str, SymbolicState] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)

class StateMapper:
    """
    Maps continuous embeddings and task metadata to discrete SymbolicStates.
    
    This class handles the abstraction of raw sensor data and task specifications
    into a form usable by the symbolic planner, explicitly filtering out continuous
    physics dynamics as per the design constraints.
    """
    
    def __init__(self, threshold_pose: float = POSE_DEV_TOLERANCE_CM,
                 threshold_orient: float = ORIENT_DEV_TOLERANCE_DEG):
        self.threshold_pose = threshold_pose
        self.threshold_orient = threshold_orient
        logger.info(f"StateMapper initialized with pose threshold {self.threshold_pose}cm and orient threshold {self.threshold_orient}deg")

    def map_embedding_to_predicates(self, embedding: np.ndarray, task_metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Maps a continuous embedding vector to a list of discrete predicates.
        
        Args:
            embedding: Numpy array representing the semantic embedding.
            task_metadata: Optional dictionary containing task-specific metadata.
            
        Returns:
            List of string predicates.
        """
        # Placeholder logic for predicate extraction based on embedding thresholds
        # In a real implementation, this would involve clustering or thresholding
        # specific dimensions of the embedding space.
        predicates = []
        
        if embedding is not None and len(embedding) > 0:
            # Example heuristic: if mean embedding value > 0.5, assume 'active' state
            if np.mean(embedding) > 0.5:
                predicates.append("state_active")
            else:
                predicates.append("state_idle")
        
        # Add task-specific predicates if metadata is provided
        if task_metadata:
            if task_metadata.get("task_type") == "pick_and_place":
                predicates.append("task_pick_and_place")
            elif task_metadata.get("task_type") == "assembly":
                predicates.append("task_assembly")
                
        return predicates

    def map_to_affordances(self, task_metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Derives affordances from task metadata.
        
        Args:
            task_metadata: Dictionary containing task specifications.
            
        Returns:
            Dictionary mapping objects to their allowed actions.
        """
        affordances = {}
        if not task_metadata:
            return affordances
        
        # Example mapping based on metadata
        objects = task_metadata.get("objects", [])
        for obj in objects:
            obj_name = obj.get("name", "unknown")
            affordances[obj_name] = obj.get("allowed_actions", ["move"])
            
        return affordances

    def determine_connectivity(self, current_state_id: str, possible_next_states: List[str]) -> List[str]:
        """
        Determines the list of reachable neighboring state IDs.
        
        Args:
            current_state_id: ID of the current state.
            possible_next_states: List of candidate next state IDs.
            
        Returns:
            List of valid connected state IDs.
        """
        # In a full implementation, this would validate transitions against the graph
        return possible_next_states

    def create_symbolic_state(self, 
                              state_id: str, 
                              embedding: np.ndarray, 
                              task_metadata: Dict[str, Any],
                              possible_next_states: Optional[List[str]] = None) -> SymbolicState:
        """
        Creates a complete SymbolicState object from inputs.
        
        This method orchestrates the mapping of continuous data to discrete symbols
        and explicitly sets the `replan_support` flag based on task metadata.
        
        Args:
            state_id: Unique ID for the state.
            embedding: Continuous embedding vector.
            task_metadata: Dictionary containing task specifications and metadata.
            possible_next_states: Optional list of candidate next state IDs.
            
        Returns:
            A fully populated SymbolicState object.
        """
        # Map embedding to predicates
        predicates = self.map_embedding_to_predicates(embedding, task_metadata)
        
        # Map metadata to affordances
        affordances = self.map_to_affordances(task_metadata)
        
        # Determine connectivity
        connectivity = self.determine_connectivity(state_id, possible_next_states or [])
        
        # --- T046 Implementation: Populate replan_support based on task metadata ---
        # Check for explicit flag in metadata, default to False if not present
        # Common keys might be 'replan_allowed', 'supports_replanning', or nested in 'constraints'
        replan_support = False
        
        if task_metadata:
            # Check direct keys
            if "replan_support" in task_metadata:
                replan_support = bool(task_metadata["replan_support"])
            elif "replan_allowed" in task_metadata:
                replan_support = bool(task_metadata["replan_allowed"])
            elif "supports_replanning" in task_metadata:
                replan_support = bool(task_metadata["supports_replanning"])
            
            # Check nested constraints if direct keys are missing
            elif "constraints" in task_metadata:
                constraints = task_metadata["constraints"]
                if isinstance(constraints, dict):
                    if "replan_support" in constraints:
                        replan_support = bool(constraints["replan_support"])
                    elif "replan_allowed" in constraints:
                        replan_support = bool(constraints["replan_allowed"])
        
        logger.debug(f"State {state_id}: replan_support determined as {replan_support} from metadata keys: {list(task_metadata.keys()) if task_metadata else []}")
        
        return SymbolicState(
            state_id=state_id,
            predicates=predicates,
            affordances=affordances,
            connectivity=connectivity,
            replan_support=replan_support
        )

def create_symbolic_state(state_id: str, 
                          embedding: np.ndarray, 
                          task_metadata: Dict[str, Any],
                          possible_next_states: Optional[List[str]] = None) -> SymbolicState:
    """
    Convenience function to create a SymbolicState using the default StateMapper.
    
    Args:
        state_id: Unique ID for the state.
        embedding: Continuous embedding vector.
        task_metadata: Dictionary containing task specifications.
        possible_next_states: Optional list of candidate next state IDs.
        
    Returns:
        SymbolicState object with replan_support populated from metadata.
    """
    mapper = StateMapper()
    return mapper.create_symbolic_state(state_id, embedding, task_metadata, possible_next_states)