"""
Unit tests for the logging statistics module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import get_logger
from data.logging_stats import (
    ExcludedMolecule,
    DatasetStatistics,
    log_excluded_molecule,
    log_dataset_statistics,
    log_split_statistics
)


class TestExcludedMolecule:
    """Tests for ExcludedMolecule dataclass."""

    def test_excluded_molecule_creation(self):
        """Test creation of ExcludedMolecule instance."""
        excluded = ExcludedMolecule(
            smiles="CCO",
            reason="Invalid SMILES",
            step="preprocess",
            error_message="Failed to parse"
        )
        
        assert excluded.smiles == "CCO"
        assert excluded.reason == "Invalid SMILES"
        assert excluded.step == "preprocess"
        assert excluded.error_message == "Failed to parse"

    def test_excluded_molecule_without_error(self):
        """Test creation without error message."""
        excluded = ExcludedMolecule(
            smiles="CCO",
            reason="Invalid SMILES",
            step="preprocess"
        )
        
        assert excluded.error_message is None


class TestLogExcludedMolecule:
    """Tests for log_excluded_molecule function."""

    def test_log_excluded_molecule(self, caplog):
        """Test that excluded molecules are logged correctly."""
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.WARNING):
            log_excluded_molecule(
                logger=logger,
                smiles="CCO",
                reason="Invalid SMILES",
                step="preprocess",
                error_message="Failed to parse"
            )
        
        assert "[EXCLUDED]" in caplog.text
        assert "Step: preprocess" in caplog.text
        assert "Reason: Invalid SMILES" in caplog.text
        assert "CCO" in caplog.text


class TestDatasetStatistics:
    """Tests for dataset statistics calculation."""

    def test_log_dataset_statistics_basic(self, tmp_path):
        """Test basic dataset statistics calculation."""
        # Create a temporary directory for logs
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock the get_results_dir function temporarily
            import data.logging_stats as stats_module
            original_get_results_dir = stats_module.get_results_dir
            stats_module.get_results_dir = lambda: Path(tmp_dir)
            
            try:
                logger = get_logger(__name__)
                
                # Create a simple DataFrame
                df = pd.DataFrame({
                    "smiles": ["CCO", "CCCO", "CCCCO"],
                    "sasa": [20.5, 30.2, 40.1],
                    "mw": [46.07, 60.10, 74.12],
                    "logp": [-0.3, 0.5, 1.3],
                    "num_atoms": [5, 7, 9]
                })
                
                stats = log_dataset_statistics(logger, df, excluded_count=2)
                
                assert stats.total_molecules == 5
                assert stats.included_count == 3
                assert stats.excluded_count == 2
                assert abs(stats.exclusion_rate - 0.4) < 0.01
                
                # Check SASA statistics
                assert abs(stats.mean_sasa - 30.266) < 0.01
                assert stats.std_sasa is not None
                
                # Check that stats file was created
                stats_path = Path(tmp_dir) / "dataset_statistics.json"
                assert stats_path.exists()
                
                with open(stats_path, "r") as f:
                    saved_stats = json.load(f)
                
                assert saved_stats["total_molecules"] == 5
                assert saved_stats["included_count"] == 3
            finally:
                stats_module.get_results_dir = original_get_results_dir

    def test_empty_dataframe(self, tmp_path):
        """Test statistics calculation with empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import data.logging_stats as stats_module
            original_get_results_dir = stats_module.get_results_dir
            stats_module.get_results_dir = lambda: Path(tmp_dir)
            
            try:
                logger = get_logger(__name__)
                df = pd.DataFrame({"smiles": [], "sasa": []})
                
                stats = log_dataset_statistics(logger, df, excluded_count=0)
                
                assert stats.total_molecules == 0
                assert stats.included_count == 0
                assert stats.exclusion_rate == 0.0
            finally:
                stats_module.get_results_dir = original_get_results_dir


class TestSplitStatistics:
    """Tests for split statistics logging."""

    def test_log_split_statistics(self, caplog):
        """Test that split statistics are logged correctly."""
        logger = get_logger(__name__)
        
        train_df = pd.DataFrame({
            "sasa": [20.0, 30.0, 40.0],
            "mw": [50.0, 60.0, 70.0]
        })
        
        test_df = pd.DataFrame({
            "sasa": [25.0, 35.0],
            "mw": [55.0, 65.0]
        })
        
        with caplog.at_level(logging.INFO):
            log_split_statistics(logger, train_df, test_df)
        
        assert "SPLIT STATISTICS" in caplog.text
        assert "TRAIN SET:" in caplog.text
        assert "TEST SET:" in caplog.text
        assert "Count: 3" in caplog.text
        assert "Count: 2" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
