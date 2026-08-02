"""
Unit tests for the Streaming Handoff logic.
"""
import json
import os
import tempfile
from pathlib import Path
import time
import pytest
from unittest.mock import patch, MagicMock

from src.data_synthesis.handoff import (
    ChunkManifest,
    HandoffManager,
    get_handoff_manager
)
from src.utils.validation import validate_manifest_structure


@pytest.fixture
def temp_handoff_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HandoffManager(tmpdir)
        yield manager


def test_write_chunk_creates_files(temp_handoff_manager):
    """Test that finalizing a chunk creates the manifest file."""
    manager = temp_handoff_manager
    chunk_id = "test_chunk_001"
    start_ts = time.time()
    
    # Register start
    manifest = manager.register_chunk_start(chunk_id, start_ts)
    assert manifest.status == 'writing'
    
    # Finalize
    finalized = manager.finalize_chunk(manifest, time.time(), 100)
    assert finalized.status == 'ready'
    
    # Check files exist
    manifest_path = Path(manager.output_dir) / f"{chunk_id}_manifest.json"
    assert manifest_path.exists()
    
    # Check content
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    assert data['chunk_id'] == chunk_id
    assert data['frame_count'] == 100
    assert data['status'] == 'ready'


def test_get_all_chunks(temp_handoff_manager):
    """Test retrieving all chunks from the global manifest."""
    manager = temp_handoff_manager
    
    # Add a chunk
    chunk_id = "chunk_A"
    manifest = manager.register_chunk_start(chunk_id, time.time())
    manager.finalize_chunk(manifest, time.time(), 50)
    manager.update_global_manifest(manifest)
    
    # Retrieve
    chunks = manager.get_all_chunks()
    assert len(chunks) == 1
    assert chunks[0].chunk_id == chunk_id


def test_get_new_chunks_since(temp_handoff_manager):
    """Test fetching only new chunks since a specific ID."""
    manager = temp_handoff_manager
    
    # Add Chunk A
    chunk_a = manager.register_chunk_start("chunk_A", time.time())
    manager.finalize_chunk(chunk_a, time.time(), 10)
    manager.update_global_manifest(chunk_a)
    
    # Add Chunk B
    chunk_b = manager.register_chunk_start("chunk_B", time.time())
    manager.finalize_chunk(chunk_b, time.time(), 20)
    manager.update_global_manifest(chunk_b)
    
    # Get new since A
    new_chunks = manager.get_new_chunks_since("chunk_A")
    assert len(new_chunks) == 1
    assert new_chunks[0].chunk_id == "chunk_B"
    
    # Get new since B (none)
    new_chunks = manager.get_new_chunks_since("chunk_B")
    assert len(new_chunks) == 0


def test_wait_for_next_chunk_generator(temp_handoff_manager):
    """Test the generator waits for new chunks."""
    manager = temp_handoff_manager
    last_id = None
    
    # Start the generator in a way that we can test logic
    # Since this is a blocking generator, we test the timeout logic via wait_for_next_chunk
    result = manager.wait_for_next_chunk(timeout=0.1)
    assert result is None  # Timeout expected
    
    # Add a chunk manually and check
    chunk = manager.register_chunk_start("chunk_C", time.time())
    manager.finalize_chunk(chunk, time.time(), 30)
    manager.update_global_manifest(chunk)
    
    result = manager.wait_for_next_chunk(timeout=0.1)
    assert result is not None
    assert result.chunk_id == "chunk_C"


def test_atomic_rename_on_write(temp_handoff_manager):
    """Test that the manifest file is written atomically."""
    manager = temp_handoff_manager
    chunk_id = "atomic_test"
    
    manifest = manager.register_chunk_start(chunk_id, time.time())
    
    # Check that .tmp file is created first (internally in finalize_chunk)
    # We can't easily test the atomic rename timing, but we can verify the final state
    # and that no .tmp files are left behind
    finalized = manager.finalize_chunk(manifest, time.time(), 10)
    
    manifest_path = Path(manager.output_dir) / f"{chunk_id}_manifest.json"
    tmp_path = Path(manager.output_dir) / f"{chunk_id}_manifest.json.tmp"
    
    assert manifest_path.exists()
    assert not tmp_path.exists()  # Should be cleaned up by rename
