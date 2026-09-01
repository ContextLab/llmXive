import pytest
import pandas as pd
from code.data.descriptors import calculate_size_mismatch, compute_descriptors_dataframe

def test_size_mismatch_calculation():
    # Test known values: Cu (1.28) and Ni (1.25)
    # (1.28 - 1.25) / 1.25 = 0.03 / 1.25 = 0.024
    result = calculate_size_mismatch("Cu", "Ni")
    assert abs(result - 0.024) < 1e-6

def test_size_mismatch_negative():
    # Solute smaller than host
    result = calculate_size_mismatch("Ni", "Cu")
    # (1.25 - 1.28) / 1.28 = -0.03 / 1.28 = -0.0234375
    expected = -0.03 / 1.28
    assert abs(result - expected) < 1e-6

def test_compute_descriptors_dataframe():
    data = {
        'solute_symbol': ['Cu', 'Ni'],
        'host_symbol': ['Ni', 'Cu'],
        'activation_energy_eV': [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    feature_df = compute_descriptors_dataframe(df)
    assert 'size_mismatch' in feature_df.columns
    assert len(feature_df) == 2
