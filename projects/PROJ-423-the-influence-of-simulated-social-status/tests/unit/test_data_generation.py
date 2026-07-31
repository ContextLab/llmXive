"""
Unit tests for data generation logic.

Verifies that data generation is deterministic given a fixed seed
and that the output structure matches expectations.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Ensure code/ is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from generate_data import generate_synthetic_data
from utils import set_seed

def test_deterministic_output():
    """Verify that the same seed produces the same data."""
    seed_val = 42
    n = 50
    
    # Generate first time
    set_seed(seed_val)
    df1 = generate_synthetic_data(
        n_participants=n,
        status_effect_size=0.5,
        behavior_effect_size=0.3,
        interaction_effect_size=0.2,
        random_seed=seed_val
    )
    
    # Generate second time
    set_seed(seed_val)
    df2 = generate_synthetic_data(
        n_participants=n,
        status_effect_size=0.5,
        behavior_effect_size=0.3,
        interaction_effect_size=0.2,
        random_seed=seed_val
    )
    
    # Compare
    assert df1.equals(df2), "Data generation is not deterministic with fixed seed"
    assert len(df1) == n, f"Expected {n} participants, got {len(df1)}"

def test_between_subjects_design():
    """Verify that each participant has exactly one observation."""
    df = generate_synthetic_data(n_participants=100, random_seed=999)
    assert df["participant_id"].is_unique, "Between-subjects design violated: duplicate participant IDs"
    
def test_required_columns_present():
    """Verify that the output contains all required columns."""
    df = generate_synthetic_data(n_participants=10, random_seed=123)
    expected_cols = ["participant_id", "status_level", "observed_behavior", "risk_taking_score"]
    assert all(col in df.columns for col in expected_cols), "Missing required columns"
    
def test_valid_status_levels():
    """Verify that status levels are strictly High or Low."""
    df = generate_synthetic_data(n_participants=100, random_seed=456)
    valid_levels = {"High", "Low"}
    assert set(df["status_level"].unique()).issubset(valid_levels), "Invalid status levels detected"

def test_valid_behaviors():
    """Verify that observed behaviors are strictly Risky or Conservative."""
    df = generate_synthetic_data(n_participants=100, random_seed=789)
    valid_behaviors = {"Risky", "Conservative"}
    assert set(df["observed_behavior"].unique()).issubset(valid_behaviors), "Invalid behaviors detected"
