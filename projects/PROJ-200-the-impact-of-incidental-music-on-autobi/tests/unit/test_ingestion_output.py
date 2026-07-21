import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_project_root
from state_manager import load_state

class TestT018IngestedCohort:
    """Tests for T018: Generate data/processed/ingested_cohort.parquet"""

    @pytest.fixture
    def project_root(self):
        return get_project_root()

    @pytest.fixture
    def expected_file_path(self, project_root):
        return project_root / "data" / "processed" / "ingested_cohort.parquet"

    @pytest.fixture
    def state_file_path(self, project_root):
        return project_root / "state.yaml"

    def test_output_file_exists(self, expected_file_path):
        """Verify that the output parquet file exists."""
        assert expected_file_path.exists(), f"File {expected_file_path} does not exist"

    def test_output_file_is_valid_parquet(self, expected_file_path):
        """Verify that the output file is a valid Parquet file."""
        try:
            df = pd.read_parquet(expected_file_path)
            assert df is not None
        except Exception as e:
            pytest.fail(f"Failed to read parquet file: {e}")

    def test_required_columns_present(self, expected_file_path):
        """Verify that the required columns are present in the output."""
        df = pd.read_parquet(expected_file_path)
        required_columns = [
            'track_id', 
            'adolescent_exposure_score', 
            'residualized_exposure_score',
            'birth_year'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        assert not missing_columns, f"Missing columns: {missing_columns}"

    def test_exposure_score_range(self, expected_file_path):
        """Verify that adolescent_exposure_score is between 0.0 and 1.0."""
        df = pd.read_parquet(expected_file_path)
        assert df['adolescent_exposure_score'].min() >= 0.0
        assert df['adolescent_exposure_score'].max() <= 1.0

    def test_state_yaml_updated(self, state_file_path, expected_file_path):
        """Verify that state.yaml has been updated with the file checksum."""
        assert state_file_path.exists(), "state.yaml does not exist"
        
        with open(state_file_path, 'r') as f:
            state = yaml.safe_load(f)
        
        # Check if the file is registered in state
        file_name = expected_file_path.name
        found = False
        for entry in state.get('files', []):
            if entry.get('file') == str(expected_file_path):
                found = True
                # Verify checksum is present and non-empty
                assert entry.get('checksum'), "Checksum is missing or empty"
                break
        
        assert found, f"File {file_name} not found in state.yaml"

    def test_no_birth_year_missing(self, expected_file_path):
        """Verify that records without birth_year are excluded."""
        df = pd.read_parquet(expected_file_path)
        # Check for NaN or None in birth_year column
        assert df['birth_year'].isna().sum() == 0, "Found records with missing birth_year"