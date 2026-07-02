"""
Tests for run_experiment.py
"""
import pytest
import sys
from pathlib import Path
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_experiment import parse_args, parse_agent_counts, generate_synthetic_game_data, compute_game_metrics

def test_parse_agent_counts():
    """Test parsing of agent counts."""
    assert parse_agent_counts("5") == [5]
    assert parse_agent_counts("3,5,7") == [3, 5, 7]
    assert parse_agent_counts("2, 4, 6") == [2, 4, 6]

def test_generate_synthetic_game_data():
    """Test synthetic game generation."""
    games = generate_synthetic_game_data(
        num_games=10,
        num_agents=3,
        context_condition="full",
        seed=42
    )
    assert len(games) == 10
    assert all(g["num_agents"] == 3 for g in games)
    assert all(g["context_condition"] == "full" for g in games)

def test_compute_game_metrics():
    """Test metric computation."""
    games = generate_synthetic_game_data(
        num_games=5,
        num_agents=3,
        context_condition="limited",
        threshold=128,
        seed=42
    )
    records = compute_game_metrics(games, "limited")
    
    assert len(records) == 5
    assert all("game_id" in r for r in records)
    assert all("specialization_index" in r for r in records)
    assert all("retrieval_efficiency" in r for r in records)
    assert all(r["context_condition"] == "limited" for r in records)
    assert all(r["agent_count"] == 3 for r in records)

def test_limited_context_threshold():
    """Test that limited context uses threshold."""
    games = generate_synthetic_game_data(
        num_games=5,
        num_agents=3,
        context_condition="limited",
        threshold=256,
        seed=42
    )
    assert all(g["context_threshold"] == 256 for g in games)