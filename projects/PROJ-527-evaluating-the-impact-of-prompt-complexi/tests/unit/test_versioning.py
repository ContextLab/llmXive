import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.versioning import (
    compute_file_hash,
    generate_version_manifest,
    update_project_manifest,
)
from utils.hash_artifacts import compute_sha256


class TestVersioning:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_artifact(self, temp_dir):
        artifact_path = temp_dir / "sample_data.json"
        artifact_path.write_text(json.dumps({"key": "value"}))
        return artifact_path

    def test_compute_file_hash(self, temp_dir, sample_artifact):
        """Test that file hash is computed correctly."""
        expected_hash = compute_sha256(str(sample_artifact))
        actual_hash = compute_file_hash(sample_artifact)
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length

    def test_generate_version_manifest_creates_file(self, temp_dir, sample_artifact):
        """Test that generate_version_manifest creates a valid YAML file."""
        output_dir = temp_dir / "state" / "projects"
        artifacts = [{"path": str(sample_artifact), "hash": compute_file_hash(sample_artifact)}]

        manifest_path = generate_version_manifest("TEST-001", artifacts, output_dir)

        assert manifest_path.exists()
        assert manifest_path.name == "TEST-001.yaml"

        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        assert manifest_data["project_id"] == "TEST-001"
        assert "artifacts" in manifest_data
        assert len(manifest_data["artifacts"]) == 1
        assert manifest_data["artifacts"][0]["path"] == str(sample_artifact)
        assert "generated_at" in manifest_data

    def test_update_project_manifest_adds_new_artifact(self, temp_dir, sample_artifact):
        """Test that update_project_manifest adds a new artifact to existing manifest."""
        output_dir = temp_dir / "state" / "projects"
        output_dir.mkdir(parents=True, exist_ok=True)

        # First, create a manifest with one artifact
        artifacts = [{"path": str(sample_artifact), "hash": compute_file_hash(sample_artifact)}]
        generate_version_manifest("TEST-002", artifacts, output_dir)

        # Create a second artifact
        second_artifact = temp_dir / "second_data.json"
        second_artifact.write_text(json.dumps({"another": "value"}))

        # Update manifest with second artifact
        manifest_path = update_project_manifest("TEST-002", second_artifact, output_dir)

        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        assert len(manifest_data["artifacts"]) == 2
        paths = [a["path"] for a in manifest_data["artifacts"]]
        assert str(sample_artifact) in paths
        assert str(second_artifact) in paths

    def test_update_project_manifest_updates_existing_artifact(self, temp_dir, sample_artifact):
        """Test that update_project_manifest updates an existing artifact's hash."""
        output_dir = temp_dir / "state" / "projects"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest
        artifacts = [{"path": str(sample_artifact), "hash": compute_file_hash(sample_artifact)}]
        generate_version_manifest("TEST-003", artifacts, output_dir)

        # Modify the artifact
        sample_artifact.write_text(json.dumps({"key": "modified_value"}))

        # Update manifest
        manifest_path = update_project_manifest("TEST-003", sample_artifact, output_dir)

        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        assert len(manifest_data["artifacts"]) == 1
        updated_hash = manifest_data["artifacts"][0]["hash"]
        expected_hash = compute_sha256(str(sample_artifact))
        assert updated_hash == expected_hash

    def test_update_project_manifest_creates_new_if_missing(self, temp_dir, sample_artifact):
        """Test that update_project_manifest creates a new manifest if none exists."""
        output_dir = temp_dir / "state" / "projects"
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = update_project_manifest("TEST-004", sample_artifact, output_dir)

        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        assert manifest_data["project_id"] == "TEST-004"
        assert len(manifest_data["artifacts"]) == 1
        assert manifest_data["artifacts"][0]["path"] == str(sample_artifact)
