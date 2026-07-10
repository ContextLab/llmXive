"""
Unit tests for Source Verification Task (T011)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import code
from code.utils import logging_setup

# Import the module under test
# We need to import the module directly from the code directory
import importlib.util
spec = importlib.util.spec_from_file_location("source_verification", "code/03_source_verification.py")
source_ver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_ver)

def test_manifest_structure():
    """Test that the manifest has the required fields."""
    manifest = source_ver.verify_source()
    
    assert "search_scope" in manifest
    assert "query_string" in manifest
    assert "results" in manifest
    assert "mode" in manifest
    assert "reason" in manifest
    
    assert manifest["search_scope"] == source_ver.SEARCH_SOURCES
    assert manifest["query_string"] == source_ver.QUERY_STRING

def test_mode_flag_set_correctly():
    """Test that mode is set to 'Data Insufficient' when no dataset is found."""
    manifest = source_ver.verify_source()
    assert manifest["mode"] == "Data Insufficient"

def test_manifest_written_to_disk():
    """Test that the manifest is written to the correct path."""
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_path = tmp_path / "test_manifest.json"
        
        # Patch the OUTPUT_PATH
        original_output_path = source_ver.OUTPUT_PATH
        source_ver.OUTPUT_PATH = output_path
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run main
        source_ver.main()
        
        # Check file exists
        assert output_path.exists()
        
        # Check content
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert "mode" in data
            assert data["mode"] == "Data Insufficient"
        
        # Restore
        source_ver.OUTPUT_PATH = original_output_path