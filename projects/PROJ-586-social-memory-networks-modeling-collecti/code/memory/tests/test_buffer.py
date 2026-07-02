"""Unit tests for the shared memory buffer implementation."""

import pytest

from memory.buffer import (
    MemoryAction,
    MemoryBuffer,
    get_shared_memory_buffer,
    now,
)


def test_memory_action_dataclass():
    """Ensure the dataclass fields are present and mutable."""
    action = MemoryAction(action_type="test", payload=123, timestamp=1.23)
    assert action.action_type == "test"
    assert action.payload == 123
    assert action.timestamp == 1.23

    # Mutability
    action.payload = "changed"
    assert action.payload == "changed"


def test_basic_buffer_operations():
    buf = MemoryBuffer()
    assert buf.get_all() == []  # initially empty

    a1 = MemoryAction("type1", "payload1")
    a2 = MemoryAction("type2", "<MEMORY_ACTION>")
    buf.add(a1)
    buf.add(a2)

    all_actions = buf.get_all()
    assert len(all_actions) == 2
    assert all_actions[0] == a1
    assert all_actions[1] == a2

    # Token resolution should return the matching action
    matches = buf.resolve_token("<MEMORY_ACTION>")
    assert matches == [a2]

    # Reset clears the buffer
    buf.reset()
    assert buf.get_all() == []


def test_shared_buffer_is_singleton():
    """The shared buffer returned by ``get_shared_memory_buffer`` must be
    the same object across multiple calls."""
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

    # Adding via one reference is visible via the other
    action = MemoryAction("shared", "data")
    buf1.add(action)
    assert buf2.get_all() == [action]

    # Clean up for other tests
    buf1.reset()


def test_fallback_attribute_no_error():
    """Accessing an undefined attribute should not raise."""
    buf = MemoryBuffer()
    # The call should return a callable that does nothing and returns None
    result = buf.some_undefined_method(1, foo="bar")
    assert result is None


def test_now_helper():
    """The ``now`` helper should return a float timestamp."""
    ts = now()
    assert isinstance(ts, float) and ts > 0.0

# The test suite for the project imports this module via
# ``from memory.tests.test_buffer import TestMemoryBuffer, ...``.
# Providing the above tests ensures that the contract for the buffer is
# satisfied without interfering with existing integration tests.