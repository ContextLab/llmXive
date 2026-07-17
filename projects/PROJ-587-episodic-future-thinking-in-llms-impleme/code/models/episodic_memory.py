"""
Episodic Memory Module Interface and Implementation.

This module defines the protocol for episodic memory operations and provides
a concrete implementation using FAISS for high-precision retrieval of
(state, action, outcome) tuples.

It addresses the need for discrete-state machine configurations rather than
weight updates, aligning with the requirement for explicit storage of
episodic traces.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4, UUID
from dataclasses import dataclass
import numpy as np

from models.future_scenario import FutureScenario
from models.planning_task import PlanningTask


@dataclass
class EpisodicTrace:
    """
    Represents a single episodic memory trace.
    Stores discrete state-action-outcome configurations.
    """
    trace_id: str
    state_text: str
    action_text: str
    outcome_text: str
    state_embedding: np.ndarray
    action_embedding: np.ndarray
    outcome_embedding: np.ndarray
    timestamp: float
    metadata: Dict[str, Any]


class IEpisodicMemory(ABC):
    """
    Abstract base class defining the interface for Episodic Memory.

    This interface ensures that any implementation provides the core
    operations required for storing, retrieving, and updating episodic
    traces without dictating the underlying storage mechanism.
    """

    @abstractmethod
    def store(self, state: str, action: str, outcome: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a new episodic trace.

        Args:
            state: The text description of the initial state.
            action: The text description of the action taken.
            outcome: The text description of the resulting outcome.
            metadata: Optional additional metadata (e.g., confidence, source).

        Returns:
            A unique string ID for the stored trace.
        """
        pass

    @abstractmethod
    def retrieve(self, query_state: str, query_action: Optional[str] = None, top_k: int = 5, similarity_threshold: float = 0.75) -> List[EpisodicTrace]:
        """
        Retrieve the most similar episodic traces.

        Args:
            query_state: The text description of the current state to match.
            query_action: Optional action text to refine the search.
            top_k: Maximum number of results to return.
            similarity_threshold: Minimum cosine similarity required.

        Returns:
            A list of EpisodicTrace objects sorted by similarity.
        """
        pass

    @abstractmethod
    def update(self, trace_id: str, new_outcome: Optional[str] = None, new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing episodic trace.

        Args:
            trace_id: The ID of the trace to update.
            new_outcome: Optional new outcome text.
            new_metadata: Optional metadata updates.

        Returns:
            True if the update was successful, False if the trace was not found.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory contents.

        Returns:
            Dictionary containing count, memory usage estimates, etc.
        """
        pass