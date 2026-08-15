"""
Unit Tests for Pearson Correlation Analysis (T033a)

Tests:
  - load_feature_importance_data
  - load_thermal_conductivity_data
  - align_data
  - compute_pearson_correlation
  - generate_correlation_report
  - save_results
"""
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import the module under test
from analysis.pearson_correlation import (
    load_feature_importance_data,
    load_thermal_conductivity_data,
    align_data,
    compute_pearson_correlation,
    generate_correlation_report,
    save_results,
    main
)


class TestLoadFeatureImportanceData:
    def test_load_existing_file(self):
        """Test loading an existing feature importance file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data = {
                "sample_1": {"feat1": 0.5, "feat2": 0.3},
                "sample_2": {"feat1": 0.2, "feat2": 0.8}
            }
            file_path = tmpdir / "feature_importance.json"
            with open(file_path, 'w') as f:
                json.dump(data, f)

            result = load_feature_importance_data(tmpdir)
            assert result == data

    def test_missing_file_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_feature_importance_data(Path(tmpdir))


class TestLoadThermalConductivityData:
    def test_load_pickle_files(self):
        """Test loading conductivity from pickle files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create sample pickle files
            for i in range(3):
                sample = {
                    "sample_id": f"sample_{i}",
                    "thermal_conductivity": 1.0 + i * 0.5
                }
                file_path = tmpdir / f"sample_{i}.pkl"
                with open(file_path, 'wb') as f:
                    pickle.dump(sample, f)

            result = load_thermal_conductivity_data(tmpdir)
            assert len(result) == 3
            assert result["sample_0"] == 1.0
            assert result["sample_1"] == 1.5
            assert result["sample_2"] == 2.0

    def test_missing_directory_raises_error(self):
        """Test that missing directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_thermal_conductivity_data(Path("/nonexistent"))


class TestAlignData:
    def test_align_common_samples(self):
        """Test aligning data with common sample IDs."""
        feature_imp = {
            "s1": {"f1": 0.5},
            "s2": {"f1": 0.3},
            "s3": {"f1": 0.2}
        }
        conductivity = {
            "s1": 1.0,
            "s2": 2.0,
            "s4": 3.0  # s4 not in feature_imp
        }

        x, y, ids = align_data(feature_imp, conductivity)

        assert set(ids) == {"s1", "s2"}
        assert len(x) == 2
        assert len(y) == 2
        # Check values (mean of abs)
        assert x[0] == 0.5  # s1
        assert y[0] == 1.0
        assert x[1] == 0.3  # s2
        assert y[1] == 2.0

    def test_no_common_samples_raises_error(self):
        """Test that no common samples raises ValueError."""
        feature_imp = {"s1": {"f1": 0.5}}
        conductivity = {"s2": 1.0}

        with pytest.raises(ValueError):
            align_data(feature_imp, conductivity)


class TestComputePearsonCorrelation:
    def test_perfect_correlation(self):
        """Test with perfectly correlated data."""
        x = [1.0, 2.0, 3.0, 4.0]
        y = [2.0, 4.0, 6.0, 8.0]
        r, p = compute_pearson_correlation(x, y)
        assert np.isclose(r, 1.0)
        assert p < 0.05

    def test_no_correlation(self):
        """Test with uncorrelated data (small sample)."""
        # Use data that is known to have low correlation
        x = [1.0, 2.0, 3.0, 4.0]
        y = [4.0, 1.0, 3.0, 2.0]
        r, p = compute_pearson_correlation(x, y)
        # r should be small
        assert abs(r) < 0.5

    def test_insufficient_samples_raises_error(self):
        """Test that < 2 samples raises ValueError."""
        with pytest.raises(ValueError):
            compute_pearson_correlation([1.0], [2.0])


class TestGenerateCorrelationReport:
    def test_report_structure(self):
        """Test that the report contains expected keys."""
        report = generate_correlation_report(
            r=0.85,
            p_value=0.01,
            sample_ids=["s1", "s2"],
            n_samples=2
        )

        assert report["analysis_type"] == "Pearson Correlation"
        assert report["spec_reference"] == "FR-005"
        assert report["task_id"] == "T033a"
        assert report["n_samples"] == 2
        assert report["correlation_coefficient"] == 0.85
        assert report["p_value"] == 0.01
        assert "interpretation" in report

class TestSaveResults:
    def test_save_to_file(self):
        """Test saving report to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            report = {"test": "value"}
            output_path = tmpdir / "result.json"

            save_results(report, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == report