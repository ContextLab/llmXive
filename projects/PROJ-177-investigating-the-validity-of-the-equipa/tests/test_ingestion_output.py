import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import calculate_energy_components, check_z_axis_completeness, main
from config import load_config

@pytest.fixture
def sample_config():
    return {
        'materials': {
            'steel': {'mass': 1.0, 'inertia': 0.5},
            'polymer': {'mass': 0.5, 'inertia': 0.25}
        },
        'default_mass': 1.0,
        'default_inertia': 1.0,
        'gravity': 9.81
    }

@pytest.fixture
def sample_df():
    data = {
        'particle_id': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
        'time': [0.0, 1.0, 2.0, 3.0, 4.0, 0.0, 1.0, 2.0, 3.0, 4.0],
        'x': [0.0, 1.0, 2.0, 3.0, 4.0, 0.0, 0.5, 1.0, 1.5, 2.0],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'z': [0.0, 1.0, 2.0, 3.0, 4.0, 0.0, 1.0, 2.0, 3.0, 4.0],
        'material_type': ['steel', 'steel', 'steel', 'steel', 'steel', 'polymer', 'polymer', 'polymer', 'polymer', 'polymer']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_z():
    data = {
        'particle_id': [1, 1, 1, 1, 1],
        'time': [0.0, 1.0, 2.0, 3.0, 4.0],
        'x': [0.0, 1.0, 2.0, 3.0, 4.0],
        'y': [0.0, 0.0, 0.0, 0.0, 0.0],
        # No z column
        'material_type': ['steel', 'steel', 'steel', 'steel', 'steel']
    }
    return pd.DataFrame(data)

def test_energy_calculation(sample_df, sample_config):
    df = sample_df.copy()
    # Add velocity columns manually for testing
    df['v_x'] = df['x'].diff().fillna(0)
    df['v_y'] = df['y'].diff().fillna(0)
    df['omega_theta'] = 0.0 # No rotation

    result = calculate_energy_components(df, sample_config)

    # Check E_trans for particle 1 (steel, mass=1.0)
    # v_x = 1.0, v_y = 0.0 => v^2 = 1.0 => E_trans = 0.5 * 1.0 * 1.0 = 0.5
    p1_data = result[result['particle_id'] == 1]
    assert all(p1_data['E_trans'] == 0.5)

    # Check E_pot for particle 1 (steel, mass=1.0, g=9.81)
    # z = [0, 1, 2, 3, 4] => E_pot = 1.0 * 9.81 * z
    expected_pot = [0.0, 9.81, 19.62, 29.43, 39.24]
    assert all(p1_data['E_pot'] == expected_pot)

    # Check E_rot (zero in this case)
    assert all(p1_data['E_rot'] == 0.0)

    # Check pot_incomplete is False
    assert all(p1_data['pot_incomplete'] == False)

def test_missing_z_axis(sample_df_missing_z, sample_config):
    df = sample_df_missing_z.copy()
    df['v_x'] = df['x'].diff().fillna(0)
    df['v_y'] = df['y'].diff().fillna(0)
    df['omega_theta'] = 0.0

    result = calculate_energy_components(df, sample_config)

    # Check pot_incomplete is True
    assert all(result['pot_incomplete'] == True)

    # Check E_pot is 0.0 (as per implementation)
    assert all(result['E_pot'] == 0.0)

def test_z_axis_check():
    df_complete = pd.DataFrame({'z': [1.0, 2.0, 3.0]})
    df_incomplete = pd.DataFrame({'x': [1.0, 2.0, 3.0]})

    assert check_z_axis_completeness(df_complete, 1) == True
    assert check_z_axis_completeness(df_incomplete, 1) == False

def test_main_integration(tmp_path, sample_config):
    # Create a mock CSV file
    data_dir = tmp_path / 'data' / 'raw'
    data_dir.mkdir(parents=True)
    csv_file = data_dir / 'tracking.csv'
    csv_file.write_text("particle_id,time,x,y,z,material_type\n1,0.0,0.0,0.0,0.0,steel\n1,1.0,1.0,0.0,1.0,steel\n")

    config_file = tmp_path / 'config.yaml'
    config_file.write_text("""
    materials:
      steel: {mass: 1.0, inertia: 0.5}
    default_mass: 1.0
    default_inertia: 1.0
    gravity: 9.81
    """)

    output_file = tmp_path / 'data' / 'derived' / 'energy_samples.csv'

    # Mock sys.argv for main
    sys.argv = [
        'ingestion',
        '--config', str(config_file),
        '--data-dir', str(data_dir),
        '--output', str(output_file),
        '--verbose'
    ]

    main()

    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert 'particle_id' in df.columns
    assert 'timestamp' in df.columns
    assert 'E_trans' in df.columns
    assert 'E_rot' in df.columns
    assert 'E_pot' in df.columns
    assert 'E_vib' in df.columns
    assert 'pot_incomplete' in df.columns