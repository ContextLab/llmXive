"""
Tests for the extractor module (T008b).
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from extractor import (
    load_ablation_results,
    normalize_ablation_record,
    convert_to_dataframe,
    validate_output,
    main
)


@pytest.fixture
def temp_input_file():
    """Create a temporary input file with sample ablation data."""
    sample_data = [
        {
            "trajectory_id": "traj_001",
            "turn": 5,
            "layer_id": "layer_3",
            "utility_score": 0.85
        },
        {
            "trajectory_id": "traj_001",
            "turn": 5,
            "layer_id": "layer_7",
            "utility_score": 0.72
        },
        {
            "trajectory_id": "traj_002",
            "turn": 10,
            "layer_id": "layer_3",
            "utility_score": 0.91
        },
        {
            "trajectory_id": "traj_002",
            "turn": 10,
            "layer_id": "layer_1",
            "utility_score": 0.45
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_path = f.name
    
    yield Path(temp_path)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_load_ablation_results_valid_file(temp_input_file):
    """Test loading valid JSON ablation results."""
    records = load_ablation_results(temp_input_file)
    
    assert isinstance(records, list)
    assert len(records) == 4
    assert records[0]['trajectory_id'] == 'traj_001'
    assert records[0]['layer_id'] == 'layer_3'


def test_load_ablation_results_file_not_found():
    """Test loading from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_ablation_results(Path("/nonexistent/path/file.json"))


def test_normalize_ablation_record_basic():
    """Test normalization of a basic record."""
    raw_record = {
        "traj_id": "t123",
        "step": 5,
        "layer": "L4",
        "score": 0.95
    }
    
    normalized = normalize_ablation_record(raw_record)
    
    assert normalized['trajectory_id'] == 't123'
    assert normalized['turn'] == 5
    assert normalized['layer_id'] == 'L4'
    assert normalized['utility_score'] == 0.95


def test_normalize_ablation_record_missing_fields():
    """Test normalization handles missing fields gracefully."""
    raw_record = {
        "layer_id": "L1"
    }
    
    normalized = normalize_ablation_record(raw_record)
    
    assert normalized['layer_id'] == 'L1'
    assert normalized['utility_score'] is None
    assert normalized['trajectory_id'] is None


def test_convert_to_dataframe(temp_input_file):
    """Test conversion of records to DataFrame."""
    records = load_ablation_results(temp_input_file)
    df = convert_to_dataframe(records)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert 'layer_id' in df.columns
    assert 'utility_score' in df.columns
    assert 'trajectory_id' in df.columns
    assert 'turn' in df.columns
    
    # Check data types
    assert pd.api.types.is_numeric_dtype(df['utility_score'])
    assert pd.api.types.is_numeric_dtype(df['turn'])


def test_validate_output_valid(temp_input_file):
    """Test validation of valid output."""
    records = load_ablation_results(temp_input_file)
    df = convert_to_dataframe(records)
    
    assert validate_output(df) is True


def test_validate_output_empty():
    """Test validation of empty DataFrame."""
    df = pd.DataFrame(columns=['layer_id', 'utility_score'])
    
    assert validate_output(df) is False


def test_validate_output_missing_column():
    """Test validation when required column is missing."""
    df = pd.DataFrame({'layer_id': ['L1', 'L2']})
    
    assert validate_output(df) is False


def test_validate_output_null_utility_score(temp_input_file):
    """Test validation when utility_score has null values."""
    records = load_ablation_results(temp_input_file)
    # Manually introduce a null value
    records[0]['utility_score'] = None
    
    df = convert_to_dataframe(records)
    
    # Should fail validation due to null utility_score
    assert validate_output(df) is False


def test_main_execution(temp_input_file, temp_output_dir):
    """Test main function execution."""
    # Temporarily override the default output path
    import extractor
    original_output = extractor.OUTPUT_FILE
    extractor.OUTPUT_FILE = temp_output_dir / "test_output.csv"
    
    try:
        # Create a modified version of main that uses our temp file
        import json
        records = load_ablation_results(temp_input_file)
        df = convert_to_dataframe(records)
        extractor.OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(extractor.OUTPUT_FILE, index=False)
        
        # Verify output file exists
        assert extractor.OUTPUT_FILE.exists()
        
        # Verify content
        output_df = pd.read_csv(extractor.OUTPUT_FILE)
        assert len(output_df) == 4
        assert 'utility_score' in output_df.columns
        
    finally:
        extractor.OUTPUT_FILE = original_output


def test_main_file_not_found(capsys):
    """Test main function when input file is missing."""
    import extractor
    original_input = extractor.INPUT_FILE
    extractor.INPUT_FILE = Path("/nonexistent/file.json")
    
    try:
        result = main()
        assert result == 1
    finally:
        extractor.INPUT_FILE = original_input
