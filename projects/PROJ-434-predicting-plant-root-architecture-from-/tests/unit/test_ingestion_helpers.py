import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.ingestion.data_loader import DataFetchError
from code.ingestion.logging_utils import setup_logging, get_logger, log_excluded_record
from code.utils.exceptions import DataQualityError

class TestDataFetchError:
    def test_data_fetch_error_instantiation(self):
        error = DataFetchError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_data_fetch_error_with_cause(self):
        original_error = ValueError("Original error")
        error = DataFetchError("Failed to fetch", original_error)
        assert str(error) == "Failed to fetch"
        assert error.__cause__ == original_error

class TestLoggingUtils:
    def setup_method(self):
        self.logger = get_logger("test_logger")

    def test_setup_logging_creates_logger(self):
        logger = setup_logging("test.log", level="DEBUG")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_get_logger_returns_existing(self):
        logger1 = get_logger("shared_logger")
        logger2 = get_logger("shared_logger")
        assert logger1 is logger2

    def test_log_excluded_record(self):
        record_id = 123
        reason_code = "missing_soil_data"
        log_excluded_record(record_id, reason_code, self.logger)
        # Just verify it doesn't crash

    def test_log_excluded_record_with_message(self):
        record_id = 456
        reason_code = "invalid_value"
        message = "Additional context"
        log_excluded_record(record_id, reason_code, self.logger, message)

class TestValidationLogic:
    def test_pandas_dataframe_operations(self):
        """Test basic dataframe operations that mimic ingestion logic."""
        df = pd.DataFrame({
            'species': ['A', 'B', 'C', 'A', 'B'],
            'depth': [10.0, 20.0, 30.0, 15.0, 25.0],
            'pH': [6.5, 7.0, 5.5, 8.0, 6.0]
        })

        # Filter physically plausible
        mask = (df['depth'] > 0) & (df['pH'] >= 3.0) & (df['pH'] <= 9.0)
        filtered = df[mask]

        assert len(filtered) == len(df)  # All rows should pass this filter

    def test_species_counting(self):
        df = pd.DataFrame({
            'species': ['A', 'A', 'A', 'B', 'B', 'C'],
            'valid': [1, 1, 1, 1, 1, 1]
        })

        counts = df.groupby('species')['valid'].count()
        
        assert counts['A'] == 3
        assert counts['B'] == 2
        assert counts['C'] == 1

    def test_filter_species_threshold(self):
        df = pd.DataFrame({
            'species': ['A'] * 15 + ['B'] * 5 + ['C'] * 8,
            'depth': np.random.rand(28) * 100
        })

        # Count per species
        counts = df.groupby('species').size()
        
        # Filter for >= 10 observations
        valid_species = counts[counts >= 10].index.tolist()
        
        assert 'A' in valid_species
        assert 'B' not in valid_species
        assert 'C' not in valid_species

    def test_match_proportion_calculation(self):
        total_rows = 100
        valid_rows = 95
        
        proportion = valid_rows / total_rows
        
        assert proportion == 0.95
        assert proportion >= 0.90  # Should pass threshold

    def test_match_proportion_below_threshold(self):
        total_rows = 100
        valid_rows = 80
        
        proportion = valid_rows / total_rows
        
        assert proportion == 0.80
        assert proportion < 0.90  # Should fail threshold

class TestPathHandling:
    def test_path_creation(self):
        test_path = Path("data/test_output")
        test_path.mkdir(parents=True, exist_ok=True)
        assert test_path.exists()
        assert test_path.is_dir()

    def test_path_joining(self):
        base = Path("data")
        sub = Path("processed")
        file = "test.csv"
        
        full_path = base / sub / file
        
        assert str(full_path) == "data/processed/test.csv"

class TestDataQualityScenarios:
    def test_missing_data_handling(self):
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10.0, np.nan, 30.0, np.nan, 50.0]
        })
        
        # Count non-null
        valid_count = df['value'].notna().sum()
        
        assert valid_count == 3
        assert len(df) == 5

    def test_invalid_value_filtering(self):
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'pH': [6.0, 2.0, 7.0, 10.0, 5.5]  # 2.0 and 10.0 are invalid
        })
        
        mask = (df['pH'] >= 3.0) & (df['pH'] <= 9.0)
        filtered = df[mask]
        
        assert len(filtered) == 3
        assert 2.0 not in filtered['pH'].values
        assert 10.0 not in filtered['pH'].values
