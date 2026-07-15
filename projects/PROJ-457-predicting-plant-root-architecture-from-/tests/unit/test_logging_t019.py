import pytest
import logging
import sys
import os
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_ingestion import filter_data, main as ingestion_main
from preprocessing import apply_log_transformation, apply_zscore_normalization, apply_knn_imputation, main as preprocessing_main

class TestLoggingT019:
    """
    Tests for T019: Logging for exclusion counts and transformation steps.
    Verifies that the correct log messages are generated during pipeline execution.
    """

    def setup_method(self):
        # Setup a test logger
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.INFO)
        
        # Create a handler that captures logs
        self.log_capture = []
        class LogCapture(logging.Handler):
            def emit(self, record):
                self.log_capture.append(record.getMessage())
        
        self.handler = LogCapture()
        self.handler.log_capture = self.log_capture
        self.logger.addHandler(self.handler)

    def test_filter_data_logs_exclusion_counts(self):
        """Test that filter_data logs exclusion counts for species < 20 and experimental data."""
        # Create mock data
        # 10 rows of Species A (will be excluded)
        # 50 rows of Species B (will be kept)
        # 5 rows of Species B with experimental type (will be excluded)
        data = []
        for i in range(10):
            data.append({"species": "Species_A", "root_length": 1.0, "data_source_type": "field"})
        for i in range(50):
            data.append({"species": "Species_B", "root_length": 1.0, "data_source_type": "field"})
        for i in range(5):
            data.append({"species": "Species_B", "root_length": 1.0, "data_source_type": "experimental"})

        # Run filter
        filtered, stats = filter_data(data, min_species_count=20)

        # Verify logs
        logs = self.handler.log_capture
        logs_str = " ".join(logs)
        
        assert "Exclusion Filter (Species Count < 20)" in logs_str
        assert "Total rows excluded" in logs_str
        assert "Exclusion Filter (Data Source Type)" in logs_str
        
        # Verify stats
        assert stats["species_low_count"] == 10
        assert stats["experimental_controlled"] == 5

    def test_apply_log_transformation_logs_steps(self):
        """Test that log transformation logs the columns and count."""
        data = [{"root_length": 10.0, "branching_density": 2.0}] * 10
        
        _, count = apply_log_transformation(data, ["root_length", "branching_density"])
        
        logs = self.handler.log_capture
        logs_str = " ".join(logs)
        
        assert "Applying log transformation to columns" in logs_str
        assert "Log transformation complete" in logs_str

    def test_apply_zscore_normalization_logs_steps(self):
        """Test that z-score normalization logs statistics and count."""
        data = [{"phosphorus": 10.0, "nitrogen": 2.0}] * 10
        
        _, stats = apply_zscore_normalization(data, ["phosphorus", "nitrogen"])
        
        logs = self.handler.log_capture
        logs_str = " ".join(logs)
        
        assert "Applying z-score normalization to columns" in logs_str
        assert "Calculated global statistics" in logs_str
        assert "Z-score normalization complete" in logs_str

    def test_apply_knn_imputation_logs_steps(self):
        """Test that KNN imputation logs the process."""
        data = [{"phosphorus": None, "nitrogen": 2.0}] * 10
        
        _, count = apply_knn_imputation(data, k=5, columns=["phosphorus"])
        
        logs = self.handler.log_capture
        logs_str = " ".join(logs)
        
        assert "Applying KNN imputation" in logs_str
        assert "KNN imputation complete" in logs_str
