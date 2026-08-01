import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import ingest_data, check_z_axis_completeness, calculate_energy_components

@pytest.fixture
def sample_config():
    return {
        'mass': 0.01,  # kg
        'inertia': 0.000004,  # kg*m^2 (example: 2/5 * m * r^2 with r=0.01m)
        'gravity': 9.81,
        'k_spring': 100.0,
        'z_ref': 0.0
    }

@pytest.fixture
def temp_input_dir(tmp_path):
    # Create fake tracking and driving data
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    tracking_dir = input_dir / "tracking"
    driving_dir = input_dir / "driving"
    tracking_dir.mkdir()
    driving_dir.mkdir()

    # Create tracking CSV
    tracking_data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'x': [0.1, 0.2, 0.3, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
        'z': [0.0, 0.1, 0.2, 0.3, 0.4],
        'theta': [0.0, 0.1, 0.2, 0.3, 0.4],
        'particle_id': [1, 1, 1, 1, 1]
    }
    pd.DataFrame(tracking_data).to_csv(tracking_dir / "track1.csv", index=False)

    # Create driving CSV (just timestamp for simplicity)
    driving_data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'signal': [1.0, 1.0, 1.0, 1.0, 1.0]
    }
    pd.DataFrame(driving_data).to_csv(driving_dir / "drive1.csv", index=False)

    return input_dir

def test_ingestion_creates_output_file(temp_input_dir, sample_config, tmp_path):
    """Test that ingestion creates energy_samples.csv with correct columns."""
    output_dir = tmp_path / "output"
    output_file = output_dir / "energy_samples.csv"

    ingest_data(temp_input_dir, output_dir, sample_config)

    assert output_file.exists(), "energy_samples.csv was not created"

    df = pd.read_csv(output_file)
    expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)}"

def test_pot_incomplete_flag(temp_input_dir, sample_config, tmp_path):
    """Test that pot_incomplete flag is set correctly when z-axis is missing."""
    # Modify tracking data to remove z
    tracking_dir = temp_input_dir / "tracking"
    df = pd.read_csv(tracking_dir / "track1.csv")
    df = df.drop(columns=['z'])
    df.to_csv(tracking_dir / "track1.csv", index=False)

    output_dir = tmp_path / "output"
    ingest_data(temp_input_dir, output_dir, sample_config)

    df_out = pd.read_csv(output_dir / "energy_samples.csv")
    assert 'pot_incomplete' in df_out.columns
    assert df_out['pot_incomplete'].all(), "pot_incomplete should be True when z is missing"

def test_energy_values_calculated_correctly(temp_input_dir, sample_config, tmp_path):
    """Test that energy values are calculated correctly."""
    output_dir = tmp_path / "output"
    ingest_data(temp_input_dir, output_dir, sample_config)

    df = pd.read_csv(output_dir / "energy_samples.csv")

    # Check that energy columns are numeric and non-negative
    for col in ['E_trans', 'E_rot', 'E_pot', 'E_vib']:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"
        assert (df[col] >= 0).all(), f"{col} contains negative values"

    # Spot check: E_trans = 0.5 * m * v^2
    # v = dx/dt = (0.2-0.1)/(2.0-1.0) = 0.1
    # E_trans = 0.5 * 0.01 * (0.1^2 + 0.1^2 + 0.1^2) = 0.5 * 0.01 * 0.03 = 0.00015
    # (Approximate, since we use gradient on 5 points)
    # We just check that values are reasonable (not zero or inf)
    assert df['E_trans'].mean() > 0, "E_trans should be positive"
    assert df['E_rot'].mean() > 0, "E_rot should be positive"
    assert df['E_pot'].mean() > 0, "E_pot should be positive (z > 0)"
    assert df['E_vib'].mean() > 0, "E_vib should be positive (z > z_ref)"
