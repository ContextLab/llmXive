"""
Unit tests for the Streaming Handoff logic (T013b).

Tests verify:
1. Chunk writing and atomic renaming.
2. Manifest updates.
3. Retrieval of all chunks and new chunks since a point.
4. Basic polling behavior (simulated).
"""

import json
import os
import tempfile
from pathlib import Path
import time

import pytest

from src.data_synthesis.handoff import HandoffManager, ChunkManifest, get_handoff_manager


@pytest.fixture
def temp_handoff_manager():
    """Create a temporary directory and HandoffManager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.jsonl")
        chunk_dir = os.path.join(tmpdir, "chunks")
        manager = HandoffManager(manifest_path, chunk_dir)
        yield manager


def test_write_chunk_creates_files(temp_handoff_manager):
    """Test that write_chunk creates the data file and updates the manifest."""
    manager = temp_handoff_manager
    chunk_id = "test_001"
    frames = [{"frame_id": 1, "data": "dummy"}, {"frame_id": 2, "data": "dummy"}]

    manifest_entry = manager.write_chunk(
        chunk_id=chunk_id,
        start_frame=0,
        end_frame=2,
        frames_data=frames,
        start_timestamp=0.0,
        end_timestamp=2.0
    )

    # Verify manifest entry
    assert manifest_entry.chunk_id == chunk_id
    assert manifest_entry.num_frames == 2
    assert manifest_entry.is_complete is True

    # Verify file exists
    expected_file = os.path.join(manager.chunk_dir, f"{chunk_id}.jsonl")
    assert os.path.exists(expected_file)

    # Verify file content
    with open(expected_file, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == frames[0]

    # Verify manifest content
    with open(manager.manifest_path, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 1
    manifest_data = json.loads(lines[0])
    assert manifest_data['chunk_id'] == chunk_id


def test_get_all_chunks(temp_handoff_manager):
    """Test retrieval of all chunks from the manifest."""
    manager = temp_handoff_manager

    # Write two chunks
    manager.write_chunk("c1", 0, 10, [{"f": 0}], 0.0, 1.0)
    manager.write_chunk("c2", 10, 20, [{"f": 10}], 1.0, 2.0)

    chunks = manager.get_all_chunks()
    assert len(chunks) == 2
    assert chunks[0].chunk_id == "c1"
    assert chunks[1].chunk_id == "c2"


def test_get_new_chunks_since(temp_handoff_manager):
    """Test retrieval of chunks added after a specific ID."""
    manager = temp_handoff_manager

    # Write three chunks
    manager.write_chunk("c1", 0, 10, [{"f": 0}], 0.0, 1.0)
    manager.write_chunk("c2", 10, 20, [{"f": 10}], 1.0, 2.0)
    manager.write_chunk("c3", 20, 30, [{"f": 20}], 2.0, 3.0)

    # Get new chunks after c1
    new_chunks = manager.get_new_chunks_since("c1")
    assert len(new_chunks) == 2
    assert new_chunks[0].chunk_id == "c2"
    assert new_chunks[1].chunk_id == "c3"

    # Get new chunks after c3 (none)
    new_chunks = manager.get_new_chunks_since("c3")
    assert len(new_chunks) == 0

    # Get all if last_id is None
    all_chunks = manager.get_new_chunks_since(None)
    assert len(all_chunks) == 3


def test_wait_for_next_chunk_generator(temp_handoff_manager):
    """Test the generator behavior of wait_for_next_chunk."""
    manager = temp_handoff_manager

    # Start the generator
    gen = manager.wait_for_next_chunk(poll_interval=0.1, timeout=1.0)

    # Initially no chunks, generator should yield nothing immediately if we don't advance
    # But the generator logic is: check -> sleep -> check.
    # We need to simulate writing a chunk while the generator is running.
    # Since we can't easily run two threads in a simple unit test without complexity,
    # we test the logic by calling next() and ensuring it blocks or raises StopIteration on timeout.

    # Test 1: Timeout when no data
    try:
        next(gen)
        # Should not reach here immediately if no data
        assert False, "Generator yielded without data"
    except StopIteration:
        # Expected if timeout is reached immediately (or very quickly)
        pass

    # Test 2: Yield when data appears
    # We write a chunk, then call next()
    manager.write_chunk("c1", 0, 10, [{"f": 0}], 0.0, 1.0)

    # Reset generator with the new state
    gen = manager.wait_for_next_chunk(last_chunk_id=None, poll_interval=0.01, timeout=1.0)
    try:
        chunk = next(gen)
        assert chunk.chunk_id == "c1"
    except StopIteration:
        assert False, "Generator should have yielded the new chunk"


def test_atomic_rename_on_write(temp_handoff_manager):
    """Verify that the final file is only visible after the full write."""
    manager = temp_handoff_manager
    chunk_id = "atomic_test"
    final_path = os.path.join(manager.chunk_dir, f"{chunk_id}.jsonl")

    # The write_chunk implementation uses os.replace(temp, final).
    # We can't easily test the atomicity of os.replace in a single thread,
    # but we can verify the final state is correct and no temp file remains.
    manager.write_chunk(
        chunk_id=chunk_id,
        start_frame=0,
        end_frame=1,
        frames_data=[{"f": 0}],
        start_timestamp=0.0,
        end_timestamp=1.0
    )

    assert os.path.exists(final_path)
    # Check no .tmp files left
    tmp_files = [f for f in os.listdir(manager.chunk_dir) if f.endswith('.tmp')]
    assert len(tmp_files) == 0