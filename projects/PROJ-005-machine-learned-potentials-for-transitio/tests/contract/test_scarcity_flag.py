"""
Contract test for T016c: Scarcity Flag Validation.

Tests the logic of `validate_scarcity_flag.py` to ensure it correctly
identifies valid and invalid states of the scarcity flag propagation.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Import the functions to test
from src.data.validate_scarcity_flag import load_scarcity_flag, validate_propagation, get_project_root


class TestScarcityFlagValidation:
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create necessary subdirectories
            (root / "data" / "processed").mkdir(parents=True)
            (root / "code").mkdir(parents=True)
            yield root
    
    def test_flag_exists_and_propagated(self, temp_project_root):
        """Test case where flag exists and matches parquet metadata."""
        # Create flag file
        flag_data = {
            "count": 50,
            "status": "scarcity",
            "threshold": 120
        }
        flag_path = temp_project_root / "data" / "processed" / "data_scarcity_flag.json"
        with open(flag_path, "w") as f:
            json.dump(flag_data, f)
        
        # Create dummy parquet with matching metadata
        df = pd.DataFrame({"node_id": [1, 2], "edge_attr": [0.1, 0.2]})
        # Store metadata in a way pandas respects (attrs or schema)
        # For simplicity in this test, we will mock the metadata check
        parquet_path = temp_project_root / "data" / "processed" / "graphs.parquet"
        df.to_parquet(parquet_path)
        
        # Patch get_project_root to return our temp dir
        with patch("src.data.validate_scarcity_flag.get_project_root", return_value=temp_project_root):
            # We need to mock the metadata reading logic because pandas parquet metadata
            # can be tricky to set up in a simple temp file without custom schema.
            # Instead, we test the logic by patching load_graphs_metadata
            with patch("src.data.validate_scarcity_flag.load_graphs_metadata") as mock_meta:
                mock_meta.return_value = {"scarcity_status": "scarcity"}
                
                result = validate_propagation()
                assert result is True
    
    def test_flag_exists_mismatch(self, temp_project_root):
        """Test case where flag exists but parquet metadata differs."""
        flag_data = {
            "count": 50,
            "status": "scarcity",
            "threshold": 120
        }
        flag_path = temp_project_root / "data" / "processed" / "data_scarcity_flag.json"
        with open(flag_path, "w") as f:
            json.dump(flag_data, f)
        
        with patch("src.data.validate_scarcity_flag.get_project_root", return_value=temp_project_root):
            with patch("src.data.validate_scarcity_flag.load_graphs_metadata") as mock_meta:
                # Parquet says 'normal' but flag says 'scarcity'
                mock_meta.return_value = {"scarcity_status": "normal"}
                
                result = validate_propagation()
                assert result is False
    
    def test_flag_missing_parquet_has_flag(self, temp_project_root):
        """Test case where flag file is missing but parquet indicates scarcity."""
        # No flag file created
        
        with patch("src.data.validate_scarcity_flag.get_project_root", return_value=temp_project_root):
            with patch("src.data.validate_scarcity_flag.load_graphs_metadata") as mock_meta:
                mock_meta.return_value = {"scarcity_status": "scarcity"}
                
                result = validate_propagation()
                assert result is False
    
    def test_flag_missing_parquet_normal(self, temp_project_root):
        """Test case where flag file is missing and parquet is normal."""
        with patch("src.data.validate_scarcity_flag.get_project_root", return_value=temp_project_root):
            with patch("src.data.validate_scarcity_flag.load_graphs_metadata") as mock_meta:
                mock_meta.return_value = {"scarcity_status": "normal"}
                
                result = validate_propagation()
                assert result is True
    
    def test_flag_missing_no_parquet(self, temp_project_root):
        """Test case where neither flag nor parquet exists."""
        with patch("src.data.validate_scarcity_flag.get_project_root", return_value=temp_project_root):
            with patch("src.data.validate_scarcity_flag.load_graphs_metadata", return_value=None):
                result = validate_propagation()
                # Should return False because we can't verify propagation if parquet is missing
                assert result is False