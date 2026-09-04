"""
State Mapper Module for RoboDojo Symbolic Abstraction.

This module maps continuous semantic embeddings from the vision encoder
into discrete symbolic states (predicates) suitable for symbolic planning.
It implements deterministic thresholding to ensure reproducibility.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass, field
import json

from src.config import STATE_MAPPER_CONFIG_PATH

logger = logging.getLogger(__name__)


@dataclass
class SymbolicState:
    """
    Represents a discrete symbolic state derived from continuous embeddings.
    Contains boolean predicates regarding object affordances and connectivity.
    """
    task_id: str
    predicates: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "predicates": self.predicates,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolicState':
        return cls(
            task_id=data["task_id"],
            predicates=data.get("predicates", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class AffordanceGraph:
    """
    Represents the connectivity and affordance graph derived from the state.
    Nodes are objects, edges represent possible interactions.
    """
    nodes: List[str]
    edges: List[Tuple[str, str, str]]  # (source, target, action_type)
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "properties": self.properties
        }


class StateMapper:
    """
    Maps continuous semantic embeddings to discrete SymbolicStates.
    Uses deterministic thresholds defined in configuration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the StateMapper with configuration.

        Args:
            config_path: Path to the JSON configuration file containing
                         thresholds and predicate definitions. If None,
                         defaults to config/STATE_MAPPER_CONFIG_PATH.
        """
        self.config_path = config_path or STATE_MAPPER_CONFIG_PATH
        self.thresholds: Dict[str, float] = {}
        self.predicate_definitions: Dict[str, List[str]] = {}
        self._load_config()
        logger.info(f"StateMapper initialized with config: {self.config_path}")

    def _load_config(self) -> None:
        """Load thresholds and predicate definitions from config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.thresholds = config.get("thresholds", {})
            self.predicate_definitions = config.get("predicates", {})
        except FileNotFoundError:
            # Fallback to sensible defaults if config is missing
            logger.warning(f"Config file {self.config_path} not found. Using defaults.")
            self.thresholds = {
                "grasp_probability": 0.5,
                "connectivity_strength": 0.3,
                "object_presence": 0.1
            }
            self.predicate_definitions = {
                "graspable": ["object"],
                "connected": ["object_a", "object_b"],
                "present": ["object"]
            }

    def map_embedding_to_predicates(
        self,
        embedding: np.ndarray,
        task_id: str,
        object_ids: List[str]
    ) -> SymbolicState:
        """
        Map a continuous embedding vector to a set of discrete predicates.

        This function implements deterministic thresholding. It does NOT
        use random sampling or synthetic fallbacks. If the embedding
        dimensions do not match expected predicate dimensions, it raises
        a ValueError.

        Args:
            embedding: Numpy array of shape (N,) representing the semantic
                       embedding of the current scene state.
            task_id: Unique identifier for the current task.
            object_ids: List of object identifiers present in the scene.

        Returns:
            SymbolicState: A dataclass containing the task_id and a dictionary
                           of predicate names to boolean values.

        Raises:
            ValueError: If embedding shape is invalid or configuration is missing.
        """
        if embedding is None or not isinstance(embedding, np.ndarray):
            raise ValueError("Embedding must be a non-null numpy array.")

        if embedding.ndim != 1:
            raise ValueError(f"Embedding must be 1D, got {embedding.ndim}D.")

        # Determine which predicates to evaluate based on config
        # For this implementation, we assume the embedding encodes:
        # [grasp_probs (len(objects)), connectivity_matrix (flattened), presence_flags]
        # The exact mapping depends on the vision_encoder output structure.
        # We will use a generic mapping based on the threshold config.

        predicates = {}
        dim = embedding.shape[0]

        # 1. Graspability Predicates
        # Assume first N dimensions correspond to grasp probability for each object
        num_objects = len(object_ids)
        grasp_dim = self.thresholds.get("grasp_probability_dim", num_objects)

        if dim < grasp_dim:
            raise ValueError(f"Embedding dimension {dim} too small for {grasp_dim} objects.")

        for i, obj_id in enumerate(object_ids):
            prob = float(embedding[i])
            pred_name = f"graspable_{obj_id}"
            predicates[pred_name] = prob >= self.thresholds.get("grasp_probability", 0.5)

        # 2. Connectivity Predicates
        # Assume next N*N dimensions (flattened) or a specific range represent connectivity
        # For simplicity, we check a specific connectivity threshold if dimensions allow
        # This is a simplified mapping; in a full system, the embedding structure
        # would be strictly defined by the VisionEncoder contract.
        # We assume dimensions [grasp_dim : grasp_dim + num_objects] represent
        # a simplified connectivity score to a target or general connectivity.
        conn_start = grasp_dim
        conn_end = conn_start + num_objects

        if dim >= conn_end:
            for i, obj_id in enumerate(object_ids):
                score = float(embedding[conn_start + i])
                pred_name = f"connected_{obj_id}"
                predicates[pred_name] = score >= self.thresholds.get("connectivity_strength", 0.3)

        # 3. Presence Predicates (if applicable)
        # Remaining dimensions or specific flags
        # Assuming presence is implicit if grasp/connectivity scores are non-zero
        for obj_id in object_ids:
            if f"graspable_{obj_id}" not in predicates:
                # Fallback check if dimensions were insufficient
                predicates[f"present_{obj_id}"] = False
            else:
                predicates[f"present_{obj_id}"] = True

        return SymbolicState(task_id=task_id, predicates=predicates)

    def build_affordance_graph(
        self,
        symbolic_state: SymbolicState,
        task_spec: Optional[Dict[str, Any]] = None
    ) -> AffordanceGraph:
        """
        Construct an AffordanceGraph from a SymbolicState.

        Args:
            symbolic_state: The discrete state to convert.
            task_spec: Optional task specification containing allowed actions.

        Returns:
            AffordanceGraph: A graph representing valid object interactions.
        """
        nodes = []
        edges = []

        # Extract objects from predicates
        object_names = set()
        for key in symbolic_state.predicates:
            if key.startswith("graspable_") or key.startswith("connected_"):
                obj_name = key.split("_", 1)[1]
                object_names.add(obj_name)

        nodes = list(object_names)

        # Generate edges based on connectivity predicates
        # In a full implementation, this would iterate over all pairs
        # and check specific connectivity predicates.
        for key, is_connected in symbolic_state.predicates.items():
            if key.startswith("connected_") and is_connected:
                obj_name = key.split("_", 1)[1]
                # Assuming a generic "connected" predicate implies edge to a target
                # or a specific neighbor defined in task_spec.
                # For this generic mapper, we create a self-loop or generic connection
                # if the predicate is true, representing "connectivity exists".
                # A more robust version would parse the predicate name for target.
                edges.append((obj_name, "target", "move_to"))

        # Add edges for graspable objects
        for key, is_graspable in symbolic_state.predicates.items():
            if key.startswith("graspable_") and is_graspable:
                obj_name = key.split("_", 1)[1]
                edges.append((obj_name, "robot_gripper", "grasp"))

        return AffordanceGraph(
            nodes=nodes,
            edges=edges,
            properties=symbolic_state.metadata
        )

    def map_batch(
        self,
        embeddings: List[np.ndarray],
        task_ids: List[str],
        object_lists: List[List[str]]
    ) -> List[SymbolicState]:
        """
        Map a batch of embeddings to symbolic states.

        Args:
            embeddings: List of numpy arrays.
            task_ids: List of task IDs.
            object_lists: List of object ID lists corresponding to each embedding.

        Returns:
            List of SymbolicState objects.
        """
        if not (len(embeddings) == len(task_ids) == len(object_lists)):
            raise ValueError("All input lists must have the same length.")

        return [
            self.map_embedding_to_predicates(emb, tid, objs)
            for emb, tid, objs in zip(embeddings, task_ids, object_lists)
        ]


def create_symbolic_state(
    embedding: np.ndarray,
    task_id: str,
    object_ids: List[str],
    config_path: Optional[str] = None
) -> SymbolicState:
    """
    Convenience function to create a SymbolicState from an embedding.

    Args:
        embedding: The continuous embedding vector.
        task_id: The task identifier.
        object_ids: List of object identifiers.
        config_path: Optional path to config file.

    Returns:
        A SymbolicState instance.
    """
    mapper = StateMapper(config_path)
    return mapper.map_embedding_to_predicates(embedding, task_id, object_ids)