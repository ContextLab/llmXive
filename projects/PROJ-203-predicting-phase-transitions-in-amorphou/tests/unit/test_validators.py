import pandas as pd
import pytest

# The validators module lives in the ``utils`` package under ``code``.
# The test runner adds the repository root to ``sys.path`` so we can import it directly.
from utils.validators import check_nan, check_physical_bounds


def test_check_nan_detects_nan_columns():
    df = pd.DataFrame({
        "good_col": [1, 2, 3],
        "has_nan": [4, None, 6],
        "also_good": [7, 8, 9],
    })
    nan_cols = check_nan(df)
    assert nan_cols == ["has_nan"], "check_nan should return only columns that contain NaN values"


def test_check_physical_bounds_identifies_out_of_bounds():
    # Create a descriptor row with a mixture of valid and invalid values
    descriptor = pd.Series({
        "rdf_peak_position": 25.0,   # > max (20.0)
        "rdf_peak_width": 0.3,       # within bounds
        "bond_angle_variance": -5.0, # < min (0.0)
        "coordination_number": 5,   # valid
        "Tg": 150.0,                 # valid
        "Tx": 3000.0,                # > max (2500.0)
    })

    out_of_bounds = check_physical_bounds(descriptor)
    # The order is not important; compare as sets
    assert set(out_of_bounds) == {"rdf_peak_position", "bond_angle_variance", "Tx"}