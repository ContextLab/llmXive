"""
Unit tests for feature_engineering.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import sys
from pathlib import Path as PathSys

# Ensure code directory is in path
code_root = PathSys(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.processing.feature_engineering import (
    calculate_stability_score,
    calculate_csa_index,
    derive_village_id,
    perform_village_aggregation,
    check_and_aggregate_if_needed,
    load_linkage_validation
)


class TestStabilityScoreCalculation:
    def test_stability_score_low_variance(self):
        """Test stability score with low variance (high stability)."""
        series = pd.Series([0.8, 0.81, 0.79, 0.8])
        score = calculate_stability_score(series)
        assert score > 10.0  # Low CV implies high score

    def test_stability_score_high_variance(self):
        """Test stability score with high variance (low stability)."""
        series = pd.Series([0.2, 0.8, 0.1, 0.9])
        score = calculate_stability_score(series)
        assert score < 10.0  # Higher CV implies lower score

    def test_stability_score_empty(self):
        """Test stability score with empty series."""
        series = pd.Series([], dtype=float)
        score = calculate_stability_score(series)
        assert score == 0.0

    def test_stability_score_zero_mean(self):
        """Test stability score when mean is zero."""
        series = pd.Series([0.0, 0.0, 0.0])
        score = calculate_stability_score(series)
        assert score == 0.0


class TestCSAIndexConstruction:
    def test_csa_index_all_practices(self):
        """Test CSA Index when all practices are adopted."""
        row = pd.Series({
            'practice_mixed_farming': True,
            'practice_terracing': True,
            'practice_conservation_tillage': True,
            'practice_agroforestry': True
        })
        score = calculate_csa_index(row)
        assert score == 4.0

    def test_csa_index_no_practices(self):
        """Test CSA Index when no practices are adopted."""
        row = pd.Series({
            'practice_mixed_farming': False,
            'practice_terracing': False,
            'practice_conservation_tillage': False,
            'practice_agroforestry': False
        })
        score = calculate_csa_index(row)
        assert score == 0.0

    def test_csa_index_partial(self):
        """Test CSA Index with partial adoption."""
        row = pd.Series({
            'practice_mixed_farming': True,
            'practice_terracing': False,
            'practice_conservation_tillage': True,
            'practice_agroforestry': False
        })
        score = calculate_csa_index(row)
        assert score == 2.0

    def test_csa_index_missing_columns(self):
        """Test CSA Index when columns are missing."""
        row = pd.Series({'other_col': True})
        score = calculate_csa_index(row)
        assert score == 0.0


class TestVillageIDDerivation:
    def test_village_id_derivation(self):
        """Test village ID derivation with known coordinates."""
        row = pd.Series({'latitude': 12.34, 'longitude': 45.67})
        # grid_resolution = 0.1
        # lat_grid = int(12.34 / 0.1) * 0.1 = 12.3
        # lon_grid = int(45.67 / 0.1) * 0.1 = 45.6
        village_id = derive_village_id(row, grid_resolution=0.1)
        assert village_id == "12.3_45.6"

    def test_village_id_nan(self):
        """Test village ID derivation with NaN coordinates."""
        row = pd.Series({'latitude': None, 'longitude': 45.67})
        village_id = derive_village_id(row, grid_resolution=0.1)
        assert village_id == "UNKNOWN"


class TestVillageAggregation:
    def test_aggregation_logic(self):
        """Test that aggregation correctly computes mean by village."""
        data = {
            'village_id': ['V1', 'V1', 'V2', 'V2'],
            'CSA_Index': [1.0, 3.0, 2.0, 4.0],
            'Stability_Score': [10.0, 20.0, 15.0, 25.0]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "agg.csv"
            result_df = perform_village_aggregation(df, output_path)

            assert len(result_df) == 2  # 2 unique villages
            assert result_df[result_df['village_id'] == 'V1']['CSA_Index'].iloc[0] == 2.0
            assert result_df[result_df['village_id'] == 'V1']['Stability_Score'].iloc[0] == 15.0

    def test_aggregation_excludes_nulls(self):
        """Test that aggregation excludes rows with null metrics."""
        data = {
            'village_id': ['V1', 'V1', 'V2'],
            'CSA_Index': [1.0, None, 2.0],
            'Stability_Score': [10.0, 20.0, None]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "agg.csv"
            result_df = perform_village_aggregation(df, output_path)

            # V1 has 1 valid row (index 0), V2 has 0 valid rows (index 2 has null Stability)
            # Wait, index 2 has null Stability, so it's excluded.
            # Index 0: V1, 1.0, 10.0 -> Valid
            # Index 1: V1, None, 20.0 -> Excluded (null CSA)
            # Index 2: V2, 2.0, None -> Excluded (null Stability)
            # Result should only have V1.
            assert len(result_df) == 1
            assert result_df['village_id'].iloc[0] == 'V1'


class TestIntegration:
    def test_check_and_aggregate_triggered(self):
        """Test the full check_and_aggregate_if_needed flow when triggered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            validation_file = tmpdir / "validation.json"

            # Create input data
            data = {
                'village_id': ['V1', 'V1', 'V2', 'V2'],
                'CSA_Index': [1.0, 3.0, 2.0, 4.0],
                'Stability_Score': [10.0, 20.0, 15.0, 25.0]
            }
            pd.DataFrame(data).to_csv(input_file, index=False)

            # Create validation file indicating trigger
            validation_data = {
                "triggered_aggregation": True,
                "linkage_percentage": 90.0,
                "total_valid_households": 100,
                "exclusion_reason": "low_linkage"
            }
            with open(validation_file, 'w') as f:
                json.dump(validation_data, f)

            result = check_and_aggregate_if_needed(input_file, output_file, validation_file)

            assert result is True
            assert output_file.exists()
            output_df = pd.read_csv(output_file)
            assert len(output_df) == 2

    def test_check_and_aggregate_not_triggered(self):
        """Test the flow when aggregation is NOT triggered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "input.csv"
            output_file = tmpdir / "output.csv"
            validation_file = tmpdir / "validation.json"

            # Create validation file indicating NO trigger
            validation_data = {
                "triggered_aggregation": False,
                "linkage_percentage": 99.0,
                "total_valid_households": 1000,
                "exclusion_reason": "none"
            }
            with open(validation_file, 'w') as f:
                json.dump(validation_data, f)

            result = check_and_aggregate_if_needed(input_file, output_file, validation_file)

            assert result is False
            assert not output_file.exists()

    def test_load_linkage_validation_missing(self):
        """Test loading a missing validation file."""
        path = Path("/nonexistent/path/validation.json")
        result = load_linkage_validation(path)
        assert result['triggered_aggregation'] is False
        assert result['exclusion_reason'] == "File not found"