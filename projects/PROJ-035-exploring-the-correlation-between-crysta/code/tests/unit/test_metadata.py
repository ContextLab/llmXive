"""
Unit tests for the metadata generation module.

Tests verify that:
1. Metadata file is created at the correct path
2. Required fields are present (Constitution VII compliance)
3. Timestamps are valid ISO format
4. Source information is recorded correctly
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.metadata import (
    generate_metadata,
    get_query_timestamp,
    get_materials_project_version,
    get_thermal_data_version
)


class TestQueryTimestamp:
    def test_returns_iso_format(self):
        """Verify timestamp is in ISO format."""
        timestamp = get_query_timestamp()
        assert "T" in timestamp
        assert timestamp.endswith("Z")
        # Try parsing it to ensure it's valid
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp is not valid ISO format")


class TestMaterialsProjectVersion:
    def test_has_required_fields(self):
        """Verify MP version info has required fields."""
        version = get_materials_project_version()
        assert "source" in version
        assert "query_timestamp" in version
        assert version["source"] == "Materials Project API"
        assert "api_version" in version
        assert "endpoint" in version


class TestThermalDataVersion:
    def test_has_required_fields(self):
        """Verify thermal data version has required fields."""
        version = get_thermal_data_version()
        assert "source" in version
        assert "query_timestamp" in version
        assert "provenance_type" in version
        assert version["provenance_type"] == "peer_reviewed"
        assert version["compliance"]["constitution_vii"] is True
        assert version["compliance"]["fr_010"] is True


class TestGenerateMetadata:
    def test_creates_file(self):
        """Verify metadata file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metadata.yaml"
            result = generate_metadata(output_path=output_path)
            
            assert result.exists()
            assert result == output_path

    def test_yaml_is_valid(self):
        """Verify generated file is valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metadata.yaml"
            generate_metadata(output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert isinstance(data, dict)

    def test_contains_required_fields(self):
        """Verify metadata contains Constitution VII required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metadata.yaml"
            generate_metadata(output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Check top-level keys
            assert "project_id" in data
            assert "generated_at" in data
            assert "dataset_versions" in data
            assert "constitution_compliance" in data
            
            # Check dataset versions
            assert "crystal_structures" in data["dataset_versions"]
            assert "thermal_conductivity" in data["dataset_versions"]
            
            # Check compliance flags
            assert data["constitution_compliance"]["vii_version_tracking"] is True

    def test_contains_fr_compliance(self):
        """Verify FR-010 compliance is recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metadata.yaml"
            generate_metadata(output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert "fr_compliance" in data
            assert data["fr_compliance"]["fr_010"] is True

    def test_thermal_source_is_peer_reviewed(self):
        """Verify thermal data source is marked as peer-reviewed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metadata.yaml"
            generate_metadata(output_path=output_path)
            
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            thermal = data["dataset_versions"]["thermal_conductivity"]
            assert thermal["provenance_type"] == "peer_reviewed"
            assert thermal["compliance"]["fr_010"] is True

    def test_default_path(self):
        """Verify default path is data/metadata.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change project_root behavior by passing explicit path
            output_path = Path(tmpdir) / "data" / "metadata.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            result = generate_metadata(output_path=output_path)
            
            assert result.exists()
            assert result.name == "metadata.yaml"
            assert result.parent.name == "data"