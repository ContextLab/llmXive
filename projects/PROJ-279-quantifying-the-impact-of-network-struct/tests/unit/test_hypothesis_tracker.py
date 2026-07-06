"""
Unit tests for hypothesis_tracker.py (Task T037).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock the env_config to return a temporary directory
@pytest.fixture
def temp_processed_dir(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return tmp_path

def test_determine_hypothesis_status_regression_missing(temp_processed_dir):
    """Test H-001 and H-002 are UNTESTABLE when regression did not run."""
    from hypothesis_tracker import determine_hypothesis_status
    
    # Simulate no regression results
    regression_results = None
    descriptor_availability = {
        "ring_stats": True,
        "vdos_missing": False
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-001"]["status"] == "UNTESTABLE"
    assert status["H-002"]["status"] == "UNTESTABLE"
    assert status["H-003"]["status"] == "TESTED" # Ring stats exist
    assert status["H-004"]["status"] == "UNTESTABLE" # Needs regression

def test_determine_hypothesis_status_vdos_missing(temp_processed_dir):
    """Test H-001 is UNTESTABLE when VDOS is missing but regression ran."""
    from hypothesis_tracker import determine_hypothesis_status
    
    # Simulate regression ran (k available) but VDOS missing
    regression_results = {"r2": 0.5}
    descriptor_availability = {
        "ring_stats": True,
        "vdos_missing": True
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-001"]["status"] == "UNTESTABLE" # No VDOS
    assert status["H-002"]["status"] == "TESTED" # k and Topology exist
    assert status["H-003"]["status"] == "TESTED"
    assert status["H-004"]["status"] == "TESTED" # k and Topology exist

def test_determine_hypothesis_status_full_success(temp_processed_dir):
    """Test all hypotheses are TESTED when everything is available."""
    from hypothesis_tracker import determine_hypothesis_status
    
    regression_results = {"r2": 0.8}
    descriptor_availability = {
        "ring_stats": True,
        "vdos_missing": False
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-001"]["status"] == "TESTED"
    assert status["H-002"]["status"] == "TESTED"
    assert status["H-003"]["status"] == "TESTED"
    assert status["H-004"]["status"] == "TESTED"

def test_determine_hypothesis_status_no_ring_stats(temp_processed_dir):
    """Test H-002 and H-004 fail if ring stats are missing."""
    from hypothesis_tracker import determine_hypothesis_status
    
    regression_results = {"r2": 0.5}
    descriptor_availability = {
        "ring_stats": False,
        "vdos_missing": False
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-002"]["status"] == "FAILED"
    assert status["H-004"]["status"] == "FAILED"
    assert status["H-003"]["status"] == "FAILED"
