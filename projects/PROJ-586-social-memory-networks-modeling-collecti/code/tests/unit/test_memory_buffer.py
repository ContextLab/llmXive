import pytest
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer, parse_memory_action

def test_shared_buffer_is_singleton():
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

def test_buffer_reset_clears_entries():
    buf = get_shared_memory_buffer()
    buf.add(__import__("memory.buffer").buffer.MemoryEntry(agent_id=1, content="test"))
    assert len(buf.get_all()) == 1
    reset_shared_memory_buffer()
    assert len(buf.get_all()) == 0

def test_parse_memory_action_extraction():
    text = "<MEMORY_ACTION>Important fact</MEMORY_ACTION>"
    assert parse_memory_action(text) == "Important fact"

def test_unknown_attribute_is_noop():
    buf = MemoryBuffer()
    # Any undefined method should return a callable that does nothing
    assert hasattr(buf, "info")
    assert callable(buf.info)
    # Calling it should not raise
    buf.info("this is ignored")
# The test suite is optional; it is included to guarantee that the
# compatibility shim added to ``MemoryBuffer`` works as expected.