"""
Tests for T002b: Fetch ERA5 Subset
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.fetch_era_subset import load_bounding_box, ensure_directories, fetch_tile

def test_ensure_directories():
    """Test that output directory is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock project_root to point to temp dir
        import code.fetch_era_subset as module
        original_root = module.project_root
        module.project_root = Path(tmpdir)
        
        try:
            output_dir = ensure_directories()
            assert output_dir.exists()
            assert output_dir.is_dir()
            assert output_dir.name == "era5_raw_chunks"
        finally:
            module.project_root = original_root

def test_load_bounding_box_missing():
    """Test error handling when bbox file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import code.fetch_era_subset as module
        original_root = module.project_root
        module.project_root = Path(tmpdir)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_bounding_box()
        finally:
            module.project_root = original_root

def test_load_bounding_box_valid(tmp_path):
    """Test loading a valid bounding box."""
    # Create a mock bbox file
    bbox_data = {
        "north": 60.0,
        "south": 40.0,
        "east": 10.0,
        "west": -10.0
    }
    
    data_dir = tmp_path / "data" / "external"
    data_dir.mkdir(parents=True)
    bbox_file = data_dir / "bounding_box.json"
    bbox_file.write_text(json.dumps(bbox_data))
    
    import code.fetch_era_subset as module
    original_root = module.project_root
    module.project_root = tmp_path
    
    try:
        # This would fail because the path construction expects 'data/external' relative to root
        # We need to adjust the test to match the actual implementation's path logic
        # The implementation uses: project_root / "data" / "external" / "bounding_box.json"
        result = load_bounding_box()
        assert result == bbox_data
    finally:
        module.project_root = original_root

def test_fetch_tile_rate_limit_handling():
    """Test exponential backoff on rate limit errors."""
    with patch('code.fetch_era_subset.cdsapi.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate rate limit error then success
        error = Exception("429 Too Many Requests")
        mock_client.retrieve.side_effect = [error, None]
        
        import code.fetch_era_subset as module
        original_root = module.project_root
        with tempfile.TemporaryDirectory() as tmpdir:
            module.project_root = Path(tmpdir)
            try:
                bbox = {"north": 50, "south": 40, "east": 0, "west": -10}
                output_dir = Path(tmpdir) / "data" / "raw" / "era5_raw_chunks"
                output_dir.mkdir(parents=True)
                
                # This should retry and eventually succeed
                result = fetch_tile(
                    mock_client, 
                    "2016", "01", "01", "00:00", 
                    bbox, 
                    output_dir
                )
                assert result.exists()
                # Verify retrieve was called twice (once fail, once success)
                assert mock_client.retrieve.call_count == 2
            finally:
                module.project_root = original_root