"""Unit tests for logger batch context injection (T005c)."""
import pytest
from simulation.logger import setup_logger, inject_batch_context

def test_inject_batch_context_includes_batch_id():
    """Assert that the log output contains the batch ID after injection."""
    # Setup a logger
    logger = setup_logger("test_batch_context")

    # Verify initial state has no batch_id
    logger.log("initial_action")
    initial_entry = logger.entries[-1]
    assert initial_entry.batch_id is None

    # Inject context
    batch_id = "batch_123"
    seed = 42
    inject_batch_context(logger, batch_id, seed)

    # Log an action after injection
    logger.log("action_after_injection")
    entry = logger.entries[-1]

    # Assert the batch_id and seed are present in the log entry
    assert entry.batch_id == batch_id, f"Expected batch_id {batch_id}, got {entry.batch_id}"
    assert entry.seed == seed, f"Expected seed {seed}, got {entry.seed}"

def test_inject_batch_context_persists_across_logs():
    """Assert that the batch context persists for multiple log entries."""
    logger = setup_logger("test_persistence")
    inject_batch_context(logger, "persistent_batch", 99)

    logger.log("first")
    logger.log("second")
    logger.log("third")

    for entry in logger.entries:
        assert entry.batch_id == "persistent_batch"
        assert entry.seed == 99
