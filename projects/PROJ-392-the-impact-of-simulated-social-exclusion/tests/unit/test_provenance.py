"""
Unit tests for provenance generation utilities.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from utils.provenance import (
    generate_provenance_sidecar,
    generate_provenance_manifest,
    get_software_versions,
    PIPELINE_VERSION,
)


class TestProvenanceSidecar:
    """Tests for individual provenance sidecar generation."""

    def test_generate_sidecar_creates_file(self):
        """Test that sidecar file is created with correct naming convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.nii.gz"
            output_file = Path(tmpdir) / "output.nii.gz"

            # Create dummy files
            input_file.touch()
            output_file.touch()

            sidecar_path = generate_provenance_sidecar(
                input_file=str(input_file),
                output_file=str(output_file),
                parameters={"smoothing": 6, "realign": True},
            )

            assert os.path.exists(sidecar_path)
            assert "output_provenance.nii.gz.yaml" in sidecar_path

    def test_sidecar_content_structure(self):
        """Test that sidecar contains all required provenance fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.nii.gz"
            output_file = Path(tmpdir) / "output.nii.gz"

            input_file.touch()
            output_file.touch()

            sidecar_path = generate_provenance_sidecar(
                input_file=str(input_file),
                output_file=str(output_file),
                parameters={"smoothing": 6},
                software_versions={"nibabel": "5.1.0", "numpy": "1.24.0"},
            )

            with open(sidecar_path, "r") as f:
                data = yaml.safe_load(f)

            # Check required fields
            assert "id" in data
            assert "type" in data
            assert "dct:identifier" in data
            assert "dct:title" in data
            assert "dct:created" in data
            assert "pipeline" in data
            assert data["pipeline"]["version"] == PIPELINE_VERSION
            assert "parameters" in data
            assert "software" in data
            assert "inputs" in data
            assert "outputs" in data

    def test_sidecar_with_custom_execution_id(self):
        """Test sidecar generation with custom execution ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.nii.gz"
            output_file = Path(tmpdir) / "output.nii.gz"

            input_file.touch()
            output_file.touch()

            custom_id = "test-execution-123"
            sidecar_path = generate_provenance_sidecar(
                input_file=str(input_file),
                output_file=str(output_file),
                execution_id=custom_id,
            )

            with open(sidecar_path, "r") as f:
                data = yaml.safe_load(f)

            assert data["id"] == custom_id
            assert data["dct:identifier"] == custom_id

    def test_sidecar_handles_empty_parameters(self):
        """Test sidecar generation with no parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.nii.gz"
            output_file = Path(tmpdir) / "output.nii.gz"

            input_file.touch()
            output_file.touch()

            sidecar_path = generate_provenance_sidecar(
                input_file=str(input_file),
                output_file=str(output_file),
            )

            with open(sidecar_path, "r") as f:
                data = yaml.safe_load(f)

            assert data["parameters"] == {}


class TestProvenanceManifest:
    """Tests for provenance manifest generation."""

    def test_manifest_creation(self):
        """Test that manifest file is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some dummy sidecars
            for i in range(3):
                input_file = Path(tmpdir) / f"input_{i}.nii.gz"
                output_file = Path(tmpdir) / f"output_{i}.nii.gz"
                input_file.touch()
                output_file.touch()

                generate_provenance_sidecar(
                    input_file=str(input_file),
                    output_file=str(output_file),
                )

            manifest_path = generate_provenance_manifest(output_dir=tmpdir)

            assert os.path.exists(manifest_path)
            assert "provenance_manifest.yaml" in manifest_path

    def test_manifest_content(self):
        """Test manifest contains correct metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a sidecar
            input_file = Path(tmpdir) / "input.nii.gz"
            output_file = Path(tmpdir) / "output.nii.gz"
            input_file.touch()
            output_file.touch()

            generate_provenance_sidecar(
                input_file=str(input_file),
                output_file=str(output_file),
            )

            manifest_path = generate_provenance_manifest(output_dir=tmpdir)

            with open(manifest_path, "r") as f:
                data = yaml.safe_load(f)

            assert "pipeline" in data
            assert "generated_at" in data
            assert "manifest_id" in data
            assert "total_sidecars" in data
            assert data["total_sidecars"] == 1
            assert "sidecars" in data
            assert len(data["sidecars"]) == 1

            sidecar_entry = data["sidecars"][0]
            assert "file" in sidecar_entry
            assert "execution_id" in sidecar_entry
            assert "input_file" in sidecar_entry
            assert "output_file" in sidecar_entry


class TestSoftwareVersions:
    """Tests for software version detection."""

    def test_get_software_versions_returns_dict(self):
        """Test that software versions function returns a dictionary."""
        versions = get_software_versions()
        assert isinstance(versions, dict)
        assert len(versions) > 0

    def test_known_packages_in_versions(self):
        """Test that known packages are included in version dict."""
        versions = get_software_versions()
        # At least some packages should be detected
        assert any(v != "not installed" for v in versions.values())


class TestIntegration:
    """Integration tests for provenance workflow."""

    def test_full_provenance_workflow(self):
        """Test complete workflow: process file -> generate sidecar -> generate manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate preprocessing output
            processed_files = []
            for i in range(5):
                input_file = Path(tmpdir) / f"sub-{i:03d}_task-rest_bold.nii.gz"
                output_file = Path(tmpdir) / f"sub-{i:03d}_task-rest_space-MNI_bold.nii.gz"
                input_file.touch()
                output_file.touch()

                # Generate sidecar for each processed file
                generate_provenance_sidecar(
                    input_file=str(input_file),
                    output_file=str(output_file),
                    parameters={
                        "smoothing": 6,
                        "realign": True,
                        "normalize": True,
                        "slice_timing": True,
                    },
                    software_versions=get_software_versions(),
                )
                processed_files.append(output_file)

            # Generate manifest
            manifest_path = generate_provenance_manifest(output_dir=tmpdir)

            # Verify manifest
            with open(manifest_path, "r") as f:
                manifest_data = yaml.safe_load(f)

            assert manifest_data["total_sidecars"] == 5
            assert len(manifest_data["sidecars"]) == 5

            # Verify each sidecar is referenced
            for sidecar_entry in manifest_data["sidecars"]:
                assert os.path.exists(sidecar_entry["file"])
                assert "sub-" in sidecar_entry["file"]
                assert "_provenance" in sidecar_entry["file"]
