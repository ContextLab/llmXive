"""
Unit tests for T027b: Halt Check logic.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats.halt_check import check_halt_conditions, load_power_analysis

def test_power_sufficient_proceeds():
    """Test that sufficient power returns 0."""
    results = {
        "power_for_r03": 0.85,
        "is_sufficient": True,
        "mdes": 0.25,
        "simulation_seed": 42,
        "simulation_log_path": "logs/power_sim.log"
    }
    assert check_halt_conditions(results) == 0

def test_power_insufficient_low_n_critical():
    """Test that critically low N (N < 15) returns 1."""
    # MDES ~ 0.5 implies N ~ 31 (7.84 / 0.25). Wait, 7.84 / 0.5^2 = 31.
    # To get N < 15, we need MDES > sqrt(7.84/15) ~ 0.72.
    results = {
        "power_for_r03": 0.10,
        "is_sufficient": False,
        "mdes": 0.80,  # High MDES -> Low N
        "simulation_seed": 42,
        "simulation_log_path": "logs/power_sim.log"
    }
    assert check_halt_conditions(results) == 1

def test_power_insufficient_missing_cognitive_proceeds():
    """Test that missing cognitive data (N < 85) returns 0 with warning."""
    # MDES ~ 0.35 implies N ~ 64 (7.84 / 0.35^2). This is < 85.
    results = {
        "power_for_r03": 0.40,
        "is_sufficient": False,
        "mdes": 0.35,
        "simulation_seed": 42,
        "simulation_log_path": "logs/power_sim.log"
    }
    assert check_halt_conditions(results) == 0

def test_missing_file_raises():
    """Test that loading a missing file raises SystemExit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / 'nonexistent.json'
        with pytest.raises(SystemExit):
            load_power_analysis(fake_path)