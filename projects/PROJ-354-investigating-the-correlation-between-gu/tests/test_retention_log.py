"""
Tests for T016: Cohort Retention Log Generation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Mock the config and logging to avoid environment dependencies in tests
@pytest.fixture
def mock_config():
    with patch("code.generate_retention_log.get_path") as mock_get, \
         patch("code.generate_retention_log.ensure_directories") as mock_ensure:
        
        # Create a temporary directory for the test
        temp_dir = tempfile.mkdtemp()
        
        def side_effect(path_str):
            return Path(temp_dir) / path_str
        
        mock_get.side_effect = side_effect
        mock_ensure.return_value = None
        yield temp_dir

@pytest.fixture
def mock_data_files(mock_config):
    """Create fake parquet files for testing."""
    temp_dir = Path(mock_config)
    
    # Create raw data
    raw_path = temp_dir / "data" / "raw" / "microbiome_data.parquet"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_df = pd.DataFrame({"participant_id": range(100)})
    raw_df.to_parquet(raw_path)
    
    # Create filtered data
    filtered_path = temp_dir / "data" / "processed" / "filtered_cohort.parquet"
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df = pd.DataFrame({"participant_id": range(80)})
    filtered_df.to_parquet(filtered_path)
    
    # Create zero-replaced data
    zero_path = temp_dir / "data" / "processed" / "zero_replaced_counts.parquet"
    zero_df = pd.DataFrame({"participant_id": range(80)})
    zero_df.to_parquet(zero_path)
    
    # Create ILR data
    ilr_path = temp_dir / "data" / "processed" / "ilr_coordinates.parquet"
    ilr_df = pd.DataFrame({"participant_id": range(75)})
    ilr_df.to_parquet(ilr_path)
    
    # Create final data
    final_path = temp_dir / "data" / "processed" / "cohort_with_age_groups.parquet"
    final_df = pd.DataFrame({"participant_id": range(75)})
    final_df.to_parquet(final_path)
    
    return temp_dir

def test_retention_log_generation(mock_config, mock_data_files):
    """Test that the retention log is generated with correct counts."""
    # Import after mocking
    from code.generate_retention_log import get_retention_stats
    
    # Re-run the path logic to point to our temp dir
    # We need to re-apply the patch or rely on the fixture setup
    # Since the function uses get_path which is mocked in the fixture, we just call it.
    # However, the fixture only patches the module when imported.
    # We need to import the module inside the test or re-patch.
    
    with patch("code.generate_retention_log.get_path") as mock_get:
        def side_effect(path_str):
            return Path(mock_config) / path_str
        mock_get.side_effect = side_effect
        
        stats = get_retention_stats()
        
        assert stats["raw_count"] == 100
        assert stats["filtered_count"] == 80
        assert stats["zero_replaced_count"] == 80
        assert stats["ilr_count"] == 75
        assert stats["final_count"] == 75
        
        # Check exclusions
        assert stats["exclusions"]["antibiotic_users"] == 20  # 100 - 80
        assert stats["exclusions"]["missing_data"] == 5       # 80 - 75
        
        # Check rate
        assert abs(stats["retention_rate"] - 0.75) < 0.001

def test_retention_log_missing_raw(mock_config):
    """Test behavior when raw data is missing."""
    # Create only processed files
    temp_dir = Path(mock_config)
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    final_df = pd.DataFrame({"participant_id": range(50)})
    (processed_dir / "cohort_with_age_groups.parquet").to_parquet(final_df)
    
    with patch("code.generate_retention_log.get_path") as mock_get:
        def side_effect(path_str):
            return Path(mock_config) / path_str
        mock_get.side_effect = side_effect
        
        stats = get_retention_stats()
        
        assert stats["raw_count"] is None
        assert stats["final_count"] == 50
        assert stats["retention_rate"] == 0.0

def test_retention_log_missing_intermediates(mock_config, mock_data_files):
    """Test behavior when intermediate files are missing."""
    temp_dir = Path(mock_config)
    
    # Remove filtered file
    (temp_dir / "data" / "processed" / "filtered_cohort.parquet").unlink()
    
    with patch("code.generate_retention_log.get_path") as mock_get:
        def side_effect(path_str):
            return Path(mock_config) / path_str
        mock_get.side_effect = side_effect
        
        stats = get_retention_stats()
        
        assert stats["raw_count"] == 100
        assert stats["filtered_count"] == 0 # File not found
        assert stats["final_count"] == 75
        
        # Should fall back to 'other' exclusion
        assert stats["exclusions"]["other"] == 25 # 100 - 75
        assert stats["exclusions"]["antibiotic_users"] == 0
        assert stats["exclusions"]["missing_data"] == 0
