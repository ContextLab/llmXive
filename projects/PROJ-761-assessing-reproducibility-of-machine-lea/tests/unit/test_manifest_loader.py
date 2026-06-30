"""
Unit tests for the manifest loader and validator (T009).
"""

import pytest
import yaml
import os
import tempfile
from pathlib import Path

# Import the module under test
# We assume this file is in tests/unit/, so we go up two levels to find 'code'
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from manifest_loader import (
    load_manifest,
    validate_manifest,
    load_and_validate_manifest,
    ManifestValidationError,
    REQUIRED_TOP_LEVEL_KEYS,
    REQUIRED_METRIC_KEYS
)


class TestValidateManifest:
    """Tests for the validate_manifest function."""

    def test_valid_manifest(self):
        """Test that a complete valid manifest passes validation."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": {
                "mae": 0.1,
                "r2": 0.9,
                "spearman_rho": 0.95
            }
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is True
        assert errors == []

    def test_missing_doi(self):
        """Test validation fails if DOI is missing."""
        data = {
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.95}
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("doi" in err for err in errors)

    def test_missing_repo_url(self):
        """Test validation fails if repo_url is missing."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "dataset_name": "test_dataset",
            "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.95}
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("repo_url" in err for err in errors)

    def test_missing_dataset_name(self):
        """Test validation fails if dataset_name is missing."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.95}
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("dataset_name" in err for err in errors)

    def test_missing_reported_metrics(self):
        """Test validation fails if reported_metrics is missing."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset"
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("reported_metrics" in err for err in errors)

    def test_missing_mae_metric(self):
        """Test validation fails if MAE is missing from metrics."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": {
                "r2": 0.9,
                "spearman_rho": 0.95
            }
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("mae" in err for err in errors)

    def test_missing_r2_metric(self):
        """Test validation fails if R2 is missing from metrics."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": {
                "mae": 0.1,
                "spearman_rho": 0.95
            }
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("r2" in err for err in errors)

    def test_missing_spearman_rho_metric(self):
        """Test validation fails if Spearman rho is missing from metrics."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": {
                "mae": 0.1,
                "r2": 0.9
            }
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("spearman_rho" in err for err in errors)

    def test_reported_metrics_not_dict(self):
        """Test validation fails if reported_metrics is not a dict."""
        data = {
            "doi": "10.1021/acscatal.0c01234",
            "repo_url": "https://github.com/example/repo",
            "dataset_name": "test_dataset",
            "reported_metrics": "invalid_string"
        }
        is_valid, errors = validate_manifest(data)
        assert is_valid is False
        assert any("dictionary" in err for err in errors)


class TestLoadManifest:
    """Tests for the load_manifest function."""

    def test_load_valid_yaml(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = {
                "doi": "10.1021/acscatal.0c01234",
                "repo_url": "https://github.com/example/repo",
                "dataset_name": "test",
                "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.9}
            }
            yaml.dump(yaml_content, f)
            f.flush()
            temp_path = Path(f.name)

        try:
            data = load_manifest(temp_path)
            assert data["doi"] == "10.1021/acscatal.0c01234"
            assert data["reported_metrics"]["mae"] == 0.1
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_manifest(Path("/nonexistent/path/manifest.yaml"))

    def test_empty_file(self):
        """Test that YAMLError is raised for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(Exception): # yaml.YAMLError or similar
                load_manifest(temp_path)
        finally:
            os.unlink(temp_path)


class TestLoadAndValidateManifest:
    """Tests for the combined load_and_validate_manifest function."""

    def test_success(self):
        """Test successful load and validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = {
                "doi": "10.1021/acscatal.0c01234",
                "repo_url": "https://github.com/example/repo",
                "dataset_name": "test",
                "reported_metrics": {"mae": 0.1, "r2": 0.9, "spearman_rho": 0.9}
            }
            yaml.dump(yaml_content, f)
            f.flush()
            temp_path = Path(f.name)

        try:
            data = load_and_validate_manifest(temp_path)
            assert data is not None
            assert "doi" in data
        finally:
            os.unlink(temp_path)

    def test_validation_error_raised(self):
        """Test that ManifestValidationError is raised on validation failure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = {
                "doi": "10.1021/acscatal.0c01234",
                "repo_url": "https://github.com/example/repo",
                "dataset_name": "test",
                "reported_metrics": {"mae": 0.1} # Missing r2 and spearman_rho
            }
            yaml.dump(yaml_content, f)
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ManifestValidationError):
                load_and_validate_manifest(temp_path)
        finally:
            os.unlink(temp_path)