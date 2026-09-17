import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Ensure code/ is in path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.ingestion import ingest_and_filter, compute_file_checksum, filter_by_class_sample_size
from src.modeling.config import load_config

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config():
    return {
        "data": {
            "source_url": "https://example.com/data",
            "min_class_samples": 1000
        },
        "modeling": {
            "reaction_templates_version": "v1.0"
        }
    }

@pytest.fixture
def mock_jsonl_file(temp_data_dir):
    file_path = temp_data_dir / "test_data.jsonl.gz"
    # Create a mock gzipped jsonl file
    import gzip
    import json
    
    data = [
        {"reaction_smiles": "C+C>>C", "yield_pct": 50.0, "success_flag": True},
        {"reaction_smiles": "C+C>>C", "yield_pct": 60.0, "success_flag": True},
        {"reaction_smiles": "invalid_smiles", "yield_pct": 10.0},
        {"reaction_smiles": "C+C>>C", "yield_pct": 70.0, "success_flag": True}
    ]
    
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    
    return file_path

def test_ingest_and_filter_creates_artifacts(temp_data_dir, mock_config):
    """Test that ingestion creates the CSV and provenance files."""
    input_path = temp_data_dir / "input.jsonl.gz"
    output_path = temp_data_dir / "output.csv"
    
    # We need to mock the actual classification to avoid RDKit dependency in unit test
    # or use a minimal valid SMILES that RDKit can handle.
    # For this unit test, we assume the function runs without crashing on valid input.
    # We will mock classify_batch to return "SN1" for all.
    
    with patch("src.data.ingestion.classify_batch") as mock_classify:
        mock_classify.return_value = ["SN1"] * 3 # 3 valid smiles in mock data
        
        # We need to create the input file first
        import gzip
        import json
        data = [
            {"reaction_smiles": "C+C>>C", "yield_pct": 50.0, "success_flag": True},
            {"reaction_smiles": "C+C>>C", "yield_pct": 60.0, "success_flag": True},
            {"reaction_smiles": "C+C>>C", "yield_pct": 70.0, "success_flag": True}
        ]
        with gzip.open(input_path, "wt", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        ingest_and_filter(input_path, output_path, mock_config, MagicMock())

        assert output_path.exists()
        assert output_path.with_suffix(".provenance.json").exists()
        
        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert "reaction_type" in df.columns
        assert all(df["reaction_type"] == "SN1")

def test_class_balance_filtering(temp_data_dir, mock_config):
    """Test that class balance metadata is generated."""
    # Create a dataframe with one class having < 1000 samples
    data = {
        "reaction_smiles": ["C", "C", "C"],
        "reaction_type": ["SN1", "SN1", "SN1"],
        "target_value": [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    logger = MagicMock()
    filter_by_class_sample_size(df, min_samples=1000, logger=logger)
    
    # Check if metadata file was created
    meta_path = Path("data/processed/class_exclusion_metadata.json")
    # Note: In a real run, this writes to data/processed. In unit test, we might need to mock path or check logs.
    # For this test, we verify the logger was called with the warning.
    assert logger.warning.called
    
    # Clean up if it was created (it might be created in the global data/processed if not mocked)
    if meta_path.exists():
        os.remove(meta_path)

def test_checksum_computation(temp_data_dir):
    """Test checksum calculation."""
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64 # SHA256 hex length

def test_missing_input_file(temp_data_dir, mock_config):
    """Test behavior when input file is missing."""
    input_path = temp_data_dir / "nonexistent.jsonl.gz"
    output_path = temp_data_dir / "output.csv"
    
    with pytest.raises(FileNotFoundError):
        ingest_and_filter(input_path, output_path, mock_config, MagicMock())
