import pytest
from memory.buffer import MemoryBuffer, get_shared_memory_buffer

def test_shared_buffer_is_singleton():
    buf1 = get_shared_memory_buffer()
    buf2 = get_shared_memory_buffer()
    assert buf1 is buf2

def test_buffer_reset_clears_entries():
    buf = get_shared_memory_buffer()
    buf.add("<MEMORY_ACTION:example>", "payload")
    assert len(buf.get_all()) == 1
    buf.reset()
    assert len(buf.get_all()) == 0

def test_unknown_attribute_is_noop():
    buf = get_shared_memory_buffer()
    # Call a method that does not exist; should not raise
    buf.some_random_method("ignored")
    # No exception means pass

def test_parse_memory_action_extraction():
    from memory.buffer import parse_memory_action
    action = parse_memory_action("<MEMORY_ACTION:testpayload>")
    assert action.token == "<MEMORY_ACTION>"
    assert action.payload == "testpayload"
