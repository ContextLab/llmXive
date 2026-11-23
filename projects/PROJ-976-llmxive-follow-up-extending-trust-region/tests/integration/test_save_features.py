"""
Integration tests for save_features.py pipeline.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.pipelines.save_features import (
    save_feature_matrix,
    record_feature_checksums,
    compute_file_checksum
)
from code.config import DATA_PROCESSED_DIR


@pytest.fixture
def sample_features():
    """Generate a small set of valid feature dictionaries."""
    return [
        {
            "id": "doc_001",
            "distinct_4_ratio": 0.45,
            "ngram_entropy": 2.3,
            "parse_tree_depth_variance": 1.2,
            "syntactic_variation_score": 0.8,
            "text_length": 150
        },
        {
            "id": "doc_002",
            "distinct_4_ratio": 0.52,
            "ngram_entropy": 2.5,
            "parse_tree_depth_variance": 1.5,
            "syntactic_variation_score": 0.9,
            "text_length": 200
        }
    ]

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def test_save_feature_matrix_creates_file(temp_output_dir, sample_features):
    """Test that save_feature_matrix creates a valid JSONL file."""
    # Mock DATA_PROCESSED_DIR to use temp directory
    with patch('code.pipelines.save_features.DATA_PROCESSED_DIR', str(temp_output_dir)):
        output_path = save_feature_matrix(sample_features, "test_dataset", "train")
        
        assert output_path.exists()
        assert output_path.suffix == ".jsonl"
        
        # Verify content
        with open(output_path, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == len(sample_features)
        
        # Verify JSON validity
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "distinct_4_ratio" in data

def test_save_feature_matrix_handles_nan(temp_output_dir):
    """Test that NaN values are handled correctly (converted to null)."""
    features_with_nan = [
        {
            "id": "doc_001",
            "distinct_4_ratio": float('nan'),
            "ngram_entropy": 2.3
        }
    ]
    
    with patch('code.pipelines.save_features.DATA_PROCESSED_DIR', str(temp_output_dir)):
        output_path = save_feature_matrix(features_with_nan, "test_nan", "train")
        
        with open(output_path, "r") as f:
            data = json.loads(f.read().strip())
        
        assert data["distinct_4_ratio"] is None

def test_record_feature_checksums_updates_state(temp_output_dir, sample_features):
    """Test that checksums are recorded to the state file."""
    # Create a temporary state file path
    state_dir = temp_output_dir.parent.parent / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "PROJ-976-llmxive-follow-up-extending-trust-region.yaml"
    
    # Create a mock state file
    initial_state = """
artifact_hashes:
  existing_dataset: "abc123"
"""
    state_path.write_text(initial_state)
    
    # Save features first
    with patch('code.pipelines.save_features.DATA_PROCESSED_DIR', str(temp_output_dir)):
        output_path = save_feature_matrix(sample_features, "test_record", "train")
        
        # Record checksums
        with patch('code.pipelines.save_features.load_state_file', return_value={"artifact_hashes": {}}):
            with patch('code.pipelines.save_features.save_state_file') as mock_save:
                record_feature_checksums({"test_record": output_path})
                
                # Verify save_state_file was called
                assert mock_save.called
                # Verify the checksum was included in the call
                call_args = mock_save.call_args[0][0]
                assert "artifact_hashes" in call_args
                assert "test_record" in call_args["artifact_hashes"]

def test_compute_file_checksum_consistency(temp_output_dir, sample_features):
    """Test that checksum computation is consistent."""
    with patch('code.pipelines.save_features.DATA_PROCESSED_DIR', str(temp_output_dir)):
        output_path = save_feature_matrix(sample_features, "test_checksum", "train")
        
        checksum1 = compute_file_checksum(output_path)
        checksum2 = compute_file_checksum(output_path)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length