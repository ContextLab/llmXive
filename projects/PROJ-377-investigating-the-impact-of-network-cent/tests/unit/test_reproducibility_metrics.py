import pytest
import json
import hashlib
from pathlib import Path
import tempfile
import os

from code.utils.metrics import (
    get_file_checksum,
    get_directory_checksums,
    calculate_artifact_checksums,
    load_validation_metrics,
    load_cv_metrics,
    load_permutation_results,
    load_baseline_r2,
    load_regression_summary,
)


class TestGetFileChecksum:
    def test_returns_valid_checksum(self):
        """Test that a valid checksum is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            content = "Hello, World!"
            with open(file_path, 'w') as f:
                f.write(content)

            checksum = get_file_checksum(str(file_path))

            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex length
            # Verify it's a valid hex string
            int(checksum, 16)  # Should not raise

    def test_different_files_different_checksums(self):
        """Test that different files produce different checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"

            with open(file1, 'w') as f:
                f.write("Content 1")
            with open(file2, 'w') as f:
                f.write("Content 2")

            checksum1 = get_file_checksum(str(file1))
            checksum2 = get_file_checksum(str(file2))

            assert checksum1 != checksum2

    def test_same_file_same_checksum(self):
        """Test that the same file produces the same checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            with open(file_path, 'w') as f:
                f.write("Content")

            checksum1 = get_file_checksum(str(file_path))
            checksum2 = get_file_checksum(str(file_path))

            assert checksum1 == checksum2

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            get_file_checksum("/nonexistent/path/file.txt")


class TestGetDirectoryChecksums:
    def test_returns_checksums_for_all_files(self):
        """Test that checksums are returned for all files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "file1.txt").write_text("Content 1")
            (Path(tmpdir) / "file2.txt").write_text("Content 2")
            (Path(tmpdir) / "subdir").mkdir()
            (Path(tmpdir) / "subdir" / "file3.txt").write_text("Content 3")

            checksums = get_directory_checksums(tmpdir)

            assert isinstance(checksums, dict)
            assert len(checksums) == 3
            assert all(isinstance(v, str) and len(v) == 64 for v in checksums.values())

    def test_handles_empty_directory(self):
        """Test behavior with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksums = get_directory_checksums(tmpdir)
            assert checksums == {}

    def test_excludes_directories(self):
        """Test that only files are included, not directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("Content 1")
            (Path(tmpdir) / "subdir").mkdir()

            checksums = get_directory_checksums(tmpdir)

            assert "file1.txt" in checksums
            assert "subdir" not in checksums


class TestLoadValidationMetrics:
    def test_loads_json_correctly(self):
        """Test that validation metrics are loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
          metrics_path = Path(tmpdir) / "validation_results.json"
          metrics = {
              'p_value': 0.03,
              'null_distribution_mean': 0.0,
              'observed_coef': 0.5
          }
          with open(metrics_path, 'w') as f:
              json.dump(metrics, f)

          result = load_validation_metrics(str(metrics_path))

          assert isinstance(result, dict)
          assert result['p_value'] == 0.03

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_validation_metrics("/nonexistent/path/validation_results.json")


class TestLoadCVMetrics:
    def test_loads_json_correctly(self):
        """Test that CV metrics are loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cv_path = Path(tmpdir) / "cv_results.json"
            metrics = {
                'mean_r2': 0.45,
                'std_r2': 0.05,
                'mean_rmse': 1.2,
                'std_rmse': 0.1
            }
            with open(cv_path, 'w') as f:
                json.dump(metrics, f)

            result = load_cv_metrics(str(cv_path))

            assert isinstance(result, dict)
            assert result['mean_r2'] == 0.45

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_cv_metrics("/nonexistent/path/cv_results.json")


class TestLoadPermutationResults:
    def test_loads_json_correctly(self):
        """Test that permutation results are loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            perm_path = Path(tmpdir) / "permutation_results.json"
            results = {
                'empirical_p_value': 0.02,
                'n_permutations': 1000
            }
            with open(perm_path, 'w') as f:
                json.dump(results, f)

            result = load_permutation_results(str(perm_path))

            assert isinstance(result, dict)
            assert result['empirical_p_value'] == 0.02

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_permutation_results("/nonexistent/path/permutation_results.json")


class TestLoadBaselineR2:
    def test_loads_json_correctly(self):
        """Test that baseline R2 is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline_r2.json"
            results = {
                'baseline_r2': 0.05,
                'n_subjects': 100
            }
            with open(baseline_path, 'w') as f:
                json.dump(results, f)

            result = load_baseline_r2(str(baseline_path))

            assert isinstance(result, dict)
            assert result['baseline_r2'] == 0.05

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_baseline_r2("/nonexistent/path/baseline_r2.json")


class TestLoadRegressionSummary:
    def test_loads_csv_correctly(self):
        """Test that regression summary is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "linear_model_summary.csv"
            data = {
                'parameter': ['Intercept', 'global_centrality', 'age'],
                'coef': [2.5, 0.5, 0.02],
                'p_value': [0.001, 0.03, 0.15]
            }
            df = pd.DataFrame(data)
            df.to_csv(summary_path, index=False)

            result = load_regression_summary(str(summary_path))

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'coef' in result.columns

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_regression_summary("/nonexistent/path/linear_model_summary.csv")