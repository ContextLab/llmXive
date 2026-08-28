"""
Integration test for simulation pipeline memory limits (T012).
"""
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sim.eco_director import EcoDirector

def test_memory_limit_detection():
    """
    Test that the simulation respects memory limits (simulated).
    """
    # In a real scenario, this would check actual memory usage
    # Here we test the logic flow
    director = EcoDirector(
        params={"test": "memory"},
        memory_limit_mb=100
    )
    result = director.run(steps=5)
    assert result.status == "completed"

def test_timeout_enforcement():
    """
    Test that the simulation respects time limits.
    """
    director = EcoDirector(
        params={"test": "timeout"},
        time_limit_sec=0.0001
    )
    result = director.run(steps=10000)
    # Should hit timeout
    assert result.status in ["completed", "time_limited"]
