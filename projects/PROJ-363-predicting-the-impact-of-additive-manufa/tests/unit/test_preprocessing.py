import pytest
import pandas as pd
import numpy as np
from code.preprocess import normalize_columns, handle_ev_fallback
from code.utils import set_seed


@pytest.fixture
def sample_data():
    set_seed(42)
    data = {
        "laser_power": [100, 200, 300, np.nan],
        "scan_speed": [500, 600, 700, 800],
        "hatch_spacing": [100, 110, 120, 130],
        "layer_thickness": [30, 35, 40, 45],
        "porosity": [0.1, 0.2, 0.3, 0.4],
    }
    return pd.DataFrame(data)


def test_normalize_columns(sample_data):
    """Test that normalization scales data to [0, 1]."""
    normalized = normalize_columns(
        sample_data, ["laser_power", "scan_speed", "hatch_spacing", "layer_thickness"]
    )
    for col in ["laser_power", "scan_speed", "hatch_spacing", "layer_thickness"]:
        assert normalized[col].min() >= 0.0
        assert normalized[col].max() <= 1.0


def test_handle_ev_fallback():
    """Test fallback logic for Volumetric Energy Density."""
    # Case 1: Raw parameters present
    data_raw = pd.DataFrame({
        "laser_power": [100],
        "scan_speed": [500],
        "hatch_spacing": [100],
        "layer_thickness": [30],
    })
    result_raw = handle_ev_fallback(data_raw)
    assert "energy_density" in result_raw.columns
    expected_ev = (100 * 1000) / (500 * 100 * 30) * 1000000  # Approximate formula
    assert np.isclose(result_raw["energy_density"].iloc[0], expected_ev, rtol=0.1)

    # Case 2: Existing EV column
    data_ev = pd.DataFrame({
        "VolumetricEnergyDensity": [50.0],
        "laser_power": [100],
    })
    result_ev = handle_ev_fallback(data_ev)
    assert "energy_density" in result_ev.columns
    assert result_ev["energy_density"].iloc[0] == 50.0
