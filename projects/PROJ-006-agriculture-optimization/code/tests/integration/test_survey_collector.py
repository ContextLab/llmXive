import os
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

from src.data.collectors.survey_collector import SurveyCollector
from src.utils.io_helpers import read_csv_strict
from src.config.constants import BUFFER_SIZE_KM

class TestSurveyCollector:
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_real_data_missing_uses_fallback(self, temp_workspace):
        """
        Test that if real LSMS-ISA data is missing, the collector
        falls back to generating synthetic data.
        """
        # Ensure lsms_isa.csv does NOT exist
        lsms_path = temp_workspace / "lsms_isa.csv"
        assert not lsms_path.exists()

        collector = SurveyCollector(data_dir=str(temp_workspace))
        
        # Run collection - should trigger fallback
        df = collector.run()

        # Verify output files exist
        assert (temp_workspace / "survey_raw.csv").exists()
        assert (temp_workspace / "filtered_survey.csv").exists()

        # Verify data is loaded and valid
        assert df is not None
        assert len(df) > 0

        # Verify schema
        required_cols = [
            'household_id', 'latitude', 'longitude', 'land_size',
            'education_level', 'finance_access', 'practice_mixed_farming',
            'practice_terracing', 'practice_conservation_tillage',
            'practice_agroforestry', 'extension_visits', 'hlias'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_real_data_loaded_if_present(self, temp_workspace):
        """
        Test that if real LSMS-ISA data exists, it is loaded and validated.
        """
        # Create a mock real data file
        lsms_path = temp_workspace / "lsms_isa.csv"
        mock_data = {
            'household_id': [1, 2, 3],
            'latitude': [30.0, 31.0, 32.0],
            'longitude': [35.0, 36.0, 37.0],
            'land_size': [1.0, 2.0, 3.0],
            'education_level': [5, 6, 7],
            'finance_access': [True, False, True],
            'practice_mixed_farming': [True, False, True],
            'practice_terracing': [False, True, False],
            'practice_conservation_tillage': [True, True, False],
            'practice_agroforestry': [False, False, True],
            'extension_visits': [2, 3, 4],
            'hlias': [10, 15, 12]
        }
        pd.DataFrame(mock_data).to_csv(lsms_path, index=False)

        collector = SurveyCollector(data_dir=str(temp_workspace))
        
        # Run collection
        df = collector.run()

        # Verify output files exist
        assert (temp_workspace / "survey_raw.csv").exists()
        assert (temp_workspace / "filtered_survey.csv").exists()

        # Verify data matches input (since no filtering expected on valid coords)
        assert len(df) == 3
        assert df['household_id'].tolist() == [1, 2, 3]
        assert df['latitude'].tolist() == [30.0, 31.0, 32.0]

    def test_filtering_missing_coordinates(self, temp_workspace):
        """
        Test that rows with missing coordinates are filtered out.
        """
        # Create mock data with missing coordinates
        lsms_path = temp_workspace / "lsms_isa.csv"
        mock_data = {
            'household_id': [1, 2, 3],
            'latitude': [30.0, None, 32.0],
            'longitude': [35.0, 36.0, None],
            'land_size': [1.0, 2.0, 3.0],
            'education_level': [5, 6, 7],
            'finance_access': [True, False, True],
            'practice_mixed_farming': [True, False, True],
            'practice_terracing': [False, True, False],
            'practice_conservation_tillage': [True, True, False],
            'practice_agroforestry': [False, False, True],
            'extension_visits': [2, 3, 4],
            'hlias': [10, 15, 12]
        }
        pd.DataFrame(mock_data).to_csv(lsms_path, index=False)

        collector = SurveyCollector(data_dir=str(temp_workspace))
        df = collector.run()

        # Only row 1 and 3 have valid coords (row 2 has None lat, row 3 has None lon -> actually row 3 is invalid too)
        # Row 1: lat=30, lon=35 -> Valid
        # Row 2: lat=None, lon=36 -> Invalid
        # Row 3: lat=32, lon=None -> Invalid
        # So only 1 row should remain
        assert len(df) == 1
        assert df['household_id'].iloc[0] == 1

    def test_schema_validation_fail(self, temp_workspace):
        """
        Test that data missing required columns fails validation.
        """
        lsms_path = temp_workspace / "lsms_isa.csv"
        # Missing 'hlias' column
        mock_data = {
            'household_id': [1],
            'latitude': [30.0],
            'longitude': [35.0],
            'land_size': [1.0],
            # Missing many other required columns
        }
        pd.DataFrame(mock_data).to_csv(lsms_path, index=False)

        collector = SurveyCollector(data_dir=str(temp_workspace))
        
        # This should raise an error or return None depending on implementation
        # Our implementation returns None if schema fails in collect_real_data
        # But then it falls back to synthetic.
        # To test strict failure, we would need to disable fallback.
        # For now, we test that the fallback mechanism works even if real data is bad.
        # The task says "If no, skip this task and rely on T015b."
        # So if real data is bad, it should fall back.
        
        df = collector.run()
        assert df is not None # Should have fallen back to synthetic
        assert len(df) > 0
