"""Unit tests for the shared memory buffer.

The tests verify that the buffer behaves as a singleton, that ``reset``
clears entries, and that unknown attribute accesses are harmless no‑ops.
"""
import pytest
from memory.buffer import (
    MemoryBuffer,
    get_shared_memory_buffer,
    reset_shared_memory_buffer,
    parse_memory_action,
)

def test_shared_buffer_is_singleton():
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

def test_buffer_reset_clears_entries():
    buf = get_shared_memory_buffer()
    buf.store("key", "value")
    assert len(buf) == 1
    buf.reset()
    assert len(buf) == 0

def test_unknown_attribute_is_noop():
    buf = get_shared_memory_buffer()
    # Should not raise AttributeError
    buf.info("this is a test")
    buf.debug("another test")
    # No return value expected
    assert True

def test_parse_memory_action_extraction():
    found, action = parse_memory_action("do something <MEMORY_ACTION:store>")
    assert found is True
    assert action == "store"

    found, action = parse_memory_action("no token here")
    assert found is False
    assert action is None