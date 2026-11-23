"""
Unit tests for group analysis (Fisher's Z transformation and aggregation).
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.models.group_analysis import (
    fisher_z_transform,
    inverse_fisher_z,
    aggregate_group_stats,
    run_group_rsa_analysis
)

class TestFisherZTransform:
    """Tests for Fisher's Z transformation functions."""

    def test_fisher_z_identity(self):
        """Test that Fisher's Z is approximately identity for r=0."""
        z = fisher_z_transform(0.0)
        assert abs(z) < 1e-10

    def test_fisher_z_positive_correlation(self):
        """Test Fisher's Z for positive correlations."""
        r = 0.5
        z = fisher_z_transform(r)
        # Z should be positive for positive r
        assert z > 0
        # Check approximate value: Z(0.5) ≈ 0.549
        assert abs(z - 0.5493) < 0.01

    def test_fisher_z_negative_correlation(self):
        """Test Fisher's Z for negative correlations."""
        r = -0.5
        z = fisher_z_transform(r)
        # Z should be negative for negative r
        assert z < 0
        # Check approximate value: Z(-0.5) ≈ -0.549
        assert abs(z - (-0.5493)) < 0.01

    def test_fisher_z_boundary_clamping(self):
        """Test that boundary values are handled correctly."""
        # Values at exactly 1 or -1 would cause division by zero
        # The function should clamp them
        z_99 = fisher_z_transform(0.999999)
        z_neg_99 = fisher_z_transform(-0.999999)
        assert np.isfinite(z_99)
        assert np.isfinite(z_neg_99)
        assert z_99 > 0
        assert z_neg_99 < 0

    def test_inverse_fisher_z_roundtrip(self):
        """Test that inverse_fisher_z(fisher_z_transform(r)) ≈ r."""
        r_values = [-0.9, -0.5, 0.0, 0.5, 0.9]
        for r in r_values:
            z = fisher_z_transform(r)
            r_recovered = inverse_fisher_z(z)
            assert abs(r - r_recovered) < 1e-6

    def test_array_input(self):
        """Test that functions work with numpy arrays."""
        r_array = np.array([0.0, 0.5, -0.5])
        z_array = fisher_z_transform(r_array)
        assert isinstance(z_array, np.ndarray)
        assert len(z_array) == 3
        assert z_array[0] == 0.0
        assert z_array[1] > 0
        assert z_array[2] < 0

class TestAggregateGroupStats:
    """Tests for group aggregation function."""

    def test_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            aggregate_group_stats([])

    def test_single_subject(self):
        """Test aggregation with a single subject."""
        single_subject = {
            "hippocampus": {
                "early_late": 0.5,
                "early_early": 0.8
            }
        }
        result = aggregate_group_stats([single_subject])
        
        assert "hippocampus" in result
        assert "early_late" in result["hippocampus"]
        assert result["hippocampus"]["early_late"]["n_subjects"] == 1
        # Mean should be the same as input
        assert abs(result["hippocampus"]["early_late"]["mean_r"] - 0.5) < 1e-6

    def test_multiple_subjects(self):
        """Test aggregation with multiple subjects."""
        subjects = [
            {"hippocampus": {"early_late": 0.5, "early_early": 0.8}},
            {"hippocampus": {"early_late": 0.6, "early_early": 0.7}},
            {"hippocampus": {"early_late": 0.4, "early_early": 0.9}}
        ]
        result = aggregate_group_stats(subjects)
        
        assert result["hippocampus"]["early_late"]["n_subjects"] == 3
        # Mean r should be approximately 0.5
        mean_r = result["hippocampus"]["early_late"]["mean_r"]
        assert 0.4 < mean_r < 0.6

    def test_multiple_rois(self):
        """Test aggregation with multiple ROIs."""
        subjects = [
            {
                "hippocampus": {"early_late": 0.5, "early_early": 0.8},
                "mPFC": {"early_late": 0.3, "early_early": 0.6}
            },
            {
                "hippocampus": {"early_late": 0.6, "early_early": 0.7},
                "mPFC": {"early_late": 0.4, "early_early": 0.5}
            }
        ]
        result = aggregate_group_stats(subjects)
        
        assert "hippocampus" in result
        assert "mPFC" in result
        assert result["hippocampus"]["early_late"]["n_subjects"] == 2
        assert result["mPFC"]["early_late"]["n_subjects"] == 2

    def test_missing_roi_in_some_subjects(self):
        """Test handling of missing ROIs in some subjects."""
        subjects = [
            {"hippocampus": {"early_late": 0.5}},
            {"hippocampus": {"early_late": 0.6}, "mPFC": {"early_late": 0.3}},
            {"hippocampus": {"early_late": 0.4}}
        ]
        # Should use intersection of ROIs (only hippocampus)
        result = aggregate_group_stats(subjects)
        
        assert "hippocampus" in result
        assert "mPFC" not in result
        assert result["hippocampus"]["early_late"]["n_subjects"] == 3

class TestRunGroupRsaAnalysis:
    """Tests for the main analysis function."""

    def test_run_with_temp_files(self):
        """Test running the full analysis pipeline with temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "results"
            input_dir.mkdir()
            output_path = Path(tmpdir) / "group_rsa_stats.json"

            # Create fake subject files
            for i in range(3):
                subject_data = {
                    "hippocampus": {"early_late": 0.5 + i * 0.1, "early_early": 0.8},
                    "mPFC": {"early_late": 0.3 + i * 0.05, "early_early": 0.6}
                }
                with open(input_dir / f"sub-0{i+1}_rsa.json", 'w') as f:
                    json.dump(subject_data, f)

            # Run analysis
            result = run_group_rsa_analysis(input_dir, output_path)

            # Check output file exists
            assert output_path.exists()

            # Check result structure
            assert "n_subjects" in result
            assert result["n_subjects"] == 3
            assert "results" in result
            assert "hippocampus" in result["results"]
            assert "mPFC" in result["results"]

            # Verify file content
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result == result

    def test_run_with_combined_file(self):
        """Test running analysis when only a combined file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "results"
            input_dir.mkdir()
            output_path = Path(tmpdir) / "group_rsa_stats.json"

            # Create a combined file with multiple subjects
            combined_data = {
                "sub-01": {"hippocampus": {"early_late": 0.5, "early_early": 0.8}},
                "sub-02": {"hippocampus": {"early_late": 0.6, "early_early": 0.7}}
            }
            with open(input_dir / "rsa_matrices.json", 'w') as f:
                json.dump(combined_data, f)

            # Run analysis
            result = run_group_rsa_analysis(input_dir, output_path)

            assert output_path.exists()
            assert result["n_subjects"] == 2

    def test_run_with_no_files(self):
        """Test that running with no input files raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "results"
            input_dir.mkdir()
            output_path = Path(tmpdir) / "group_rsa_stats.json"

            with pytest.raises(FileNotFoundError):
                run_group_rsa_analysis(input_dir, output_path)
