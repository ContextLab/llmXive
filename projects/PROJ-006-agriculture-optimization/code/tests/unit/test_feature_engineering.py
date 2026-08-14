"""
Unit tests for T018: Feature Engineering (CSA_Index and Stability_Score).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.data.processing.feature_engineering import FeatureEngineer, MIN_SAMPLE_SIZE_FOR_HOUSEHOLD
from src.utils.io_helpers import FatalError, IntegrityError

class TestGrowingSeasonMapping:
    """Test T018a: Temporal window mapping logic."""

    def test_malawi_season(self):
        """Malawi should return March-May."""
        engineer = FeatureEngineer(Path("dummy"), Path("dummy"))
        months = engineer._get_growing_season_months("Malawi", 2020)
        assert months == [3, 4, 5]

    def test_tanzania_season(self):
        """Tanzania should return March-May and Nov-Dec."""
        engineer = FeatureEngineer(Path("dummy"), Path("dummy"))
        months = engineer._get_growing_season_months("Tanzania", 2020)
        assert months == [3, 4, 5, 11, 12]

    def test_unknown_country_raises(self):
        """Unknown country should raise IntegrityError."""
        engineer = FeatureEngineer(Path("dummy"), Path("dummy"))
        with pytest.raises(IntegrityError):
            engineer._get_growing_season_months("UnknownCountry", 2020)

class TestStabilityScoreCalculation:
    """Test T018b & T018c: Stability Score (1/CV) logic."""

    def test_stability_calculation(self):
        """Verify 1/CV calculation."""
        # Mean = 0.5, Std = 0.1 -> CV = 0.2 -> Stability = 5.0
        data = pd.Series([0.4, 0.5, 0.6]) # Approx mean 0.5, std 0.1
        # Exact: mean=0.5, std=0.1 (sample std for [0.4, 0.5, 0.6] is 0.1)
        engineer = FeatureEngineer(Path("dummy"), Path("dummy"))
        score = engineer._aggregate_ndvi_to_stability(data)
        expected_cv = 0.1 / 0.5
        expected_stability = 1.0 / expected_cv
        assert abs(score - expected_stability) < 0.01

    def test_low_variance_high_stability(self):
        """Low variance should result in high stability score."""
        data = pd.Series([0.5, 0.5, 0.5])
        score = FeatureEngineer(Path("dummy"), Path("dummy"))._aggregate_ndvi_to_stability(data)
        assert score == 100.0 # Cap for near-zero CV

    def test_single_value_returns_zero(self):
        """Single value cannot calculate variance, returns 0."""
        data = pd.Series([0.5])
        score = FeatureEngineer(Path("dummy"), Path("dummy"))._aggregate_ndvi_to_stability(data)
        assert score == 0.0

class TestCSAIndexConstruction:
    """Test T018c: CSA Index construction."""

    def test_csa_index_sum(self):
        """CSA Index should sum binary practices and extension frequency."""
        # Mock a row with practices
        row_data = {
            'practice_agroforestry': 1,
            'practice_terracing': 1,
            'practice_irrigation': 0,
            'practice_conservation_tillage': 0,
            'practice_diversification': 0,
            'extension_frequency': 2.0
        }
        # Create a dummy dataframe to satisfy the self.df check in the method
        # We will patch the method to accept a Series directly or mock self.df
        # For unit test simplicity, we test the logic directly if possible, 
        # or construct a minimal DF.
        
        # The method _calculate_csa_index expects a row from a dataframe.
        # We'll create a dummy DF with the necessary columns.
        df = pd.DataFrame([row_data])
        engineer = FeatureEngineer(Path("dummy"), Path("dummy"))
        engineer.df = df # Inject the dummy DF
        
        score = engineer._calculate_csa_index(df.iloc[0])
        # Expected: 1 (agro) + 1 (terracing) + 2 (ext) = 4.0
        assert score == 4.0

class TestIntegration:
    """Integration test for the full feature engineering pipeline."""

    def test_full_pipeline(self):
        """Test loading, processing, and saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create mock input data
            # Simulate joined data with ndvi_values as JSON strings
            mock_data = [
                {
                    'household_id': 'H1',
                    'country': 'Malawi',
                    'survey_year': 2020,
                    'ndvi_values': '[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]', # 12 months
                    'month': 1, # Dummy month column to trigger slicing
                    'practice_agroforestry': 1,
                    'extension_frequency': 1.0
                },
                {
                    'household_id': 'H2',
                    'country': 'Tanzania',
                    'survey_year': 2020,
                    'ndvi_values': '[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]',
                    'month': 1,
                    'practice_agroforestry': 0,
                    'extension_frequency': 0.0
                }
            ]
            df_mock = pd.DataFrame(mock_data)
            df_mock.to_csv(input_path, index=False)
            
            # Run engineer
            engineer = FeatureEngineer(input_path, output_path)
            engineer.load_data()
            result = engineer.process_features()
            engineer.save_results(result)
            
            # Verify output exists
            assert output_path.exists()
            
            # Verify columns
            assert 'CSA_Index' in result.columns
            assert 'Stability_Score' in result.columns
            
            # Verify values are not null
            assert not result['CSA_Index'].isnull().any()
            assert not result['Stability_Score'].isnull().any()

    def test_village_aggregation_fallback(self):
        """Test T021: Aggregation when N < 300."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_small.csv"
            output_path = Path(tmpdir) / "output_village.csv"
            
            # Create small dataset (< 300 rows)
            data = []
            for i in range(50):
                data.append({
                    'household_id': f'H{i}',
                    'village_id': f'V{i%5}', # 5 villages
                    'country': 'Malawi',
                    'survey_year': 2020,
                    'ndvi_values': '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]',
                    'month': 1,
                    'practice_agroforestry': 1,
                    'extension_frequency': 1.0
                })
            df_mock = pd.DataFrame(data)
            df_mock.to_csv(input_path, index=False)
            
            engineer = FeatureEngineer(input_path, output_path)
            engineer.load_data()
            result = engineer.process_features()
            engineer.save_results(result)
            
            # Verify output is aggregated to village level (5 rows)
            assert len(result) == 5
            assert 'village_id' in result.columns
            assert 'household_count' in result.columns # Added in aggregation step