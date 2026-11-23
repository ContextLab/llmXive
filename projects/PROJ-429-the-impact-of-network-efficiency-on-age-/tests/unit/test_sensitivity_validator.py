import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Import the functions to test
# Note: We assume the module is named sensitivity_validator based on the API surface provided
# If the import path differs, adjust accordingly.
try:
    from code.stats.sensitivity_validator import (
        load_csv_if_exists,
        calculate_overall_stability,
        validate_density_stability,
        validate_artifact_stability
    )
except ImportError:
    # Fallback if running tests in a different context
    import sys
    sys.path.insert(0, 'code')
    from stats.sensitivity_validator import (
        load_csv_if_exists,
        calculate_overall_stability,
        validate_density_stability,
        validate_artifact_stability
    )


class TestLoadCsvIfExists:
    def test_load_existing_csv(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n3,4")
        df = load_csv_if_exists(csv_file)
        assert not df.empty
        assert list(df.columns) == ['a', 'b']
        assert len(df) == 2

    def test_load_missing_csv(self, tmp_path):
        csv_file = tmp_path / "nonexistent.csv"
        df = load_csv_if_exists(csv_file)
        assert df.empty


class TestCalculateOverallStability:
    def test_both_stable(self):
        assert calculate_overall_stability(True, True) is True

    def test_density_unstable(self):
        assert calculate_overall_stability(False, True) is False

    def test_artifact_unstable(self):
        assert calculate_overall_stability(True, False) is False

    def test_both_unstable(self):
        assert calculate_overall_stability(False, False) is False


class TestValidateDensityStability:
    def test_all_stable(self):
        df = pd.DataFrame({'is_stable': [True, True, True]})
        assert validate_density_stability(df) is True

    def test_mixed_stable(self):
        # 2 out of 3 stable -> 0.66 < 0.8 -> False
        df = pd.DataFrame({'is_stable': [True, True, False]})
        assert validate_density_stability(df) is False

    def test_majority_stable(self):
        # 4 out of 5 stable -> 0.8 >= 0.8 -> True (if logic uses > 0.8, this might be False, but usually >= is used for "majority")
        # Adjusting test to match implementation: > 0.8
        df = pd.DataFrame({'is_stable': [True, True, True, True, False]}) # 0.8
        # Implementation: df['is_stable'].mean() > 0.8
        # 0.8 > 0.8 is False. So this should be False.
        # Let's test a case that is > 0.8
        df = pd.DataFrame({'is_stable': [True, True, True, True, True, False]}) # 5/6 = 0.833
        assert validate_density_stability(df) is True

    def test_empty_df(self):
        df = pd.DataFrame()
        assert validate_density_stability(df) is False

    def test_missing_column(self):
        df = pd.DataFrame({'other_col': [True, True]})
        assert validate_density_stability(df) is False


class TestValidateArtifactStability:
    def test_all_stable(self):
        df = pd.DataFrame({'is_stable': [True, True, True]})
        assert validate_artifact_stability(df) is True

    def test_all_unstable(self):
        df = pd.DataFrame({'is_stable': [False, False, False]})
        assert validate_artifact_stability(df) is False

    def test_empty_df(self):
        df = pd.DataFrame()
        assert validate_artifact_stability(df) is False

    def test_missing_column(self):
        df = pd.DataFrame({'other_col': [True, True]})
        assert validate_artifact_stability(df) is False