"""
Unit tests for harmonize_datasets.py.

These tests verify the logic of mapping participant IDs, aligning condition labels,
and generating the unified metadata structure without requiring the full dataset.
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_download.harmonize_datasets import (
    harmonize_participant_id,
    align_condition_labels,
    harmonize_datasets,
    DATASET_CONFIG
)

def test_harmonize_participant_id():
    """Test that participant IDs are correctly prefixed."""
    # Test with 'sub-' prefix
    result = harmonize_participant_id("sub-01", "ds000246", "exc")
    assert result == "exc_01", f"Expected 'exc_01', got '{result}'"
    
    # Test without 'sub-' prefix
    result = harmonize_participant_id("01", "ds004738", "rew")
    assert result == "rew_01", f"Expected 'rew_01', got '{result}'"
    
    # Test with hyphens
    result = harmonize_participant_id("sub-01-02", "ds000246", "exc")
    assert result == "exc_01_02", f"Expected 'exc_01_02', got '{result}'"

def test_align_condition_labels():
    """Test condition mapping for both datasets."""
    # ds000246 (Exclusion)
    assert align_condition_labels("exclusion", "ds000246", "exclusion") == "exclusion"
    assert align_condition_labels("inclusion", "ds000246", "exclusion") == "inclusion"
    assert align_condition_labels("Exclude", "ds000246", "exclusion") == "exclusion" # Case insensitive
    
    # ds004738 (Reward)
    assert align_condition_labels("win", "ds004738", "reward") == "reward_receipt"
    assert align_condition_labels("loss", "ds004738", "reward") == "no_reward"
    assert align_condition_labels("anticipation", "ds004738", "reward") == "reward_ant"
    
    # Unknown condition
    assert align_condition_labels("unknown", "ds000246", "exclusion") is None

def test_harmonize_datasets_integration():
    """Test the full harmonization pipeline with mock data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock directory structure
        raw_dir = tmp_path / "raw-fmri"
        raw_dir.mkdir()
        
        # Mock ds000246
        ds1_dir = raw_dir / "ds000246"
        ds1_dir.mkdir()
        participants1 = ds1_dir / "participants.tsv"
        participants1.write_text("participant_id\tage\tsex\nsub-01\t25\tF\nsub-02\t30\tM\n")
        
        # Mock ds004738
        ds2_dir = raw_dir / "ds004738"
        ds2_dir.mkdir()
        participants2 = ds2_dir / "participants.tsv"
        participants2.write_text("participant_id\tage\tsex\nsub-03\t22\tF\nsub-04\t28\tM\n")
        
        # Create output directory
        out_dir = tmp_path / "processed-fmri"
        out_dir.mkdir()
        
        # Mock config loader to return known IDs
        with patch('code.data_download.harmonize_datasets.get_all_dataset_ids') as mock_get_ids:
            mock_get_ids.return_value = ["ds000246", "ds004738"]
            with patch('code.data_download.harmonize_datasets.get_config') as mock_get_config:
                mock_get_config.return_value = {}
                
                output_file = harmonize_datasets(raw_dir, out_dir)
                
                assert output_file.exists(), "Output file was not created"
                
                # Verify content
                with open(output_file, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"
                
                # Check specific mappings
                ids = [r['unified_participant_id'] for r in rows]
                assert "exc_01" in ids
                assert "exc_02" in ids
                assert "rew_03" in ids
                assert "rew_04" in ids
                
                # Check covariate tag
                for row in rows:
                    assert 'dataset_id' in row
                    assert row['covariate_dataset_id'] in ['ds000246', 'ds004738']

if __name__ == "__main__":
    test_harmonize_participant_id()
    test_align_condition_labels()
    test_harmonize_datasets_integration()
    print("All tests passed.")
