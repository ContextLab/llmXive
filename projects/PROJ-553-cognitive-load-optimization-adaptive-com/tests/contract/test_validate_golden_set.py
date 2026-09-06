import pytest
import pandas as pd
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_golden_set import validate_golden_set

class TestGoldenSetValidation:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up a temporary data directory structure for each test."""
        self.data_dir = tmp_path / "data" / "processed"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        yield
        os.chdir(self.original_cwd)

    def _create_golden_set(self, rows, score_values=None):
        """Helper to create a golden set CSV file."""
        df = pd.DataFrame({
            'interaction_id': [f'interaction_{i}' for i in range(rows)],
            'expert_load_score': score_values if score_values else [50.0] * rows
        })
        path = self.data_dir / "golden_set.csv"
        df.to_csv(path, index=False)
        return path

    def test_missing_file_raises_error(self, setup):
        """Test that a missing file raises SystemExit with the correct message."""
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_insufficient_rows_raises_error(self, setup):
        """Test that a file with < 50 rows raises SystemExit."""
        self._create_golden_set(rows=49)
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_missing_column_raises_error(self, setup):
        """Test that a file missing 'expert_load_score' raises SystemExit."""
        df = pd.DataFrame({'interaction_id': [f'id_{i}' for i in range(50)]})
        path = self.data_dir / "golden_set.csv"
        df.to_csv(path, index=False)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_invalid_score_range_raises_error(self, setup):
        """Test that scores outside 0-100 raise SystemExit."""
        # Create 50 rows, one with score 101
        scores = [50.0] * 49 + [101.0]
        self._create_golden_set(rows=50, score_values=scores)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_negative_score_raises_error(self, setup):
        """Test that negative scores raise SystemExit."""
        scores = [50.0] * 49 + [-1.0]
        self._create_golden_set(rows=50, score_values=scores)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_nan_score_raises_error(self, setup):
        """Test that NaN scores raise SystemExit."""
        scores = [50.0] * 49 + [float('nan')]
        self._create_golden_set(rows=50, score_values=scores)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_golden_set()
        assert "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." in str(excinfo.value)

    def test_valid_golden_set_passes(self, setup):
        """Test that a valid golden set (50+ rows, valid scores) returns True."""
        self._create_golden_set(rows=50, score_values=[50.0] * 50)
        
        result = validate_golden_set()
        assert result is True

    def test_valid_golden_set_more_than_50_rows(self, setup):
        """Test that a valid golden set with > 50 rows passes."""
        self._create_golden_set(rows=100, score_values=[i for i in range(100)])
        
        result = validate_golden_set()
        assert result is True