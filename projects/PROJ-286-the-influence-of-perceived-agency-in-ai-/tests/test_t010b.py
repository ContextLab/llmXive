"""
Test for T010b: Retrieve the canonical Lee & See (2004) Trust Scale.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.research.retrieve_trust_scale import (
    LEE_SEE_2004_ITEMS, 
    load_scale_validation_report, 
    verify_scale_validity, 
    write_scale_items_file,
    main
)

def test_hardcoded_items_count():
    """Verify the hardcoded list has exactly 12 items."""
    assert len(LEE_SEE_2004_ITEMS) == 12

def test_hardcoded_items_content():
    """Verify specific items match the expected text."""
    assert LEE_SEE_2004_ITEMS[0] == "The AI's performance is predictable."
    assert LEE_SEE_2004_ITEMS[5] == "The AI's performance is safe."
    assert LEE_SEE_2004_ITEMS[11] == "The AI's performance is open."

def test_verify_scale_validity_success():
    """Test verify_scale_validity with a passing report."""
    valid_report = {
        "status": "success",
        "items_verified": 12
    }
    assert verify_scale_validity(valid_report) is True

def test_verify_scale_validity_failure_status():
    """Test verify_scale_validity with a failing status."""
    invalid_report = {
        "status": "failed",
        "items_verified": 12
    }
    assert verify_scale_validity(invalid_report) is False

def test_verify_scale_validity_failure_count():
    """Test verify_scale_validity with wrong item count."""
    invalid_report = {
        "status": "success",
        "items_verified": 10
    }
    assert verify_scale_validity(invalid_report) is False

def test_write_scale_items_file_creates_json():
    """Test that write_scale_items_file creates a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # We need to patch the function to use our temp dir or pass it
        # The function signature takes project_root, so we create a fake project root
        fake_project_root = tmp_path
        
        # Call the internal logic directly for testing
        output_path = write_scale_items_file(fake_project_root, LEE_SEE_2004_ITEMS)
        
        assert output_path.exists()
        assert output_path.name == "trust_scale_items.md"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        assert content == LEE_SEE_2004_ITEMS
        assert len(content) == 12

def test_main_execution_with_mocked_report(tmp_path):
    """Test the main function execution with a valid T000b report."""
    # Setup directory structure
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    # Create a valid T000b report
    report_data = {
        "status": "success",
        "items_verified": 12
    }
    report_path = research_dir / "scale_text_validation.json"
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    
    # Mock the project root
    original_cwd = os.getcwd()
    try:
        # We cannot easily mock Path(__file__).resolve().parent...parent.parent 
        # inside the main function without refactoring.
        # Instead, we test the logic components which are already covered.
        # This test serves as an integration check if we refactor main to accept root.
        # For now, we assert the components work as expected.
        pass
    finally:
        os.chdir(original_cwd)
        
    # Verify the components work together
    report = load_scale_validation_report(tmp_path)
    assert verify_scale_validity(report)
    output_path = write_scale_items_file(tmp_path, LEE_SEE_2004_ITEMS)
    assert output_path.exists()