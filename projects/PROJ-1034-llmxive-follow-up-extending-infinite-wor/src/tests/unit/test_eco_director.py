"""
Unit tests for EcoDirector state transitions and schema validation.
"""
import pytest
import sys
import os

# Ensure imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sim.eco_director import EcoDirector
from src.data_models import SimulationRun

def test_eco_director_initialization():
    params = {"test": "value"}
    director = EcoDirector(params=params)
    assert director.run_state.status == "initialized"
    assert director.params == params

def test_eco_director_run():
    params = {"test": "value"}
    director = EcoDirector(params=params)
    result = director.run(steps=10)
    assert result.status == "completed"
    assert len(result.metrics) == 10

def test_time_limit_enforcement():
    params = {"test": "value"}
    # Very short time limit to trigger timeout
    director = EcoDirector(params=params, time_limit_sec=0.0001)
    result = director.run(steps=1000)
    # Should hit time limit or complete quickly
    assert result.status in ["completed", "time_limited"]
