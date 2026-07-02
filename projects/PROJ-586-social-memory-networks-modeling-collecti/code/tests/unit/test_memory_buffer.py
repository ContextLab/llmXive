"""
Unit tests for the MemoryBuffer implementation.
"""
import pytest
import time
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer, parse_memory_action

def test_shared_buffer_is_singleton():
    """Test that get_shared_memory_buffer returns the same instance."""
    buffer1 = get_shared_memory_buffer()
    buffer2 = get_shared_memory_buffer()
    assert buffer1 is buffer2

def test_buffer_reset_clears_entries():
    """Test that reset() clears all entries."""
    # Reset before test
    reset_shared_memory_buffer()
    
    buffer = get_shared_memory_buffer()
    
    # Add some entries
    buffer.store("agent1", "test content 1")
    buffer.store("agent2", "test content 2")
    
    assert len(buffer) == 2
    
    # Reset
    buffer.reset()
    
    assert len(buffer) == 0
    assert buffer.get_entries() == []

def test_parse_memory_action_extraction():
    """Test parsing of <MEMORY_ACTION> tokens."""
    # Valid token
    text = "Here is a <MEMORY_ACTION:store:important data> in the text."
    result = parse_memory_action(text)
    
    assert result is not None
    assert result['action'] == 'store'
    assert result['content'] == 'important data'
    assert result['raw'] == '<MEMORY_ACTION:store:important data>'
    
    # Invalid token
    invalid_text = "No token here or <invalid:format>"
    result = parse_memory_action(invalid_text)
    assert result is None

def test_unknown_attribute_is_noop():
    """Test that unknown attributes return a no-op callable."""
    buffer = MemoryBuffer()
    
    # Should not raise AttributeError
    noop_func = buffer.unknown_method
    assert callable(noop_func)
    
    # Calling it should return None
    result = noop_func("arg1", arg2="value")
    assert result is None

def test_store_and_retrieve():
    """Test basic store and retrieve operations."""
    reset_shared_memory_buffer()
    buffer = get_shared_memory_buffer()
    
    # Store entries
    entry1 = buffer.store("agent1", "content1", {"key": "value1"})
    entry2 = buffer.store("agent2", "content2")
    
    assert len(buffer) == 2
    assert entry1.action == 'store'
    assert entry1.agent_id == "agent1"
    
    # Retrieve all
    results = buffer.retrieve("agent1")
    assert len(results) == 2  # Returns last N, but we only have 2
    
    # Retrieve with query
    results = buffer.retrieve("agent1", query="content1")
    assert len(results) == 1
    assert results[0].content == "content1"

def test_update_operation():
    """Test update operation (treated as store)."""
    reset_shared_memory_buffer()
    buffer = get_shared_memory_buffer()
    
    entry = buffer.update("agent1", "updated content")
    
    assert entry.action == 'store'
    assert entry.content == "updated content"
    assert len(buffer) == 1

def test_callback_registration():
    """Test callback registration and invocation."""
    reset_shared_memory_buffer()
    buffer = get_shared_memory_buffer()
    
    callback_called = []
    
    def my_callback(entry):
        callback_called.append(entry)
    
    buffer.register_callback(my_callback)
    buffer.store("agent1", "test")
    
    assert len(callback_called) == 1
    assert callback_called[0].content == "test"

def test_len_operation():
    """Test __len__ operation."""
    reset_shared_memory_buffer()
    buffer = get_shared_memory_buffer()
    
    assert len(buffer) == 0
    
    buffer.store("agent1", "test1")
    buffer.store("agent2", "test2")
    
    assert len(buffer) == 2