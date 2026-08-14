"""
Unit tests for T031c: Trajectory Permutation Test.
"""
import json
import math
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from src.models.trajectory_permutation import (
    load_shift_candidates,
    calculate_shift_magnitude,
    calculate_shift_direction,
    run_permutation_test_for_species,
    run_trajectory_permutation_pipeline,
    N_SHUFFLES
)


class TestShiftCalculations:
    """Test helper functions for shift vector analysis."""

    def test_calculate_shift_magnitude(self):
        """Test magnitude calculation for a known vector."""
        vector = [3.0, 4.0]
        magnitude = calculate_shift_magnitude(vector)
        assert math.isclose(magnitude, 5.0, rel_tol=1e-5)

    def test_calculate_shift_direction(self):
        """Test direction calculation for a known vector."""
        # Vector (1, 0) -> 0 radians
        direction = calculate_shift_direction([1.0, 0.0])
        assert math.isclose(direction, 0.0, rel_tol=1e-5)

        # Vector (0, 1) -> pi/2 radians
        direction = calculate_shift_direction([0.0, 1.0])
        assert math.isclose(direction, math.pi / 2, rel_tol=1e-5)

    def test_calculate_shift_direction_empty(self):
        """Test direction calculation for empty vector."""
        direction = calculate_shift_direction([])
        assert direction == 0.0


class TestPermutationLogic:
    """Test permutation test logic."""

    @patch('src.models.trajectory_permutation.run_permutation_chunked')
    def test_run_permutation_test_for_species(self, mock_chunked):
        """Test that permutation test returns expected structure."""
        # Mock the chunked function to return a fixed set of null magnitudes
        mock_chunked.return_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        candidate = {
            "species": "TestBird",
            "year": 2020,
            "shift_vector": [0.1, 0.0]  # Magnitude 0.1
        }

        result = run_permutation_test_for_species(candidate, n_shuffles=5, seed=42)

        assert result["species"] == "TestBird"
        assert result["year"] == 2020
        assert "magnitude" in result
        assert "direction" in result
        assert "p_value" in result
        assert result["n_shuffles"] == 5
        assert 0.0 <= result["p_value"] <= 1.0


class TestPipelineIntegration:
    """Test the full pipeline integration."""

    def test_load_shift_candidates_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_shift_candidates()

    def test_run_trajectory_permutation_pipeline_empty(self):
        """Test pipeline with no shift candidates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock shift candidates file with empty list
            shift_path = Path(tmpdir) / "shift_candidates.json"
            shift_path.write_text(json.dumps([]))

            output_path = Path(tmpdir) / "output.json"

            with patch('src.models.trajectory_permutation.SHIFT_RESULTS_PATH', str(shift_path)):
                with patch('src.models.trajectory_permutation.OUTPUT_PATH', str(output_path)):
                    result = run_trajectory_permutation_pipeline()

            assert result["status"] == "success"
            assert result["n_species_processed"] == 0
            
            # Verify output file was created
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            assert len(data["records"]) == 0

    def test_run_trajectory_permutation_pipeline_with_data(self):
        """Test pipeline with valid shift candidates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock shift candidates
            shift_path = Path(tmpdir) / "shift_candidates.json"
            candidates = [
                {
                    "species": "SpeciesA",
                    "year": 2020,
                    "shift_vector": [1.0, 0.0]
                },
                {
                    "species": "SpeciesB",
                    "year": 2021,
                    "shift_vector": [0.0, 1.0]
                }
            ]
            shift_path.write_text(json.dumps(candidates))

            output_path = Path(tmpdir) / "output.json"

            # Mock run_permutation_chunked to return deterministic values
            with patch('src.models.trajectory_permutation.SHIFT_RESULTS_PATH', str(shift_path)):
                with patch('src.models.trajectory_permutation.OUTPUT_PATH', str(output_path)):
                    with patch('src.models.trajectory_permutation.run_permutation_chunked') as mock_chunked:
                        # Return a mix of values to ensure p-value calculation works
                        mock_chunked.return_value = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
                        
                        result = run_trajectory_permutation_pipeline()

            assert result["status"] == "success"
            assert result["n_species_processed"] == 2
            
            # Verify output structure
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "records" in data
            assert len(data["records"]) == 2
            
            # Verify each record has required fields
            for record in data["records"]:
                assert "species" in record
                assert "p_value" in record
                assert "magnitude" in record
                assert "direction" in record
                assert 0.0 <= record["p_value"] <= 1.0