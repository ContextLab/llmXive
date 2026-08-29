"""
Unit tests for run_experiment CLI and display functions.
"""
import json
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.cli.run_experiment import display_axis_output

def test_display_axis_output_format(capsys):
    """Test that display_axis_output prints correct format."""
    coarse = {"character": "Harry", "axis_name": "Coarse", "description": "Brave"}
    fine = {"character": "Harry", "axis_name": "Fine", "description": "Specific brave act"}
    
    display_axis_output(coarse, fine)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify structure
    assert "AXIS OUTPUT" in output
    assert "--- COARSE AXIS ---" in output
    assert "--- FINE AXIS ---" in output
    
    # Verify JSON content is present
    assert "Harry" in output
    assert "Brave" in output
    
    # Verify both objects are printed
    coarse_str = json.dumps(coarse)
    fine_str = json.dumps(fine)
    assert coarse_str in output or "Coarse" in output
    assert fine_str in output or "Fine" in output

def test_display_axis_output_empty_dict(capsys):
    """Test display with empty dictionaries."""
    coarse = {}
    fine = {}
    
    display_axis_output(coarse, fine)
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "AXIS OUTPUT" in output
    assert "{}" in output
