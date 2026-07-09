"""
Unit tests for T014: Export of raw results.
Tests that the export function correctly writes to CSV and handles empty data.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# Assuming the test runs from the project root or code is in PYTHONPATH
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils import generate_checksum
# We will mock the search functions and test the export logic directly
# Since the actual search functions rely on network, we test the export logic with fixtures.

def test_export_raw_results_creates_file():
    """Test that export_raw_results creates the file with correct headers."""
    # Import the function from the module
    # We need to import it from the specific module context
    # Since we can't easily import the internal function if it's not public, 
    # we will simulate the logic here or import if we made it public.
    # Let's assume we can import it from the module if we expose it, 
    # but for now, let's test the logic by re-implementing the export logic in the test 
    # or by importing the module and accessing it.
    
    # Better approach: Import the module and call the function if we expose it.
    # For T014, the task is to implement the export. 
    # Let's assume the function `export_raw_results` is available.
    # If not, we test the `run_search_pipeline` with mocked data.
    
    from code import code_01_search_and_screen # This might fail if file name is 01_search_and_screen.py
    # Let's use importlib to handle the dynamic name
    import importlib.util
    spec = importlib.util.spec_from_file_location("search_script", "code/01_search_and_screen.py")
    search_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(search_module)
    
    export_func = search_module.export_raw_results
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        # Mock data
        mock_studies = [
            {"title": "Study A", "year": 2023, "source": "OpenAlex", "abstract": "Test abstract", "doi": "10.1234/testA"},
            {"title": "Study B", "year": 2022, "source": "arXiv", "abstract": "Another test", "doi": "10.1234/testB"}
        ]
        
        export_func(mock_studies, tmp_path)
        
        # Verify file exists
        assert tmp_path.exists()
        
        # Verify content
        with open(tmp_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['title'] == "Study A"
            assert rows[0]['year'] == "2023"
            assert rows[0]['source'] == "OpenAlex"
            assert rows[0]['DOI'] == "10.1234/testA"
            assert rows[1]['title'] == "Study B"
            
            # Check headers
            assert reader.fieldnames == ["title", "year", "source", "abstract", "DOI"]
            
    finally:
        # Cleanup
        if tmp_path.exists():
            os.remove(tmp_path)

def test_export_empty_list():
    """Test exporting an empty list of studies."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("search_script", "code/01_search_and_screen.py")
    search_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(search_module)
    
    export_func = search_module.export_raw_results
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        export_func([], tmp_path)
        
        assert tmp_path.exists()
        with open(tmp_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            # Headers should still exist
            assert reader.fieldnames == ["title", "year", "source", "abstract", "DOI"]
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)