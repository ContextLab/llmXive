"""
Unit tests for T000b: validate_scale_text.py
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.research.validate_scale_text import (
    PRIMARY_SOURCE_TRUTH,
    fetch_scale_items_from_spec,
    compare_items,
    write_validation_report,
    main
)

def test_compare_items_match():
    """Test that identical lists return True."""
    truth = ["Item 1", "Item 2"]
    claimed = ["Item 1", "Item 2"]
    assert compare_items(claimed, truth) is True

def test_compare_items_mismatch():
    """Test that different lists return False."""
    truth = ["Item 1", "Item 2"]
    claimed = ["Item 1", "Item 3"]
    assert compare_items(claimed, truth) is False

def test_compare_items_length_mismatch():
    """Test that lists of different lengths return False."""
    truth = ["Item 1", "Item 2"]
    claimed = ["Item 1"]
    assert compare_items(claimed, truth) is False

def test_fetch_scale_items_json(tmp_path):
    """Test fetching items when they are present in a JSON-like structure in text."""
    spec_content = """
    ## Trust Scale
    The following items are used:
    1. The AI's performance is predictable.
    2. The AI's performance is consistent.
    3. The AI's performance is reliable.
    4. The AI's performance is accurate.
    5. The AI's performance is trustworthy.
    6. The AI's performance is safe.
    7. The AI's performance is effective.
    8. The AI's performance is competent.
    9. The AI's performance is helpful.
    10. The AI's performance is honest.
    11. The AI's performance is benevolent.
    12. The AI's performance is open.
    """
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(spec_content)
    
    items = fetch_scale_items_from_spec(spec_file)
    assert len(items) == 12
    assert items == PRIMARY_SOURCE_TRUTH

def test_fetch_scale_items_text_with_numbers(tmp_path):
    """Test fetching items when they are just text with numbers."""
    spec_content = """
    Scale Items:
    - The AI's performance is predictable.
    - The AI's performance is consistent.
    - The AI's performance is reliable.
    - The AI's performance is accurate.
    - The AI's performance is trustworthy.
    - The AI's performance is safe.
    - The AI's performance is effective.
    - The AI's performance is competent.
    - The AI's performance is helpful.
    - The AI's performance is honest.
    - The AI's performance is benevolent.
    - The AI's performance is open.
    """
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(spec_content)
    
    items = fetch_scale_items_from_spec(spec_file)
    assert len(items) == 12

def test_write_validation_report(tmp_path):
    """Test writing the validation report."""
    output_file = tmp_path / "test_report.json"
    write_validation_report(output_file, "verified", 12)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data["status"] == "verified"
    assert data["items_verified"] == 12

def test_main_success(tmp_path, capsys):
    """Test main function execution when spec is valid."""
    # Create a valid spec
    spec_content = """
    ## Trust Scale
    1. The AI's performance is predictable.
    2. The AI's performance is consistent.
    3. The AI's performance is reliable.
    4. The AI's performance is accurate.
    5. The AI's performance is trustworthy.
    6. The AI's performance is safe.
    7. The AI's performance is effective.
    8. The AI's performance is competent.
    9. The AI's performance is helpful.
    10. The AI's performance is honest.
    11. The AI's performance is benevolent.
    12. The AI's performance is open.
    """
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(spec_content)
    
    # Mock Path.cwd to point to tmp_path
    with patch('code.research.validate_scale_text.Path.cwd') as mock_cwd:
        mock_cwd.return_value = tmp_path
        # We need to create the directory structure expected by main
        (tmp_path / "research").mkdir()
        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "001-perceived-agency-trust").mkdir(parents=True)
        # Move spec to correct location
        spec_file.rename(tmp_path / "specs" / "001-perceived-agency-trust" / "spec.md")
        
        # Mock plan.md to not exist or be empty
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("")

        try:
            main()
            captured = capsys.readouterr()
            assert "Validation Successful" in captured.out
        except SystemExit:
            pytest.fail("main() raised SystemExit unexpectedly")

def test_main_mismatch(tmp_path):
    """Test main function execution when spec has mismatched items."""
    # Create a spec with a wrong item
    spec_content = """
    ## Trust Scale
    1. The AI's performance is predictable.
    2. The AI's performance is consistent.
    3. The AI's performance is reliable.
    4. The AI's performance is accurate.
    5. The AI's performance is trustworthy.
    6. The AI's performance is safe.
    7. The AI's performance is effective.
    8. The AI's performance is competent.
    9. The AI's performance is helpful.
    10. The AI's performance is honest.
    11. The AI's performance is benevolent.
    12. The AI's performance is WRONG.
    """
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(spec_content)
    
    with patch('code.research.validate_scale_text.Path.cwd') as mock_cwd:
        mock_cwd.return_value = tmp_path
        (tmp_path / "research").mkdir()
        (tmp_path / "specs").mkdir(parents=True)
        (tmp_path / "specs" / "001-perceived-agency-trust").mkdir(parents=True)
        spec_file.rename(tmp_path / "specs" / "001-perceived-agency-trust" / "spec.md")
        (tmp_path / "plan.md").write_text("")

        with pytest.raises(SystemExit) as excinfo:
            main()
        assert "Scale text mismatch" in str(excinfo.value)
