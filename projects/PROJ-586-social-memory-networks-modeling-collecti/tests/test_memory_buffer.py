"""Tests for the memory buffer implementation."""
import pytest
import time
from datetime import datetime
from code.memory.buffer import (
    MemoryAction, MemoryEntry, MemoryActionToken,
    MemoryBuffer, get_shared_buffer, get_shared_memory_buffer,
    parse_memory_action, parse_memory_action_token, now
)


class TestMemoryAction:
    """Tests for MemoryAction enum."""

    def test_memory_action_values(self):
        """Test that all expected actions exist."""
        assert MemoryAction.WRITE.value == "write"
        assert MemoryAction.READ.value == "read"
        assert MemoryAction.UPDATE.value == "update"
        assert MemoryAction.DELETE.value == "delete"
        assert MemoryAction.QUERY.value == "query"


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_memory_entry_creation(self):
        """Test creating a memory entry."""
        entry = MemoryEntry(
            entry_id="test_1",
            action=MemoryAction.WRITE,
            content="Test content",
            agent_id="agent_1",
            confidence=0.9
        )
        assert entry.entry_id == "test_1"
        assert entry.action == MemoryAction.WRITE
        assert entry.content == "Test content"
        assert entry.agent_id == "agent_1"
        assert entry.confidence == 0.9

    def test_memory_entry_to_dict(self):
        """Test converting entry to dictionary."""
        entry = MemoryEntry(
            entry_id="test_1",
            action=MemoryAction.WRITE,
            content="Test content"
        )
        d = entry.to_dict()
        assert d["entry_id"] == "test_1"
        assert d["action"] == "write"
        assert d["content"] == "Test content"

    def test_memory_entry_to_json(self):
        """Test converting entry to JSON."""
        entry = MemoryEntry(
            entry_id="test_1",
            action=MemoryAction.WRITE,
            content="Test content"
        )
        json_str = entry.to_json()
        assert isinstance(json_str, str)
        assert "test_1" in json_str

    def test_memory_entry_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "entry_id": "test_1",
            "action": "write",
            "content": "Test content",
            "agent_id": "agent_1",
            "confidence": 0.9
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.entry_id == "test_1"
        assert entry.action == MemoryAction.WRITE
        assert entry.content == "Test content"

    def test_memory_entry_roundtrip(self):
        """Test JSON roundtrip."""
        entry = MemoryEntry(
            entry_id="test_1",
            action=MemoryAction.WRITE,
            content="Test content",
            agent_id="agent_1"
        )
        json_str = entry.to_json()
        restored = MemoryEntry.from_json(json_str)
        assert restored.entry_id == entry.entry_id
        assert restored.action == entry.action
        assert restored.content == entry.content


class TestMemoryActionToken:
    """Tests for MemoryActionToken."""

    def test_token_creation(self):
        """Test creating a token."""
        token = MemoryActionToken(
            action=MemoryAction.WRITE,
            content="Test content",
            agent_id="agent_1"
        )
        assert token.action == MemoryAction.WRITE
        assert token.content == "Test content"

    def test_token_to_string(self):
        """Test converting token to string."""
        token = MemoryActionToken(
            action=MemoryAction.WRITE,
            content="Test content",
            agent_id="agent_1"
        )
        token_str = token.to_token_string()
        assert "<MEMORY_ACTION" in token_str
        assert "write" in token_str
        assert "agent_1" in token_str

    def test_token_from_string(self):
        """Test parsing token from string."""
        token_str = "<MEMORY_ACTION action='write' agent='agent_1'>Test content</MEMORY_ACTION>"
        token = MemoryActionToken.from_token_string(token_str)
        assert token is not None
        assert token.action == MemoryAction.WRITE
        assert token.agent_id == "agent_1"
        assert token.content == "Test content"

    def test_token_from_string_no_agent(self):
        """Test parsing token without agent."""
        token_str = "<MEMORY_ACTION action='read'>Query here</MEMORY_ACTION>"
        token = MemoryActionToken.from_token_string(token_str)
        assert token is not None
        assert token.action == MemoryAction.READ
        assert token.agent_id is None


class TestMemoryBuffer:
    """Tests for MemoryBuffer class."""

    def setup_method(self):
        """Set up test fixtures."""
        MemoryBuffer.reset_instance()
        self.buffer = MemoryBuffer()

    def test_buffer_creation(self):
        """Test buffer creation."""
        assert self.buffer.capacity == 10000
        assert len(self.buffer) == 0

    def test_write_entry(self):
        """Test writing to buffer."""
        entry = self.buffer.write("Test content", agent_id="agent_1")
        assert entry is not None
        assert entry.content == "Test content"
        assert entry.agent_id == "agent_1"
        assert len(self.buffer) == 1

    def test_read_entries(self):
        """Test reading from buffer."""
        self.buffer.write("Test content about apples", agent_id="agent_1")
        self.buffer.write("Test content about oranges", agent_id="agent_2")

        results = self.buffer.read("apples", top_k=5)
        assert len(results) == 1
        assert "apples" in results[0].content

    def test_update_entry(self):
        """Test updating an entry."""
        entry = self.buffer.write("Original content")
        updated = self.buffer.update(entry.entry_id, "Updated content")
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.action == MemoryAction.UPDATE

    def test_delete_entry(self):
        """Test deleting an entry."""
        entry = self.buffer.write("To be deleted")
        success = self.buffer.delete(entry.entry_id)
        assert success is True
        assert len(self.buffer) == 0

    def test_delete_nonexistent(self):
        """Test deleting non-existent entry."""
        success = self.buffer.delete("nonexistent")
        assert success is False

    def test_get_all(self):
        """Test getting all entries."""
        self.buffer.write("Content 1")
        self.buffer.write("Content 2")
        self.buffer.write("Content 3")

        all_entries = self.buffer.get_all()
        assert len(all_entries) == 3

    def test_get_entry(self):
        """Test getting specific entry."""
        entry = self.buffer.write("Specific content")
        retrieved = self.buffer.get_entry(entry.entry_id)
        assert retrieved is not None
        assert retrieved.content == "Specific content"

    def test_contains(self):
        """Test __contains__ method."""
        entry = self.buffer.write("Test")
        assert entry.entry_id in self.buffer
        assert "nonexistent" not in self.buffer

    def test_len(self):
        """Test __len__ method."""
        assert len(self.buffer) == 0
        self.buffer.write("One")
        assert len(self.buffer) == 1
        self.buffer.write("Two")
        assert len(self.buffer) == 2

    def test_process_token(self):
        """Test processing memory action token."""
        token_str = "<MEMORY_ACTION action='write' agent='agent_1'>Processed content</MEMORY_ACTION>"
        entry = self.buffer.process_token(token_str)
        assert entry is not None
        assert entry.content == "Processed content"
        assert entry.agent_id == "agent_1"

    def test_eviction_lru(self):
        """Test LRU eviction policy."""
        small_buffer = MemoryBuffer(capacity=3, eviction_policy="lru")
        small_buffer.write("Entry 1")
        small_buffer.write("Entry 2")
        small_buffer.write("Entry 3")
        # Access entry 1 to make it recently used
        small_buffer.get_entry("mem_1_0")
        small_buffer.write("Entry 4")  # Should evict entry 2

        # Entry 2 should be evicted, entry 1 should remain
        all_entries = small_buffer.get_all()
        assert len(all_entries) == 3

    def test_eviction_confidence(self):
        """Test confidence-based eviction policy."""
        small_buffer = MemoryBuffer(capacity=3, eviction_policy="confidence")
        small_buffer.write("Low confidence", confidence=0.1)
        small_buffer.write("Medium confidence", confidence=0.5)
        small_buffer.write("High confidence", confidence=0.9)
        small_buffer.write("New entry")  # Should evict lowest confidence

        all_entries = small_buffer.get_all()
        assert len(all_entries) == 3
        # The 0.1 confidence entry should be gone
        contents = [e.content for e in all_entries]
        assert "Low confidence" not in contents

    def test_reset(self):
        """Test reset method."""
        self.buffer.write("Entry 1")
        self.buffer.write("Entry 2")
        self.buffer.reset()
        assert len(self.buffer) == 0

    def test_fallback_attribute_no_error(self):
        """Test that unknown attributes don't raise errors (logger-style)."""
        # These should not raise AttributeError
        result = self.buffer.info("Test message")
        assert result is None

        result = self.buffer.debug("Debug info")
        assert result is None

        result = self.buffer.warning("Warning message")
        assert result is None

        result = self.buffer.error("Error message")
        assert result is None

        result = self.buffer.critical("Critical message")
        assert result is None

        result = self.buffer.unknown_method("arg1", arg2="value")
        assert result is None


class TestSharedBuffer:
    """Tests for shared buffer singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        MemoryBuffer.reset_instance()

    def test_get_shared_buffer(self):
        """Test getting shared buffer instance."""
        buffer1 = get_shared_buffer()
        buffer2 = get_shared_buffer()
        assert buffer1 is buffer2

    def test_get_shared_memory_buffer_alias(self):
        """Test alias function."""
        buffer1 = get_shared_buffer()
        buffer2 = get_shared_memory_buffer()
        assert buffer1 is buffer2

    def test_singleton_persists(self):
        """Test that singleton persists across calls."""
        buffer = get_shared_buffer()
        buffer.write("Shared content")
        assert len(buffer) == 1

        buffer2 = get_shared_buffer()
        assert len(buffer2) == 1
        assert buffer2 is buffer


class TestNowHelper:
    """Tests for now() helper."""

    def test_now_returns_string(self):
        """Test that now() returns a string."""
        timestamp = now()
        assert isinstance(timestamp, str)

    def test_now_iso_format(self):
        """Test that now() returns ISO format."""
        timestamp = now()
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp)