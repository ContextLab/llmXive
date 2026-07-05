import pytest
import json
import os
from pathlib import Path
from code.data_availability_check import check_url_availability, run_checks, main
from code.physics.fallback_data import get_planck_constants, get_xenon1t_limits, get_lep_limits

def test_fallback_data_loads():
    """Test that fallback data can be loaded without network."""
    planck = get_planck_constants()
    assert "Omega_c_h2" in planck
    assert planck["Omega_c_h2"] == 0.120

    xenon_masses, xenon_sigmas = get_xenon1t_limits()
    assert len(xenon_masses) > 0
    assert len(xenon_sigmas) > 0
    assert xenon_masses[0] == 1.0

    lep_rules = get_lep_limits()
    assert len(lep_rules) > 0
    assert "mediator_mass_min" in lep_rules[0]

def test_url_check_logic():
    """Test the URL check function logic (mocked for CI)."""
    # We expect this to fail in a restricted environment, but it should return a tuple
    is_avail, msg = check_url_availability("https://example.com", timeout=1)
    # The function should always return a tuple of (bool, str)
    assert isinstance(is_avail, bool)
    assert isinstance(msg, str)

def test_report_generation(tmp_path):
    """Test that run_checks generates a report file."""
    # Run checks (will likely fail to fetch, but should generate report)
    results = run_checks(output_dir=str(tmp_path))
    
    report_path = Path(tmp_path) / "data_availability_report.json"
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    assert "sources" in data
    assert "Planck" in data["sources"]
    assert "Xenon1T" in data["sources"]
    assert "LEP" in data["sources"]
    assert "fallback_strategy" in data["sources"]["Planck"]
    assert "summary" in data
    assert data["summary"]["total"] == 3