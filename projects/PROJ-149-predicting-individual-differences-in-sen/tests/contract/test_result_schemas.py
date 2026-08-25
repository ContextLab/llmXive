import os
import sys
import json
import csv
import pytest
from pathlib import Path

# Add project root to path for imports if needed, though we use direct file access here
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
DATA_INTERIM = PROJECT_ROOT / 'data' / 'interim'

class TestModelResultsSchema:
    """Validates schema of data/processed/model_results.json"""

    REQUIRED_KEYS = {
        'adjusted_r2', 'optimal_lambda', 'rmse', 'test_r2', 'test_rmse',
        'post_hoc_power_analysis'
    }
    POWER_ANALYSIS_KEYS = {'required_n', 'power', 'effect_size'}

    @pytest.fixture
    def file_path(self):
        return DATA_PROCESSED / 'model_results.json'

    def test_file_exists(self, file_path):
        assert file_path.exists(), f"File not found: {file_path}"

    def test_valid_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, dict), "Root must be a dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")

    def test_required_top_level_keys(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        missing = self.REQUIRED_KEYS - set(data.keys())
        assert not missing, f"Missing required keys: {missing}"

    def test_numeric_types(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        numeric_keys = {'adjusted_r2', 'optimal_lambda', 'rmse', 'test_r2', 'test_rmse'}
        for key in numeric_keys:
            if key in data:
                assert isinstance(data[key], (int, float)), f"{key} must be numeric"

    def test_power_analysis_schema(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert 'post_hoc_power_analysis' in data, "Missing post_hoc_power_analysis key"
        power_data = data['post_hoc_power_analysis']
        assert isinstance(power_data, dict), "post_hoc_power_analysis must be a dict"
        
        missing = self.POWER_ANALYSIS_KEYS - set(power_data.keys())
        assert not missing, f"Missing power analysis keys: {missing}"


class TestCorrelationsCorrectedSchema:
    """Validates schema of data/processed/correlations_corrected.csv"""

    REQUIRED_COLUMNS = {'band', 'r_value', 'p_value', 'n', 'significant'}
    BANDS = {'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma'}

    @pytest.fixture
    def file_path(self):
        return DATA_PROCESSED / 'correlations_corrected.csv'

    def test_file_exists(self, file_path):
        assert file_path.exists(), f"File not found: {file_path}"

    def test_required_columns(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames)
            
        missing = self.REQUIRED_COLUMNS - headers
        assert not missing, f"Missing required columns: {missing}"

    def test_band_values(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 6, f"Expected 6 rows (one per band), got {len(rows)}"
        
        found_bands = {row['band'] for row in rows}
        assert found_bands == self.BANDS, f"Band mismatch. Expected: {self.BANDS}, Found: {found_bands}"

    def test_numeric_columns(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # r_value
                val = float(row['r_value'])
                assert -1.0 <= val <= 1.0, f"r_value out of range: {val}"
                
                # p_value
                val = float(row['p_value'])
                assert 0.0 <= val <= 1.0, f"p_value out of range: {val}"
                
                # n
                val = int(row['n'])
                assert val > 0, f"n must be positive: {val}"

                # significant (boolean)
                sig = row['significant'].lower()
                assert sig in ('true', 'false'), f"significant must be boolean string: {sig}"


class TestNonLinearComparisonSchema:
    """Validates schema of data/processed/non_linear_comparison.json"""

    REQUIRED_KEYS = {'linear_adjusted_r2', 'non_linear_adjusted_r2', 'f_statistic', 'p_value', 'significant_at_0p05', 'interpretation'}

    @pytest.fixture
    def file_path(self):
        return DATA_PROCESSED / 'non_linear_comparison.json'

    def test_file_exists(self, file_path):
        assert file_path.exists(), f"File not found: {file_path}"

    def test_valid_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, dict), "Root must be a dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")

    def test_required_keys(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        missing = self.REQUIRED_KEYS - set(data.keys())
        assert not missing, f"Missing required keys: {missing}"

    def test_boolean_and_string_types(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data['significant_at_0p05'], bool), "significant_at_0p05 must be boolean"
        assert isinstance(data['interpretation'], str), "interpretation must be string"
        assert len(data['interpretation']) > 0, "interpretation cannot be empty"

    def test_numeric_types(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        numeric_keys = {'linear_adjusted_r2', 'non_linear_adjusted_r2', 'f_statistic', 'p_value'}
        for key in numeric_keys:
            assert isinstance(data[key], (int, float)), f"{key} must be numeric"


class TestPermutationResultsSchema:
    """Validates schema of data/processed/permutation_results.json"""

    REQUIRED_KEYS = {'observed_r2', 'p_value', 'null_distribution_path'}

    @pytest.fixture
    def file_path(self):
        return DATA_PROCESSED / 'permutation_results.json'

    def test_file_exists(self, file_path):
        assert file_path.exists(), f"File not found: {file_path}"

    def test_valid_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, dict), "Root must be a dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")

    def test_required_keys(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        missing = self.REQUIRED_KEYS - set(data.keys())
        assert not missing, f"Missing required keys: {missing}"

    def test_numeric_types(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data['observed_r2'], (int, float)), "observed_r2 must be numeric"
        assert isinstance(data['p_value'], (int, float)), "p_value must be numeric"
        
        # Validate p-value range
        assert 0.0 <= data['p_value'] <= 1.0, f"p_value out of range: {data['p_value']}"

    def test_null_distribution_file_exists(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        null_path = Path(data['null_distribution_path'])
        if not null_path.is_absolute():
            null_path = PROJECT_ROOT / null_path
        
        assert null_path.exists(), f"Null distribution file not found: {null_path}"
