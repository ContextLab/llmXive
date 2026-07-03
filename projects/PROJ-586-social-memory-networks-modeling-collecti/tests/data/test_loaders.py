"""Tests for dataset loaders and synthetic fallback."""
import pytest
from pathlib import Path
from data.loaders import (
    register_dataset,
    get_dataset,
    enable_synthetic_fallback,
    disable_synthetic_fallback,
    verify_datasets,
    load_experiment_results,
    save_experiment_results,
    _generate_synthetic_fallback
)
import csv


class TestDatasetRegistry:
    """Tests for the dataset registration system."""

    def test_register_dataset(self):
        """Test that datasets can be registered."""
        def mock_loader():
            return [{"id": 1, "value": "test"}]
        
        register_dataset("test_dataset", mock_loader)
        result = get_dataset("test_dataset")
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_duplicate_registration_raises(self):
        """Test that registering a duplicate dataset raises an error."""
        def mock_loader():
            return []
        
        register_dataset("unique_dataset", mock_loader)
        with pytest.raises(ValueError):
            register_dataset("unique_dataset", mock_loader)

    def test_get_unregistered_dataset_without_fallback(self):
        """Test that getting an unregistered dataset raises ImportError."""
        disable_synthetic_fallback()
        with pytest.raises(ImportError):
            get_dataset("nonexistent_dataset")

    def test_get_unregistered_dataset_with_fallback(self):
        """Test that synthetic fallback generates data when enabled."""
        enable_synthetic_fallback()
        try:
            result = get_dataset("synthetic_test")
            assert isinstance(result, list)
            assert len(result) > 0
            assert all("is_synthetic" in record for record in result)
            assert all(record["is_synthetic"] for record in result)
        finally:
            disable_synthetic_fallback()


class TestSyntheticFallback:
    """Tests for the synthetic fallback mechanism."""

    def test_generate_synthetic_fallback_structure(self):
        """Test that generated synthetic data has the expected structure."""
        records = _generate_synthetic_fallback("test")
        assert len(records) == 10
        
        required_fields = [
            "game_id", "agent_count", "context_condition",
            "specialization_index", "retrieval_efficiency", "is_synthetic"
        ]
        
        for record in records:
            for field in required_fields:
                assert field in record
            assert record["is_synthetic"] is True

    def test_synthetic_fallback_values(self):
        """Test that synthetic values are within expected ranges."""
        records = _generate_synthetic_fallback("test")
        
        for record in records:
            assert 3 <= record["agent_count"] <= 7
            assert record["context_condition"] in ["full", "limited"]
            assert 0.1 <= record["specialization_index"] <= 0.9
            assert 0.2 <= record["retrieval_efficiency"] <= 0.95


class TestExperimentResultsIO:
    """Tests for loading and saving experiment results."""

    def test_save_and_load_experiment_results(self, tmp_path):
        """Test that results can be saved and loaded correctly."""
        test_records = [
            {"game_id": "1", "value": 10, "is_synthetic": False},
            {"game_id": "2", "value": 20, "is_synthetic": False}
        ]
        
        output_path = tmp_path / "results.csv"
        save_experiment_results(output_path, test_records)
        
        loaded = load_experiment_results(output_path)
        assert len(loaded) == 2
        assert loaded[0]["game_id"] == "1"
        assert loaded[1]["value"] == "20"  # CSV reads as strings

    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_experiment_results(tmp_path / "nonexistent.csv")

    def test_save_empty_records_raises(self, tmp_path):
        """Test that saving empty records raises an error."""
        with pytest.raises(ValueError):
            save_experiment_results(tmp_path / "empty.csv", [])

def test_verify_datasets_with_fallback_enabled():
    """Test that verify_datasets passes when fallback is enabled."""
    enable_synthetic_fallback()
    try:
        # Should not raise even if no datasets are registered
        verify_datasets(["nonexistent"])
    finally:
        disable_synthetic_fallback()

def test_verify_datasets_without_fallback():
    """Test that verify_datasets fails when fallback is disabled."""
    disable_synthetic_fallback()
    with pytest.raises(ImportError):
        verify_datasets(["nonexistent"])
