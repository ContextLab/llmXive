import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.counterbalance import generate_counterbalance_assignments
from code.utils.logging import get_log_path

def test_generate_counterbalance_assignments_structure():
    """Test that the generated DataFrame has the correct columns."""
    df = generate_counterbalance_assignments(seed=42, n_participants=10)
    
    assert "participant_id" in df.columns
    assert "session_order" in df.columns
    assert len(df) == 10

def test_generate_counterbalance_assignments_distribution():
    """Test that the assignment is approximately 50/50 split."""
    df = generate_counterbalance_assignments(seed=42, n_participants=100)
    
    low_high_count = len(df[df["session_order"] == "Low-High"])
    high_low_count = len(df[df["session_order"] == "High-Low"])
    
    # Should be exactly 50/50 for even numbers
    assert low_high_count == 50
    assert high_low_count == 50

def test_generate_counterbalance_assignments_unique_ids():
    """Test that all participant IDs are unique."""
    df = generate_counterbalance_assignments(seed=42, n_participants=50)
    
    assert df["participant_id"].is_unique
    assert len(df["participant_id"]) == 50

def test_generate_counterbalance_assignments_format():
    """Test that participant IDs are formatted correctly (P001, P002, etc.)."""
    df = generate_counterbalance_assignments(seed=42, n_participants=5)
    
    expected_ids = ["P001", "P002", "P003", "P004", "P005"]
    assert list(df["participant_id"]) == expected_ids

def test_counterbalance_strategy_log_exists():
    """Test that the counterbalance strategy log is created."""
    from code.data.counterbalance import main
    import logging
    
    # Run the main function to generate the log
    main()
    
    # Check if the log file exists
    log_path = get_log_path() / "counterbalance_strategy.log"
    assert log_path.exists(), f"Log file not found at {log_path}"
    
    # Check if the log file contains expected content
    content = log_path.read_text()
    assert "AB/BA Design" in content
    assert "Low-High" in content
    assert "High-Low" in content
    assert "seed" in content.lower() or "42" in content