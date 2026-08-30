import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from parser import (
    compute_file_checksum,
    load_existing_checksums,
    save_checksums,
    validate_data_source,
    load_schema,
    validate_trajectory_against_schema,
    extract_metrics_from_trajectory,
    parse_trajectories
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_trajectory():
    """Sample trajectory for testing."""
    return {
        "trajectory_id": "test_traj_001",
        "turns": [
            {
                "turn": 0,
                "action": "move",
                "observation": "board state",
                "reward": 1.0,
                "done": False,
                "legal_moves": ["a1", "b2", "c3"],
                "selected_move": "a1",
                "context_tokens": 100,
                "response_tokens": 50,
                "total_tokens": 150,
                "layer_used": "layer_1",
                "confidence": 0.9
            },
            {
                "turn": 1,
                "action": "move",
                "observation": "updated board",
                "reward": 0.5,
                "done": True,
                "legal_moves": ["d4", "e5"],
                "selected_move": "d4",
                "context_tokens": 200,
                "response_tokens": 75,
                "total_tokens": 275,
                "layer_used": "layer_2",
                "confidence": 0.85
            }
        ]
    }

@pytest.fixture
def sample_schema():
    """Sample schema for testing."""
    return {
        "required": ["trajectory_id", "turns"],
        "properties": {
            "turns": {
                "items": {
                    "required": ["action", "observation"]
                }
            }
        }
    }

def test_compute_file_checksum(temp_dir):
    """Test checksum computation."""
    test_file = temp_dir / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_load_existing_checksums(temp_dir):
    """Test loading existing checksums."""
    checksum_file = temp_dir / "checksums.json"
    test_checksums = {"file1.txt": "abc123", "file2.txt": "def456"}
    
    with open(checksum_file, 'w') as f:
        json.dump(test_checksums, f)
    
    with patch('parser.CHECKSUM_FILE', checksum_file):
        loaded = load_existing_checksums()
        assert loaded == test_checksums

def test_save_checksums(temp_dir):
    """Test saving checksums."""
    checksum_file = temp_dir / "checksums.json"
    test_checksums = {"file1.txt": "abc123"}
    
    with patch('parser.CHECKSUM_FILE', checksum_file):
        save_checksums(test_checksums)
        
        with open(checksum_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_checksums

def test_validate_data_source_missing_dir(temp_dir, caplog):
    """Test validation when raw data directory is missing."""
    with patch('parser.RAW_DATA_DIR', temp_dir / "nonexistent"):
        result = validate_data_source()
        assert result is False
        assert "does not exist" in caplog.text

def test_validate_data_source_empty_dir(temp_dir, caplog):
    """Test validation when raw data directory is empty."""
    (temp_dir / "data").mkdir()
    with patch('parser.RAW_DATA_DIR', temp_dir / "data"):
        result = validate_data_source()
        assert result is False
        assert "No JSON/JSONL files found" in caplog.text

def test_validate_trajectory_against_schema_valid(sample_trajectory, sample_schema):
    """Test schema validation with valid trajectory."""
    is_valid, errors = validate_trajectory_against_schema(sample_trajectory, sample_schema)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_trajectory_against_schema_missing_field(sample_schema):
    """Test schema validation with missing required field."""
    trajectory = {
        "turns": [{"action": "move", "observation": "state"}]
    }
    
    is_valid, errors = validate_trajectory_against_schema(trajectory, sample_schema)
    assert is_valid is False
    assert any("trajectory_id" in error for error in errors)

def test_extract_metrics_from_trajectory(sample_trajectory):
    """Test metric extraction from trajectory."""
    metrics = extract_metrics_from_trajectory(sample_trajectory, "test_001")
    
    assert len(metrics) == 2
    assert metrics[0]['trajectory_id'] == "test_001"
    assert metrics[0]['turn'] == 0
    assert metrics[0]['num_legal_moves'] == 3
    assert metrics[1]['num_legal_moves'] == 2

def test_extract_metrics_from_trajectory_empty_turns():
    """Test metric extraction with empty turns."""
    trajectory = {
        "trajectory_id": "empty_traj",
        "turns": []
    }
    
    metrics = extract_metrics_from_trajectory(trajectory, "empty_traj")
    assert len(metrics) == 0

def test_parse_trajectories_missing_data(caplog):
    """Test parsing when raw data is missing."""
    with patch('parser.RAW_DATA_DIR', Path("/nonexistent")):
        with pytest.raises(FileNotFoundError, match="Real data missing"):
            parse_trajectories()

def test_parse_trajectories_schema_mismatch(temp_dir, sample_schema, caplog):
    """Test parsing with schema mismatch."""
    # Create a trajectory that doesn't match schema
    invalid_trajectory = {
        "turns": [{"action": "move"}]  # Missing required trajectory_id
    }
    
    jsonl_file = temp_dir / "test.jsonl"
    with open(jsonl_file, 'w') as f:
        f.write(json.dumps(invalid_trajectory))
    
    with patch('parser.RAW_DATA_DIR', temp_dir):
        with patch('parser.SCHEMA_FILE', temp_dir / "schema.yaml"):
            with open(temp_dir / "schema.yaml", 'w') as f:
                import yaml
                yaml.dump(sample_schema, f)
            
            with pytest.raises(ValueError, match="Schema mismatch"):
                parse_trajectories()

def test_parse_trajectories_successful(temp_dir, sample_trajectory):
    """Test successful parsing of trajectories."""
    # Create raw data directory
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create processed data directory
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Write valid trajectory
    jsonl_file = raw_dir / "test.jsonl"
    with open(jsonl_file, 'w') as f:
        f.write(json.dumps(sample_trajectory))
    
    # Create valid schema
    schema_file = temp_dir / "contracts"
    schema_file.mkdir(parents=True)
    schema_path = schema_file / "trajectory.schema.yaml"
    schema = {
        "required": ["trajectory_id", "turns"],
        "properties": {
            "turns": {
                "items": {
                    "required": ["action", "observation"]
                }
            }
        }
    }
    import yaml
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    # Mock paths
    with patch('parser.RAW_DATA_DIR', raw_dir):
        with patch('parser.PROCESSED_DATA_DIR', processed_dir):
            with patch('parser.SCHEMA_FILE', schema_path):
                df = parse_trajectories()
                
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 2  # 2 turns
                assert 'trajectory_id' in df.columns
                assert 'turn' in df.columns
                assert 'num_legal_moves' in df.columns

def test_parse_trajectories_empty_result(temp_dir, caplog):
    """Test parsing when no metrics are extracted."""
    # Create raw data directory
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create processed data directory
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Write trajectory with no turns
    jsonl_file = raw_dir / "empty.jsonl"
    with open(jsonl_file, 'w') as f:
        f.write(json.dumps({"trajectory_id": "empty", "turns": []}))
    
    # Create valid schema
    schema_file = temp_dir / "contracts"
    schema_file.mkdir(parents=True)
    schema_path = schema_file / "trajectory.schema.yaml"
    schema = {
        "required": ["trajectory_id", "turns"],
        "properties": {
            "turns": {
                "items": {
                    "required": ["action", "observation"]
                }
            }
        }
    }
    import yaml
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    
    # Mock paths
    with patch('parser.RAW_DATA_DIR', raw_dir):
        with patch('parser.PROCESSED_DATA_DIR', processed_dir):
            with patch('parser.SCHEMA_FILE', schema_path):
                with pytest.raises(ValueError, match="No metrics extracted"):
                    parse_trajectories()
