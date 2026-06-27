"""Tests for the shared memory buffer implementation."""

import pytest
import time
from memory.buffer import (
    MemoryBuffer,
    MemoryEntry,
    MemoryAction,
    MemoryActionRequest,
    MemoryActionResult,
    parse_memory_action,
    execute_memory_action,
    handle_agent_output,
    get_shared_memory_buffer,
    reset_shared_memory_buffer,
)


class TestMemoryBuffer:
    """Tests for MemoryBuffer class."""

    def test_create_buffer(self):
        """Test basic buffer creation."""
        buffer = MemoryBuffer()
        assert buffer.size == 0
        assert buffer.total_tokens == 0
        assert buffer._max_entries == 10000

    def test_store_and_retrieve(self):
        """Test storing and retrieving a memory entry."""
        buffer = MemoryBuffer()

        entry = buffer.store(
            content="Test memory content",
            creator_agent="agent_1",
            tags=["test"],
        )

        assert entry.id is not None
        assert entry.content == "Test memory content"
        assert entry.creator_agent == "agent_1"
        assert "test" in entry.tags
        assert buffer.size == 1

        retrieved = buffer.retrieve(entry.id)
        assert retrieved is not None
        assert retrieved.content == "Test memory content"
        assert retrieved.access_count == 1

    def test_retrieve_nonexistent(self):
        """Test retrieving a non-existent memory."""
        buffer = MemoryBuffer()
        result = buffer.retrieve("nonexistent_id")
        assert result is None

    def test_update_memory(self):
        """Test updating an existing memory."""
        buffer = MemoryBuffer()

        entry = buffer.store(
            content="Original content",
            creator_agent="agent_1",
        )

        updated = buffer.update(
            entry.id,
            content="Updated content",
            tags=["updated"],
        )

        assert updated is not None
        assert updated.content == "Updated content"
        assert "updated" in updated.tags

    def test_update_nonexistent(self):
        """Test updating a non-existent memory."""
        buffer = MemoryBuffer()
        result = buffer.update("nonexistent_id", content="test")
        assert result is None

    def test_delete_memory(self):
        """Test deleting a memory entry."""
        buffer = MemoryBuffer()

        entry = buffer.store(
            content="To be deleted",
            creator_agent="agent_1",
        )

        deleted = buffer.delete(entry.id)
        assert deleted is True
        assert buffer.size == 0

        # Try to delete again
        deleted_again = buffer.delete(entry.id)
        assert deleted_again is False

    def test_query_by_tags(self):
        """Test querying memories by tags."""
        buffer = MemoryBuffer()

        buffer.store(content="Memory 1", creator_agent="agent_1", tags=["important"])
        buffer.store(content="Memory 2", creator_agent="agent_1", tags=["test"])
        buffer.store(content="Memory 3", creator_agent="agent_1", tags=["important", "test"])

        results = buffer.query(tags=["important"])
        assert len(results) == 2

    def test_query_by_creator(self):
        """Test querying memories by creator."""
        buffer = MemoryBuffer()

        buffer.store(content="Memory 1", creator_agent="agent_1")
        buffer.store(content="Memory 2", creator_agent="agent_2")
        buffer.store(content="Memory 3", creator_agent="agent_1")

        results = buffer.query(creator_agent="agent_1")
        assert len(results) == 2

    def test_query_by_text(self):
        """Test querying memories by content text."""
        buffer = MemoryBuffer()

        buffer.store(content="Important meeting notes", creator_agent="agent_1")
        buffer.store(content="Shopping list", creator_agent="agent_1")
        buffer.store(content="Meeting reminder", creator_agent="agent_1")

        results = buffer.query(query_text="meeting")
        assert len(results) == 2

    def test_clear_buffer(self):
        """Test clearing the buffer."""
        buffer = MemoryBuffer()

        buffer.store(content="Test 1", creator_agent="agent_1")
        buffer.store(content="Test 2", creator_agent="agent_1")

        buffer.clear()

        assert buffer.size == 0
        assert buffer.total_tokens == 0

    def test_eviction_on_capacity(self):
        """Test LRU eviction when buffer reaches capacity."""
        buffer = MemoryBuffer(max_entries=3)

        # Store more than capacity
        for i in range(5):
            buffer.store(content=f"Memory {i}", creator_agent="agent_1")

        assert buffer.size == 3

    def test_get_stats(self):
        """Test getting buffer statistics."""
        buffer = MemoryBuffer()

        buffer.store(content="Test content", creator_agent="agent_1")

        stats = buffer.get_stats()
        assert stats["size"] == 1
        assert stats["max_entries"] == 10000
        assert stats["total_tokens"] > 0


class TestMemoryActionParsing:
    """Tests for memory action parsing and execution."""

    def test_parse_store_action(self):
        """Test parsing a STORE action."""
        content = '<MEMORY_ACTION>{"action": "store", "params": {"content": "test", "creator_agent": "agent_1"}}</MEMORY_ACTION>'

        request = parse_memory_action(content)
        assert request is not None
        assert request.action == MemoryAction.STORE
        assert request.params["content"] == "test"
        assert request.params["creator_agent"] == "agent_1"

    def test_parse_retrieve_action(self):
        """Test parsing a RETRIEVE action."""
        content = '<MEMORY_ACTION>{"action": "retrieve", "params": {"memory_id": "abc123"}}</MEMORY_ACTION>'

        request = parse_memory_action(content)
        assert request is not None
        assert request.action == MemoryAction.RETRIEVE
        assert request.params["memory_id"] == "abc123"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        content = '<MEMORY_ACTION>{invalid json}</MEMORY_ACTION>'

        request = parse_memory_action(content)
        assert request is None

    def test_parse_no_action(self):
        """Test parsing content without memory action."""
        content = "This is just regular text"

        request = parse_memory_action(content)
        assert request is None

    def test_execute_store(self):
        """Test executing a STORE action."""
        buffer = MemoryBuffer()

        request = MemoryActionRequest(
            action=MemoryAction.STORE,
            params={"content": "Test content", "creator_agent": "agent_1"},
            raw_content="",
        )

        result = execute_memory_action(request, buffer)
        assert result.success is True
        assert "memory_id" in result.data

    def test_execute_retrieve(self):
        """Test executing a RETRIEVE action."""
        buffer = MemoryBuffer()

        # First store
        store_request = MemoryActionRequest(
            action=MemoryAction.STORE,
            params={"content": "Test content", "creator_agent": "agent_1"},
            raw_content="",
        )
        store_result = execute_memory_action(store_request, buffer)
        memory_id = store_result.data["memory_id"]

        # Then retrieve
        retrieve_request = MemoryActionRequest(
            action=MemoryAction.RETRIEVE,
            params={"memory_id": memory_id},
            raw_content="",
        )
        retrieve_result = execute_memory_action(retrieve_request, buffer)

        assert retrieve_result.success is True
        assert retrieve_result.data["content"] == "Test content"

    def test_execute_retrieve_nonexistent(self):
        """Test executing a RETRIEVE for non-existent memory."""
        buffer = MemoryBuffer()

        request = MemoryActionRequest(
            action=MemoryAction.RETRIEVE,
            params={"memory_id": "nonexistent"},
            raw_content="",
        )

        result = execute_memory_action(request, buffer)
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_execute_delete(self):
        """Test executing a DELETE action."""
        buffer = MemoryBuffer()

        # Store first
        store_request = MemoryActionRequest(
            action=MemoryAction.STORE,
            params={"content": "Test", "creator_agent": "agent_1"},
            raw_content="",
        )
        store_result = execute_memory_action(store_request, buffer)
        memory_id = store_result.data["memory_id"]

        # Delete
        delete_request = MemoryActionRequest(
            action=MemoryAction.DELETE,
            params={"memory_id": memory_id},
            raw_content="",
        )
        delete_result = execute_memory_action(delete_request, buffer)

        assert delete_result.success is True

    def test_handle_agent_output_with_action(self):
        """Test handling agent output with memory action."""
        buffer = MemoryBuffer()

        output = """
        I remember this important fact.
        <MEMORY_ACTION>{"action": "store", "params": {"content": "Important fact", "creator_agent": "agent_1"}}</MEMORY_ACTION>
        And I'm done.
        """

        cleaned, results = handle_agent_output(output, buffer)

        assert "Important fact" not in cleaned
        assert len(results) == 1
        assert results[0].success is True
        assert buffer.size == 1

    def test_handle_agent_output_no_action(self):
        """Test handling agent output without memory action."""
        buffer = MemoryBuffer()

        output = "This is just regular text with no memory actions."

        cleaned, results = handle_agent_output(output, buffer)

        assert cleaned == output.strip()
        assert len(results) == 0
        assert buffer.size == 0

    def test_handle_multiple_actions(self):
        """Test handling multiple memory actions in output."""
        buffer = MemoryBuffer()

        output = """
        <MEMORY_ACTION>{"action": "store", "params": {"content": "First", "creator_agent": "agent_1"}}</MEMORY_ACTION>
        Some text
        <MEMORY_ACTION>{"action": "store", "params": {"content": "Second", "creator_agent": "agent_1"}}</MEMORY_ACTION>
        """

        cleaned, results = handle_agent_output(output, buffer)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True
        assert buffer.size == 2


class TestSharedMemoryBuffer:
    """Tests for global shared memory buffer."""

    def test_get_shared_buffer(self):
        """Test getting the shared buffer."""
        buffer1 = get_shared_memory_buffer()
        buffer2 = get_shared_memory_buffer()

        assert buffer1 is buffer2

    def test_reset_shared_buffer(self):
        """Test resetting the shared buffer."""
        buffer = get_shared_memory_buffer()
        buffer.store(content="Test", creator_agent="agent_1")

        assert buffer.size == 1

        reset_shared_memory_buffer()

        # Get a new buffer (old one is cleared)
        new_buffer = get_shared_memory_buffer()
        assert new_buffer.size == 0
