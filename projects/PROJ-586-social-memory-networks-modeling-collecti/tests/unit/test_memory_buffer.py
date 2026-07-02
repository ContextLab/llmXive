import pytest
from memory.buffer import get_shared_memory_buffer

def test_shared_buffer_is_singleton():
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

def test_buffer_reset_clears_entries():
    buf = get_shared_memory_buffer()
    buf.reset()
    assert len(buf.get_all()) == 0

def test_unknown_attribute_is_noop():
    buf = get_shared_memory_buffer()
    # Call a method that does not exist; should not raise.
    result = buf.some_random_method(1, key="value")
    assert result is None
