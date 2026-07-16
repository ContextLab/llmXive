"""
Unit tests for budget_check.py logic.
"""
import pytest
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from pipeline.budget_check import (
    calculate_per_unit_time,
    calculate_max_realizations,
    reduce_configuration,
    run_budget_check,
    MIN_REALIZATIONS
)

def test_calculate_per_unit_time():
    """Test time extraction from pilot metrics."""
    metrics = {"total_time_sec": 120.5}
    assert calculate_per_unit_time(metrics) == 120.5

def test_calculate_max_realizations():
    """Test max runs calculation."""
    # 1 hour budget, 2 min per run -> 30 runs
    assert calculate_max_realizations(3600, 120) == 30
    # Zero time -> infinite
    assert calculate_max_realizations(3600, 0) == 999999

def test_reduce_configuration_fractions():
    """Test reduction priority: fractions first."""
    initial = {"N_realizations": 10, "N_fractions": 10, "N_algos": 3}
    # Total = 300. Max allowed = 100.
    # Should reduce fractions first.
    final, changes = reduce_configuration(initial, 100)
    
    assert final["N_realizations"] == 10  # Unchanged
    assert final["N_algos"] == 3          # Unchanged
    assert final["N_fractions"] <= 3      # Reduced to fit 100 (10*3=30)
    assert any(k == "N_fractions" for k, _, _ in changes)

def test_reduce_configuration_algos():
    """Test reduction priority: algos second."""
    initial = {"N_realizations": 10, "N_fractions": 1, "N_algos": 10}
    # Total = 100. Max allowed = 50.
    # Fractions already 1, should reduce algos.
    final, changes = reduce_configuration(initial, 50)
    
    assert final["N_fractions"] == 1
    assert final["N_realizations"] == 10
    assert final["N_algos"] == 5
    assert any(k == "N_algos" for k, _, _ in changes)

def test_reduce_configuration_realizations():
    """Test reduction priority: realizations last, respects MIN."""
    initial = {"N_realizations": 10, "N_fractions": 1, "N_algos": 1}
    # Total = 10. Max allowed = 5.
    # Should reduce realizations to MIN_REALIZATIONS (30) -> but 10 < 30?
    # Wait, MIN_REALIZATIONS is 30. If initial is 10, it's already below min.
    # Let's test a case where we start above min.
    initial = {"N_realizations": 50, "N_fractions": 1, "N_algos": 1}
    # Total = 50. Max allowed = 40.
    final, changes = reduce_configuration(initial, 40)
    
    assert final["N_realizations"] == 40
    assert final["N_fractions"] == 1
    assert final["N_algos"] == 1

def test_run_budget_check_writes_log():
    """Test that run_budget_check writes run_log.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pilot_log = tmpdir / "pilot_log.json"
        log_output = tmpdir / "run_log.yaml"
        
        # Write mock pilot log
        pilot_log.write_text(json.dumps({"total_time_sec": 60}))
        
        initial_config = {
            "N_realizations": 10,
            "N_fractions": 5,
            "N_algos": 2,
        }
        
        final_config, result = run_budget_check(
            budget_sec=3600,
            initial_config=initial_config,
            pilot_log_path=pilot_log,
            log_path=log_output
        )
        
        assert log_output.exists()
        with open(log_output) as f:
            loaded_log = yaml.safe_load(f)
        
        assert loaded_log["final_config"] == final_config
        assert "reductions" in loaded_log
        assert loaded_log["halted"] is False
