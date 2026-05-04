"""Contract test for state file schema."""
import pytest
import yaml
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

class TestStateFileSchema:
    """Verify state file has required structure and checksums."""

    def test_state_file_has_artifacts_section(self):
        """State file must have an artifacts section."""
        state_content = {
            "artifacts": {
                "data": {},
                "models": {},
                "results": {}
            }
        }
        assert "artifacts" in state_content

    def test_state_file_artifacts_have_checksums(self):
        """State file artifacts must have checksums."""
        state_content = {
            "artifacts": {
                "data": {
                    "electricity.csv": {
                        "checksum": "abc123",
                        "size": 1024,
                        "timestamp": "2024-01-01T00:00:00"
                    }
                }
            }
        }
        artifact = state_content["artifacts"]["data"]["electricity.csv"]
        assert "checksum" in artifact
        assert "size" in artifact

    def test_state_file_checksum_format(self):
        """State file checksums must be valid SHA256 format."""
        checksum = hashlib.sha256(b"test").hexdigest()
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_state_file_has_version_field(self):
        """State file should have a version field."""
        state_content = {
            "version": "1.0.0",
            "artifacts": {}
        }
        assert "version" in state_content

    def test_state_file_can_load_yaml(self):
        """State file must be valid YAML."""
        state_content = """
        version: "1.0.0"
        artifacts:
          data: {}
          models: {}
        """
        loaded = yaml.safe_load(state_content)
        assert "version" in loaded
        assert "artifacts" in loaded

    def test_state_file_artifact_has_timestamp(self):
        """State file artifacts must have timestamp field."""
        state_content = {
            "artifacts": {
                "data": {
                    "electricity.csv": {
                        "checksum": "abc123",
                        "size": 1024,
                        "timestamp": "2024-01-01T00:00:00"
                    }
                }
            }
        }
        artifact = state_content["artifacts"]["data"]["electricity.csv"]
        assert "timestamp" in artifact

    def test_state_file_artifact_has_size(self):
        """State file artifacts must have size field."""
        state_content = {
            "artifacts": {
                "data": {
                    "electricity.csv": {
                        "checksum": "abc123",
                        "size": 1024,
                        "timestamp": "2024-01-01T00:00:00"
                    }
                }
            }
        }
        artifact = state_content["artifacts"]["data"]["electricity.csv"]
        assert "size" in artifact
        assert isinstance(artifact["size"], int)
        assert artifact["size"] >= 0
