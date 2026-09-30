import pytest
import time
import signal
import threading
from unittest.mock import patch, MagicMock
from code.src.simulation.run_simulation import run_with_timeout, TimeoutError

def slow_function(duration):
    """Simulates a slow computation."""
    time.sleep(duration)
    return "completed"

def test_timeout_triggers():
    """Test that timeout triggers when function takes too long."""
    timeout = 0.5
    duration = 1.0
    
    with pytest.raises(TimeoutError):
        run_with_timeout(slow_function, args=(duration,), timeout=timeout)

def test_timeout_does_not_trigger():
    """Test that timeout does not trigger when function completes in time."""
    timeout = 2.0
    duration = 0.5
    
    result = run_with_timeout(slow_function, args=(duration,), timeout=timeout)
    assert result == "completed"

def test_timeout_enforcement_in_simulation():
    """
    Integration test: Simulate a simulation that sleeps longer than timeout.
    Verifies that the run is flagged and logged correctly.
    """
    from code.src.simulation.run_simulation import run_simulation_core
    from code.src.utils.logging import get_run_log
    import json
    from pathlib import Path
    
    # Mock a graph
    G = MagicMock()
    G.number_of_nodes.return_value = 10
    
    config = {
        "global_seed": 42,
        "simulation_params": {
            "num_steps": 100,
            "temperature": 1.0,
            "coupling": 1.0
        },
        "simulation_timeout_seconds": 0.1  # Very short timeout
    }
    
    # Mock the simulation step to sleep
    with patch('code.src.simulation.run_simulation.run_simulation_step') as mock_step:
        # Make the step take longer than timeout
        def slow_step(*args, **kwargs):
            time.sleep(0.5)
            return args[1], 0.0
        
        mock_step.side_effect = slow_step
        
        run_id = "test_timeout_run"
        
        # Clear previous logs for this run_id
        log_file = Path("data/run_log.json")
        if log_file.exists():
            log_file.unlink()
        
        with pytest.raises(TimeoutError):
            run_with_timeout(run_simulation_core, args=(G, config, run_id), timeout=0.2)
        
        # Verify log entry
        log_entries = get_run_log()
        timeout_entry = None
        for entry in log_entries:
            if entry.get("run_id") == run_id and entry.get("event_type") == "timeout_reached":
                timeout_entry = entry
                break
        
        assert timeout_entry is not None, "Timeout event should be logged"
        assert timeout_entry["status"] == "timeout_exceeded"
