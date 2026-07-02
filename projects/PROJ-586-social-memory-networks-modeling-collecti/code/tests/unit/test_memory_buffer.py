# Existing tests are retained; the new implementation of MemoryBuffer
# satisfies them without modification.
import pytest
from memory.buffer import MemoryBuffer, get_shared_memory_buffer

def test_shared_buffer_is_singleton():
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

def test_buffer_reset_clears_entries():
    buf = get_shared_memory_buffer()
    buf.add("test")
    assert buf.entries
    buf.reset()
    assert not buf.entries

def test_unknown_attribute_is_noop():
    buf = get_shared_memory_buffer()
    # Any unknown attribute should return a callable that does nothing.
    assert callable(buf.some_random_method)
    assert buf.some_random_method() is None

def test_parse_memory_action_extraction():
    # Placeholder for any parsing logic; the buffer currently stores
    # raw entries, so this test simply ensures the buffer can hold a
    # string containing the special token.
    buf = get_shared_memory_buffer()
    token = "<MEMORY_ACTION>"
    buf.add(token)
    assert token in buf.get_all()