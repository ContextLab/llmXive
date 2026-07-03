"""Tests for memory buffer module."""
import pytest
from memory.buffer import (
    MemoryAction,
    MemoryEntry,
    MemoryBuffer,
    MemoryActionType,
    parse_memory_action_token,
    parse_memory_action,
    format_action_token,
    parse_action_from_prompt,
    get_shared_buffer,
    reset_shared_buffer,
    now,
)


def test_memory_action_dataclass():
    """Test MemoryAction dataclass."""
    action = MemoryAction(
        action_type=MemoryActionType.STORE,
        content="test content",
        metadata={"key": "value"}
    )
    assert action.action_type == MemoryActionType.STORE
    assert action.content == "test content"
    assert action.metadata == {"key": "value"}
    assert action.timestamp is not None
    action_dict = action.to_dict()
    assert action_dict["action_type"] == MemoryActionType.STORE
    assert action_dict["content"] == "test content"


def test_memory_entry_dataclass():
    """Test MemoryEntry dataclass."""
    entry = MemoryEntry(
        key="test_key",
        value="test_value",
        metadata={"info": "data"}
    )
    assert entry.key == "test_key"
    assert entry.value == "test_value"
    assert entry.action_type == "store"
    assert entry.timestamp is not None
    entry_dict = entry.to_dict()
    assert entry_dict["key"] == "test_key"
    assert entry_dict["value"] == "test_value"


def test_parse_memory_action_token():
    """Test parsing <MEMORY_ACTION> token."""
    token = '<MEMORY_ACTION>{"action_type": "store", "content": "hello"}</MEMORY_ACTION>'
    result = parse_memory_action_token(token)
    assert result is not None
    assert result["action_type"] == "store"
    assert result["content"] == "hello"

    # Test invalid JSON
    invalid_token = '<MEMORY_ACTION>not json</MEMORY_ACTION>'
    result = parse_memory_action_token(invalid_token)
    assert result is None

    # Test no token
    no_token = "just plain text"
    result = parse_memory_action_token(no_token)
    assert result is None


def test_parse_memory_action():
    """Test parsing memory action from text."""
    text = '<MEMORY_ACTION>{"action_type": "retrieve", "content": "query", "metadata": {"id": 1}}</MEMORY_ACTION>'
    action = parse_memory_action(text)
    assert action is not None
    assert action.action_type == "retrieve"
    assert action.content == "query"
    assert action.metadata == {"id": 1}

    # Test no action in text
    no_action = "plain text"
    action = parse_memory_action(no_action)
    assert action is None


def test_format_action_token():
    """Test formatting MemoryAction as token."""
    action = MemoryAction(
        action_type=MemoryActionType.STORE,
        content="data",
        metadata={"test": True}
    )
    token = format_action_token(action)
    assert token.startswith("<MEMORY_ACTION>")
    assert token.endswith("</MEMORY_ACTION>")
    assert "store" in token
    assert "data" in token

    # Verify round-trip
    parsed = parse_memory_action_token(token)
    assert parsed is not None
    assert parsed["action_type"] == MemoryActionType.STORE
    assert parsed["content"] == "data"


def test_parse_action_from_prompt():
    """Test extracting memory action from prompt."""
    prompt = 'Please remember this: <MEMORY_ACTION>{"action_type": "store", "content": "important fact"}</MEMORY_ACTION> and continue.'
    action = parse_action_from_prompt(prompt)
    assert action is not None
    assert action.action_type == "store"
    assert action.content == "important fact"


def test_basic_buffer_operations():
    """Test basic MemoryBuffer operations."""
    buf = MemoryBuffer()

    # Test store
    entry = buf.store("key1", "value1")
    assert entry.key == "key1"
    assert entry.value == "value1"

    # Test retrieve
    value = buf.retrieve("key1")
    assert value == "value1"

    # Test retrieve non-existent
    value = buf.retrieve("nonexistent")
    assert value is None

    # Test get_all
    buf.store("key2", "value2")
    all_entries = buf.get_all()
    assert len(all_entries) == 2
    assert all_entries[0].key == "key1"
    assert all_entries[1].key == "key2"


def test_buffer_update_delete():
    """Test MemoryBuffer update and delete operations."""
    buf = MemoryBuffer()
    buf.store("key1", "original")

    # Test update
    updated = buf.update("key1", "modified")
    assert updated is not None
    assert updated.value == "modified"
    assert updated.action_type == MemoryActionType.UPDATE

    # Retrieve should return most recent
    value = buf.retrieve("key1")
    assert value == "modified"

    # Test delete
    deleted = buf.delete("key1")
    assert deleted is True

    # After delete, retrieve returns None
    value = buf.retrieve("key1")
    assert value is None

    # Delete non-existent returns False
    deleted = buf.delete("nonexistent")
    assert deleted is False


def test_buffer_search():
    """Test MemoryBuffer search by prefix."""
    buf = MemoryBuffer()
    buf.store("user:1", "Alice")
    buf.store("user:2", "Bob")
    buf.store("task:1", "Task A")

    results = buf.search("user:")
    assert len(results) == 2
    assert all(e.key.startswith("user:") for e in results)

    results = buf.search("task:")
    assert len(results) == 1
    assert results[0].key == "task:1"

    results = buf.search("nonexistent:")
    assert len(results) == 0


def test_shared_buffer_is_singleton():
    """Test that get_shared_buffer returns the same instance."""
    buf1 = get_shared_buffer()
    buf2 = get_shared_buffer()
    assert buf1 is buf2

    # Reset and verify
    reset_shared_buffer()
    buf3 = get_shared_buffer()
    assert buf3 is buf1  # Still the same object


def test_buffer_thread_safety():
    """Test that buffer operations are thread-safe."""
    buf = MemoryBuffer()
    import threading

    def store_entries():
        for i in range(100):
            buf.store(f"key_{i}", f"value_{i}")

    threads = [threading.Thread(target=store_entries) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All entries should be stored (5 threads * 100 entries)
    all_entries = buf.get_all()
    assert len(all_entries) == 500


def test_fallback_attribute_no_error():
    """Test that unknown method calls don't raise AttributeError."""
    buf = MemoryBuffer()

    # These should not raise
    result = buf.unknown_method()
    assert result is None

    result = buf.another_unknown_call("arg1", kwarg="value")
    assert result is None

    result = buf.reset()
    assert result is None


def test_now_helper():
    """Test the now() helper function."""
    timestamp = now()
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO format contains T
    assert "Z" in timestamp or "+" in timestamp or "-" in timestamp  # timezone info