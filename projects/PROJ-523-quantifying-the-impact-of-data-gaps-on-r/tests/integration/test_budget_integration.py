"""
Integration test for the budget check pipeline.
Verifies end-to-end flow from pilot log to final config.
"""
import pytest
import json
import yaml
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from pipeline.budget_check import run_budget_check
from config import DATA_RESULTS_DIR

def test_budget_check_integration():
    """
    Simulate a full budget check scenario.
    1. Create a pilot log.
    2. Run budget check with a tight budget.
    3. Verify log is written and config is reduced.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pilot_log = tmpdir / "pilot_log.json"
        run_log = tmpdir / "run_log.yaml"
        
        # Simulate a slow pilot (5 mins per run)
        pilot_log.write_text(json.dumps({
            "total_time_sec": 300.0,
            "realizations_ran": 1,
            "algo": "harmonic_interp",
            "gap_fraction": 0.1
        }))
        
        # Budget: 1 hour (3600s) -> Max 12 runs
        initial_config = {
            "N_realizations": 20,
            "N_fractions": 5,
            "N_algos": 3
        }
        # Total initial runs: 20 * 5 * 3 = 300
        
        final_config, result = run_budget_check(
            budget_sec=3600,
            initial_config=initial_config,
            pilot_log_path=pilot_log,
            log_path=run_log
        )
        
        # Verify reduction happened
        assert final_config["N_realizations"] * final_config["N_fractions"] * final_config["N_algos"] <= 12
        
        # Verify log file
        assert run_log.exists()
        with open(run_log) as f:
            log_data = yaml.safe_load(f)
        
        assert log_data["budget_sec"] == 3600
        assert log_data["per_unit_time_sec"] == 300.0
        assert log_data["max_total_runs"] == 12
        assert len(log_data["reductions"]) > 0