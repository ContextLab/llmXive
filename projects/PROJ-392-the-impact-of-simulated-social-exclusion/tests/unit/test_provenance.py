"""
Unit tests for the provenance module.
"""
import json
import os
import tempfile
from pathlib import Path
import yaml

import pytest

from code.utils.provenance import (
    generate_provenance_record,
    write_provenance_sidecar,
)
from code.utils.checksums import compute_sha256


@pytest.fixture
def temp_artifact():
    """Create a temporary file to act as an artifact."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".nii.gz") as f:
        f.write("fake nifti content")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_input_file():
    """Create a temporary input file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tsv") as f:
        f.write("participant_id\tage\n001\t25")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_generate_provenance_record(temp_artifact):
    """Test that a provenance record is generated correctly."""
    record = generate_provenance_record(
        artifact_path=temp_artifact,
        pipeline_name="test-pipeline",
        pipeline_version="0.1.0",
        parameters={"smoothing": 6},
        input_files=[temp_artifact],
    )
    
    assert "provenance" in record
    assert record["provenance"]["pipeline"]["name"] == "test-pipeline"
    assert record["provenance"]["pipeline"]["version"] == "0.1.0"
    assert record["provenance"]["artifact"]["path"] == os.path.basename(temp_artifact)
    assert "checksum_sha256" in record["provenance"]["artifact"]
    assert record["provenance"]["parameters"]["smoothing"] == 6
    assert "input_files" in record["provenance"]


def test_provenance_checksum_matches_file(temp_artifact):
    """Verify that the checksum in the record matches the actual file checksum."""
    record = generate_provenance_record(artifact_path=temp_artifact)
    
    recorded_checksum = record["provenance"]["artifact"]["checksum_sha256"]
    actual_checksum = compute_sha256(temp_artifact)
    
    assert recorded_checksum == actual_checksum


def test_write_provenance_sidecar(temp_artifact):
    """Test that a sidecar file is written correctly."""
    sidecar_path = write_provenance_sidecar(
        artifact_path=temp_artifact,
        pipeline_name="test-pipeline",
        pipeline_version="0.1.0",
        parameters={"kernel": 4},
    )
    
    assert os.path.exists(sidecar_path)
    assert sidecar_path.endswith("_provenance.yaml")
    
    with open(sidecar_path, "r") as f:
        loaded_data = yaml.safe_load(f)
    
    assert loaded_data["provenance"]["pipeline"]["name"] == "test-pipeline"
    assert loaded_data["provenance"]["parameters"]["kernel"] == 4


def test_write_provenance_sidecar_custom_output_dir(temp_artifact):
    """Test writing sidecar to a custom directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sidecar_path = write_provenance_sidecar(
            artifact_path=temp_artifact,
            output_dir=tmpdir,
            pipeline_name="custom-output-test",
        )
        
        assert os.path.exists(sidecar_path)
        assert tmpdir in sidecar_path


def test_generate_provenance_missing_file():
    """Test that FileNotFoundError is raised for missing artifact."""
    with pytest.raises(FileNotFoundError):
        generate_provenance_record(artifact_path="/nonexistent/path/file.nii")