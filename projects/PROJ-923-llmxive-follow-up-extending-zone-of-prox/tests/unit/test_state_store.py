"""
Unit tests for the StateStore utility.

Tests cover:
- State file creation and loading
- Cycle record addition and retrieval
- Historical confidence score retrieval
- Edge cases (empty state, missing files)
"""

import pytest
import os
import yaml
from pathlib import Path
import tempfile
from datetime import datetime

from utils.state_store import StateStore, CycleRecord, ProjectState, get_state_store

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_cycle_record():
    """Create a sample cycle record for testing."""
    return CycleRecord(
        cycle_id=1,
        task_id="test_task",
        seed=42,
        timestamp=datetime.utcnow().isoformat(),
        confidence_scores=[0.1, 0.5, 0.9],
        prompt_length=150,
        accuracy=0.85,
        metrics={'loss': 0.2}
    )

@pytest.fixture
def sample_cycle_record_2():
    """Create a second sample cycle record."""
    return CycleRecord(
        cycle_id=2,
        task_id="test_task",
        seed=42,
        timestamp=datetime.utcnow().isoformat(),
        confidence_scores=[0.2, 0.6, 0.85],
        prompt_length=140,
        accuracy=0.90,
        metrics={'loss': 0.15}
    )

def test_state_store_creation(temp_state_dir):
    """Test that StateStore creates the state file correctly."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    assert store.path == state_file
    assert state_file.exists()
    assert store.state is not None
    assert store.state.project_id == "PROJ-923-llmxive-follow-up-extending-zone-of-prox"
    assert len(store.state.cycles) == 0

def test_add_cycle_record(temp_state_dir, sample_cycle_record):
    """Test adding a cycle record to the state store."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    
    assert len(store.state.cycles) == 1
    assert store.state.cycles[0].cycle_id == 1
    assert store.state.cycles[0].task_id == "test_task"
    
    # Verify file was updated
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    assert len(data['cycles']) == 1

def test_get_historical_confidence_scores(temp_state_dir, sample_cycle_record, sample_cycle_record_2):
    """Test retrieving historical confidence scores."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    store.add_cycle_record(sample_cycle_record_2)
    
    # Get all scores for the task
    scores = store.get_historical_confidence_scores("test_task")
    assert len(scores) == 2
    assert scores[0] == [0.1, 0.5, 0.9]
    assert scores[1] == [0.2, 0.6, 0.85]
    
    # Get scores for non-existent task
    scores_empty = store.get_historical_confidence_scores("nonexistent")
    assert len(scores_empty) == 0

def test_get_all_cycles_for_task(temp_state_dir, sample_cycle_record, sample_cycle_record_2):
    """Test retrieving all cycle records for a task."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    store.add_cycle_record(sample_cycle_record_2)
    
    cycles = store.get_all_cycles_for_task("test_task")
    assert len(cycles) == 2
    assert cycles[0].cycle_id == 1
    assert cycles[1].cycle_id == 2

def test_get_latest_cycle(temp_state_dir, sample_cycle_record, sample_cycle_record_2):
    """Test retrieving the latest cycle."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    store.add_cycle_record(sample_cycle_record_2)
    
    latest = store.get_latest_cycle("test_task")
    assert latest is not None
    assert latest.cycle_id == 2
    assert latest.accuracy == 0.90

def test_get_latest_cycle_with_seed_filter(temp_state_dir, sample_cycle_record):
    """Test retrieving latest cycle with seed filter."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    
    # Filter by matching seed
    latest = store.get_latest_cycle("test_task", seed=42)
    assert latest is not None
    assert latest.seed == 42
    
    # Filter by non-matching seed
    latest_none = store.get_latest_cycle("test_task", seed=999)
    assert latest_none is None

def test_state_version_increment(temp_state_dir, sample_cycle_record):
    """Test that state version increments on save."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    initial_version = store.state.version
    
    store.add_cycle_record(sample_cycle_record)
    
    assert store.state.version == initial_version + 1

def test_get_state_stats(temp_state_dir, sample_cycle_record, sample_cycle_record_2):
    """Test getting state statistics."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    store.add_cycle_record(sample_cycle_record_2)
    
    stats = store.get_state_stats()
    
    assert stats['total_cycles'] == 2
    assert stats['unique_tasks'] == 1
    assert stats['unique_seids'] == 1
    assert 'project_id' in stats
    assert 'version' in stats

def test_clear_all_records(temp_state_dir, sample_cycle_record):
    """Test clearing all records."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    store.add_cycle_record(sample_cycle_record)
    assert len(store.state.cycles) == 1
    
    store.clear_all_records()
    assert len(store.state.cycles) == 0

def test_load_existing_state(temp_state_dir, sample_cycle_record):
    """Test loading an existing state file."""
    state_file = temp_state_dir / "test_project.yaml"
    
    # Create initial store
    store1 = StateStore(state_file)
    store1.add_cycle_record(sample_cycle_record)
    
    # Create new store instance (should load existing data)
    store2 = StateStore(state_file)
    
    assert len(store2.state.cycles) == 1
    assert store2.state.cycles[0].cycle_id == 1

def test_empty_state_handling(temp_state_dir):
    """Test handling of empty state."""
    state_file = temp_state_dir / "test_project.yaml"
    store = StateStore(state_file)
    
    # Empty state should have no cycles
    assert len(store.state.cycles) == 0
    
    # Retrieving from empty state should return empty list
    scores = store.get_historical_confidence_scores("any_task")
    assert scores == []
    
    latest = store.get_latest_cycle("any_task")
    assert latest is None

def test_cycle_record_serialization():
    """Test cycle record serialization and deserialization."""
    record = CycleRecord(
        cycle_id=1,
        task_id="test",
        seed=42,
        timestamp="2024-01-01T00:00:00",
        confidence_scores=[0.1, 0.5],
        prompt_length=100,
        accuracy=0.85,
        metrics={'key': 'value'}
    )
    
    record_dict = record.to_dict()
    restored = CycleRecord.from_dict(record_dict)
    
    assert restored.cycle_id == record.cycle_id
    assert restored.task_id == record.task_id
    assert restored.seed == record.seed
    assert restored.confidence_scores == record.confidence_scores
    assert restored.prompt_length == record.prompt_length
    assert restored.accuracy == record.accuracy
    assert restored.metrics == record.metrics

def test_project_state_serialization():
    """Test project state serialization and deserialization."""
    state = ProjectState(
        project_id="TEST-PROJECT",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        version=1,
        cycles=[],
        metadata={'test': 'data'}
    )
    
    state_dict = state.to_dict()
    restored = ProjectState.from_dict(state_dict)
    
    assert restored.project_id == state.project_id
    assert restored.version == state.version
    assert restored.metadata == state.metadata
    assert len(restored.cycles) == 0

def test_get_state_store_convenience_function(temp_state_dir):
    """Test the convenience function get_state_store."""
    state_file = temp_state_dir / "test_project.yaml"
    store = get_state_store(state_file)
    
    assert isinstance(store, StateStore)
    assert store.path == state_file