"""
Unit tests for the Episodic Memory module (T010b).

This test verifies that the EpisodicMemory implementation (or a mock adhering
to the IEpisodicMemory protocol) correctly returns a valid UUID string upon
storing an episode.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

# Import the protocol defined in T010a
from models.episodic_memory import IEpisodicMemory, EpisodicTrace
from models.future_scenario import FutureScenario


class MockEpisodicMemory(IEpisodicMemory):
    """
    A mock implementation of IEpisodicMemory for unit testing T010b.
    This class simulates the storage behavior to verify the return type
    without requiring a full FAISS index setup or real data.
    """

    def __init__(self):
        self._store = {}
        self._counter = 0

    def store(self, trace: EpisodicTrace) -> str:
        """
        Stores a trace and returns a valid episode ID.
        """
        episode_id = str(uuid.uuid4())
        self._store[episode_id] = trace
        return episode_id

    def retrieve(self, query_vector: "np.ndarray", k: int = 5):
        """Mock retrieval."""
        return []

    def update(self, episode_id: str, trace: EpisodicTrace):
        """Mock update."""
        if episode_id in self._store:
            self._store[episode_id] = trace

    def get_count(self) -> int:
        return len(self._store)


def test_store_returns_id():
    """
    T010b: Assert that store() returns a valid episode ID (UUID string).

    This test uses the MockEpisodicMemory to verify the contract defined
    in IEpisodicMemory without external dependencies.
    """
    # Arrange
    memory = MockEpisodicMemory()
    
    # Create a minimal valid EpisodicTrace for the test
    # We assume EpisodicTrace accepts standard fields; if it requires specific
    # Pydantic validation, we construct it with valid dummy data.
    trace = EpisodicTrace(
        state="agent is in the kitchen",
        action="move north",
        outcome="agent enters the living room",
        timestamp="2023-10-27T10:00:00Z"
    )

    # Act
    result_id = memory.store(trace)

    # Assert
    # 1. Check that the result is a string
    assert isinstance(result_id, str), f"Expected string, got {type(result_id)}"
    
    # 2. Check that the string is a valid UUID
    try:
        uuid_obj = uuid.UUID(result_id)
        assert uuid_obj is not None, "Parsed UUID is None"
    except ValueError as e:
        pytest.fail(f"store() returned a string that is not a valid UUID: {result_id}. Error: {e}")

    # 3. Check that the ID is unique (store another and ensure different)
    trace2 = EpisodicTrace(
        state="agent is in the hallway",
        action="move east",
        outcome="agent enters the bedroom",
        timestamp="2023-10-27T10:05:00Z"
    )
    result_id_2 = memory.store(trace2)
    assert result_id != result_id_2, "store() must return unique IDs for distinct calls"

    # 4. Verify the ID exists in the internal store
    assert result_id in memory._store, "Returned ID was not stored internally"