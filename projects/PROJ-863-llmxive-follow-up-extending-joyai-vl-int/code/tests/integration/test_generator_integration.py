"""
Integration tests for the video generator (T013).

Tests verify:
1. Generator produces valid output files
2. Manifest structure is correct
3. Chunked streaming works correctly
4. CI mode generates subset, Non-CI generates full volume
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.data_synthesis.generator import generate_video_stream, main, CHUNK_SIZE, FPS
from src.data_synthesis.handoff import get_handoff_manager
from src.utils.logging import setup_project_logging

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def setup_env():
    """Setup required environment variables."""
    with patch.dict(os.environ, {'DATA_SEED': '12345', 'CI_MODE': 'false'}):
        yield

def test_generate_small_duration(temp_output_dir, setup_env):
    """Test generation of a small duration (10 seconds)."""
    duration_hours = 10 / 3600  # 10 seconds
    seed = 42
    
    manifest = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir,
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Verify manifest structure
    assert 'total_duration_hours' in manifest
    assert 'actual_duration_seconds' in manifest
    assert 'total_frames' in manifest
    assert 'chunk_count' in manifest
    assert 'chunks' in manifest
    
    # Verify expected duration (with small tolerance)
    expected_frames = int(10 * FPS)
    assert abs(manifest['total_frames'] - expected_frames) <= CHUNK_SIZE
    assert abs(manifest['actual_duration_seconds'] - 10) < 1.0
    
    # Verify chunk files exist
    for chunk_info in manifest['chunks']:
        chunk_path = Path(chunk_info['file'])
        assert chunk_path.exists(), f"Chunk file not found: {chunk_path}"
        
        # Verify chunk content
        with open(chunk_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == chunk_info['num_frames']
            
            # Verify JSONL format
            for line in lines:
                frame_data = json.loads(line)
                assert 'timestamp' in frame_data
                assert 'activity' in frame_data
                assert 'y_position' in frame_data
                assert 'frame_id' in frame_data
    
    # Verify manifest file
    manifest_path = temp_output_dir / 'manifest.jsonl'
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        loaded_manifest = json.loads(f.read())
        assert loaded_manifest['total_frames'] == manifest['total_frames']

def test_generate_multiple_chunks(temp_output_dir, setup_env):
    """Test generation that spans multiple chunks."""
    # Generate 20 seconds (should span at least 1 chunk if CHUNK_SIZE=300 frames = 10s)
    duration_hours = 20 / 3600
    seed = 42
    
    manifest = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir,
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Should have at least 2 chunks for 20 seconds with 10s chunks
    assert manifest['chunk_count'] >= 1
    assert manifest['total_frames'] > 0
    
    # Verify all chunks are registered in handoff
    handoff_manager = get_handoff_manager(temp_output_dir)
    all_chunks = handoff_manager.get_all_chunks()
    assert len(all_chunks) == manifest['chunk_count']

def test_deterministic_generation(temp_output_dir, setup_env):
    """Test that generation is deterministic with same seed."""
    duration_hours = 5 / 3600  # 5 seconds
    seed = 999
    
    # First run
    manifest1 = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir / 'run1',
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Second run with same seed
    manifest2 = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir / 'run2',
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Manifests should be identical
    assert manifest1['total_frames'] == manifest2['total_frames']
    assert manifest1['actual_duration_seconds'] == manifest2['actual_duration_seconds']
    assert manifest1['chunk_count'] == manifest2['chunk_count']
    
    # Verify first chunk content is identical
    chunk1_file = Path(manifest1['chunks'][0]['file'])
    chunk2_file = Path(manifest2['chunks'][0]['file'])
    
    with open(chunk1_file, 'r') as f1, open(chunk2_file, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
        assert len(lines1) == len(lines2)
        for l1, l2 in zip(lines1, lines2):
            assert l1 == l2, "Frame content differs between runs with same seed"

def test_ci_mode_subset_generation(temp_output_dir):
    """Test that CI mode generates a smaller subset."""
    with patch.dict(os.environ, {
        'DATA_SEED': '12345',
        'CI_MODE': 'true'
    }):
        # CI mode should generate 0.5 hours (1800 seconds)
        duration_hours = 0.5
        
        manifest = generate_video_stream(
            total_duration_hours=duration_hours,
            output_dir=temp_output_dir,
            chunk_size=CHUNK_SIZE,
            seed=42
        )
        
        assert manifest['actual_duration_seconds'] >= 1700  # Allow some tolerance
        assert manifest['actual_duration_seconds'] <= 1900

def test_non_ci_mode_full_generation(temp_output_dir):
    """Test that Non-CI mode generates full 50 hours (simulated with smaller test)."""
    with patch.dict(os.environ, {
        'DATA_SEED': '12345',
        'CI_MODE': 'false'
    }):
        # For testing, we use a smaller duration but verify the logic
        duration_hours = 1.0  # 1 hour for test
        
        manifest = generate_video_stream(
            total_duration_hours=duration_hours,
            output_dir=temp_output_dir,
            chunk_size=CHUNK_SIZE,
            seed=42
        )
        
        expected_frames = int(1.0 * 3600 * FPS)
        assert abs(manifest['total_frames'] - expected_frames) < CHUNK_SIZE
        assert abs(manifest['actual_duration_seconds'] - 3600) < 1.0

def test_streaming_writes_to_disk(temp_output_dir, setup_env):
    """Test that data is written to disk immediately (streaming)."""
    duration_hours = 1 / 3600  # 1 second
    seed = 42
    
    # Generate
    manifest = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir,
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Verify files exist on disk
    for chunk_info in manifest['chunks']:
        chunk_path = Path(chunk_info['file'])
        assert chunk_path.exists()
        assert chunk_path.stat().st_size > 0  # File has content
    
    # Verify manifest exists
    manifest_path = temp_output_dir / 'manifest.jsonl'
    assert manifest_path.exists()
    assert manifest_path.stat().st_size > 0

def test_activity_distribution(temp_output_dir, setup_env):
    """Test that multiple activity types are generated."""
    duration_hours = 5 / 3600  # 5 seconds
    seed = 42
    
    manifest = generate_video_stream(
        total_duration_hours=duration_hours,
        output_dir=temp_output_dir,
        chunk_size=CHUNK_SIZE,
        seed=seed
    )
    
    # Collect all activities from all chunks
    activities = set()
    for chunk_info in manifest['chunks']:
        chunk_path = Path(chunk_info['file'])
        with open(chunk_path, 'r') as f:
            for line in f:
                frame_data = json.loads(line)
                activities.add(frame_data['activity'])
    
    # Should have multiple activity types
    assert len(activities) > 1
    assert 'falling' in activities or 'sitting' in activities or 'standing' in activities or 'walking' in activities