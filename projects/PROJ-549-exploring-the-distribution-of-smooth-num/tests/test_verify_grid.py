"""
Tests for T023b: Grid Verification
"""
import csv
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the verification logic
# We will test the logic by simulating file creation and running the verification function
# Since main() is the entry point, we test the verify_file logic via the script's behavior

def test_verify_file_missing(tmp_path):
    """Test that verify_file correctly reports missing file."""
    # We need to import the function from the script
    # Since verify_file is inside verify_grid.py, we import it
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import verify_file
    
    import logging
    logger = logging.getLogger("test")
    
    result = verify_file(str(tmp_path / "nonexistent.csv"), "spec", logger)
    
    assert result["exists"] is False
    assert result["error"] is not None
    assert "not found" in result["error"]

def test_verify_file_empty(tmp_path):
    """Test that verify_file correctly reports empty file."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import verify_file
    
    import logging
    logger = logging.getLogger("test")
    
    # Create empty file
    filepath = tmp_path / "empty.csv"
    filepath.write_text("")
    
    result = verify_file(str(filepath), "spec", logger)
    
    assert result["exists"] is True
    assert result["non_zero_rows"] is False
    assert result["error"] is not None

def test_verify_file_schema_mismatch(tmp_path):
    """Test that verify_file detects schema mismatch."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import verify_file
    
    import logging
    logger = logging.getLogger("test")
    
    # Create file with wrong columns
    filepath = tmp_path / "wrong_schema.csv"
    content = "x,y,h\n100,200,300\n"
    filepath.write_text(content)
    
    result = verify_file(str(filepath), "spec", logger)
    
    assert result["exists"] is True
    assert result["schema_valid"] is False
    assert result["error"] is not None
    assert "Schema mismatch" in result["error"]

def test_verify_file_wrong_source(tmp_path):
    """Test that verify_file detects wrong source value."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import verify_file
    
    import logging
    logger = logging.getLogger("test")
    
    # Create file with correct schema but wrong source
    filepath = tmp_path / "wrong_source.csv"
    content = "x,y,h,start_offset,count,density,ratio,source\n100,200,300,0,10,0.1,0.5,plan\n"
    filepath.write_text(content)
    
    result = verify_file(str(filepath), "spec", logger)
    
    assert result["exists"] is True
    assert result["source_valid"] is False
    assert result["error"] is not None
    assert "unexpected values" in result["error"]

def test_verify_file_valid(tmp_path):
    """Test that verify_file passes for valid data."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import verify_file
    
    import logging
    logger = logging.getLogger("test")
    
    # Create valid file
    filepath = tmp_path / "valid.csv"
    content = "x,y,h,start_offset,count,density,ratio,source\n100,200,300,0,10,0.1,0.5,spec\n"
    filepath.write_text(content)
    
    result = verify_file(str(filepath), "spec", logger)
    
    assert result["exists"] is True
    assert result["non_zero_rows"] is True
    assert result["schema_valid"] is True
    assert result["source_valid"] is True
    assert result["error"] is None

def test_main_integration(tmp_path, caplog):
    """Test the main function integration with mock files."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import main
    
    # Create temp directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create mock spec file
    spec_file = data_dir / "density_measurements_spec.csv"
    spec_file.write_text("x,y,h,start_offset,count,density,ratio,source\n100,200,300,0,10,0.1,0.5,spec\n")
    
    # Create mock plan file
    plan_file = data_dir / "density_measurements_plan.csv"
    plan_file.write_text("x,y,h,start_offset,count,density,ratio,source\n100,200,300,0,10,0.1,0.5,plan\n")
    
    output_file = data_dir / "grid_verification.json"
    
    with patch('verify_grid.SPEC_FILE', str(spec_file)):
        with patch('verify_grid.PLAN_FILE', str(plan_file)):
            with patch('verify_grid.OUTPUT_FILE', str(output_file)):
                with patch('verify_grid.sys.exit') as mock_exit:
                    main()
                    
                    # Verify output file was created
                    assert output_file.exists()
                    
                    # Verify content
                    with open(output_file) as f:
                        data = json.load(f)
                    
                    assert data["spec_valid"] is True
                    assert data["plan_valid"] is True
                    
                    # Verify exit code was 0
                    mock_exit.assert_called_once_with(0)

def test_main_failure_integration(tmp_path, caplog):
    """Test the main function when verification fails."""
    import sys
    sys.path.insert(0, 'code')
    from verify_grid import main
    
    # Create temp directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create mock spec file (valid)
    spec_file = data_dir / "density_measurements_spec.csv"
    spec_file.write_text("x,y,h,start_offset,count,density,ratio,source\n100,200,300,0,10,0.1,0.5,spec\n")
    
    # Create mock plan file (missing - will fail)
    plan_file = data_dir / "density_measurements_plan.csv"
    # Intentionally not creating this file
    
    output_file = data_dir / "grid_verification.json"
    
    with patch('verify_grid.SPEC_FILE', str(spec_file)):
        with patch('verify_grid.PLAN_FILE', str(plan_file)):
            with patch('verify_grid.OUTPUT_FILE', str(output_file)):
                with patch('verify_grid.sys.exit') as mock_exit:
                    main()
                    
                    # Verify output file was created
                    assert output_file.exists()
                    
                    # Verify content
                    with open(output_file) as f:
                        data = json.load(f)
                    
                    assert data["spec_valid"] is True
                    assert data["plan_valid"] is False
                    
                    # Verify exit code was 1
                    mock_exit.assert_called_once_with(1)
