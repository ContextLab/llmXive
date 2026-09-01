"""
Unit tests for code/data/generate_synthetic.py

These tests verify that the synthetic data generator produces
deterministic, correctly formatted output without accessing real hardware.
"""

import os
import sys
import csv
import tempfile
import math

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.generate_synthetic import generate_decay_curve, generate_synthetic_traces
from utils.seeds import reset_seeds_to_default

def test_generate_decay_curve_deterministic():
    """Test that the decay curve is deterministic with the same seed."""
    time_points = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    amplitude = 1.0
    lifetime = 2.0
    noise_level = 0.01
    seed = 12345

    # Generate twice with same parameters
    result1 = generate_decay_curve(time_points, amplitude, lifetime, noise_level, seed)
    result2 = generate_decay_curve(time_points, amplitude, lifetime, noise_level, seed)

    assert result1 == result2, "Decay curve should be deterministic with same seed"

def test_generate_decay_curve_exponential_shape():
    """Test that the decay curve follows an exponential shape (ignoring noise)."""
    time_points = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    amplitude = 1.0
    lifetime = 1.0
    noise_level = 0.0  # No noise for this check
    seed = 42

    result = generate_decay_curve(time_points, amplitude, lifetime, noise_level, seed)

    # Check that values are decreasing
    for i in range(len(result) - 1):
        assert result[i] >= result[i+1], "Exponential decay should be non-increasing"

    # Check that at t=0, value is approximately amplitude
    assert math.isclose(result[0], amplitude, rel_tol=1e-5), "Initial value should match amplitude"

def test_generate_synthetic_traces_format(tmp_path):
    """Test that the generated CSV has the correct format."""
    output_path = os.path.join(tmp_path, "test_traces.csv")
    solvents = [
        {'name': 'test_solvent', 'lifetime_ns': 5.0, 'amplitude': 0.5, 'noise_level': 0.01}
    ]

    generate_synthetic_traces(output_path, solvents, seed=42)

    assert os.path.exists(output_path), "Output file should be created"

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        assert 'solvent_name' in headers, "Missing solvent_name column"
        assert 'time_ns' in headers, "Missing time_ns column"
        assert 'absorbance' in headers, "Missing absorbance column"

        rows = list(reader)
        assert len(rows) > 0, "CSV should contain data rows"

        # Check that solvent name is correct
        assert rows[0]['solvent_name'] == 'test_solvent'

def test_generate_synthetic_traces_multi_solvent(tmp_path):
    """Test generation with multiple solvents."""
    output_path = os.path.join(tmp_path, "test_multi.csv")
    solvents = [
        {'name': 'solvent_A', 'lifetime_ns': 2.0, 'amplitude': 0.4, 'noise_level': 0.01},
        {'name': 'solvent_B', 'lifetime_ns': 5.0, 'amplitude': 0.6, 'noise_level': 0.01}
    ]

    generate_synthetic_traces(output_path, solvents, seed=42)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check that both solvents are present
    solvent_names = set(row['solvent_name'] for row in rows)
    assert 'solvent_A' in solvent_names
    assert 'solvent_B' in solvent_names

def test_synthetic_data_is_not_real():
    """
    Sanity check that the generated data is clearly synthetic.
    This test ensures we are not accidentally loading real data.
    """
    # The generated data uses simple exponential decay with added noise.
    # Real data would have more complex features (instrument response, baseline drift).
    # We verify the simplicity here.
    time_points = [0.0, 1.0, 2.0]
    result = generate_decay_curve(time_points, 1.0, 1.0, 0.0, 42)

    # If noise is 0, it should be exactly exponential
    expected_0 = 1.0 * math.exp(-0.0 / 1.0)
    expected_1 = 1.0 * math.exp(-1.0 / 1.0)
    expected_2 = 1.0 * math.exp(-2.0 / 1.0)

    assert math.isclose(result[0], expected_0, rel_tol=1e-9)
    assert math.isclose(result[1], expected_1, rel_tol=1e-9)
    assert math.isclose(result[2], expected_2, rel_tol=1e-9)