"""
Integration tests for visualization checksum computation.

Tests the end-to-end flow of computing and recording visualization checksums.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
class TestVisualizationChecksumIntegration:
    """Integration tests for visualization checksum computation"""

    @pytest.fixture
    def project_root(self):
        """Get project root path"""
        return Path(__file__).parent.parent.parent

    def test_checksum_script_runs_successfully(self, project_root, tmp_path):
        """Test that the checksum script runs without errors"""
        # Setup test environment
        figures_dir = tmp_path / "data" / "analysis" / "figures"
        figures_dir.mkdir(parents=True)

        # Create test visualization files
        (figures_dir / "scatter_plot.png").write_bytes(b"fake png content 1")
        (figures_dir / "sensitivity_analysis.png").write_bytes(b"fake png content 2")

        manifest_path = tmp_path / "data" / "artifact_hashes.json"

        # Create initial manifest
        initial_manifest = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {},
        }
        with open(manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        # Run the checksum script
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "code" / "checksum_visualizations.py"),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PROJECT_ROOT": str(tmp_path)},
        )

        # Script should complete successfully
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_checksums_recorded_in_manifest(self, project_root, tmp_path):
        """Test that checksums are properly recorded in manifest"""
        # Setup test environment
        figures_dir = tmp_path / "data" / "analysis" / "figures"
        figures_dir.mkdir(parents=True)

        # Create test visualization files with known content
        content1 = b"test visualization content 1"
        content2 = b"test visualization content 2"
        (figures_dir / "test1.png").write_bytes(content1)
        (figures_dir / "test2.png").write_bytes(content2)

        manifest_path = tmp_path / "data" / "artifact_hashes.json"

        # Create initial manifest
        initial_manifest = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {},
        }
        with open(manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        # Run the checksum script
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "code" / "checksum_visualizations.py"),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PROJECT_ROOT": str(tmp_path)},
        )

        assert result.returncode == 0

        # Verify manifest was updated
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert "artifact_hashes" in manifest
        assert "visualizations" in manifest["artifact_hashes"]

        visualizations_data = manifest["artifact_hashes"]["visualizations"]
        assert "artifacts" in visualizations_data

        # Verify both files have checksums
        artifacts = visualizations_data["artifacts"]
        assert len(artifacts) == 2

        # Verify checksum format (SHA-256 hex string)
        for rel_path, artifact_info in artifacts.items():
            assert "checksum" in artifact_info
            assert len(artifact_info["checksum"]) == 64  # SHA-256 hex length
            assert all(c in "0123456789abcdef" for c in artifact_info["checksum"])

    def test_checksums_deterministic(self, project_root, tmp_path):
        """Test that checksums are deterministic for same content"""
        # Setup test environment
        figures_dir = tmp_path / "data" / "analysis" / "figures"
        figures_dir.mkdir(parents=True)

        # Create test file with known content
        content = b"deterministic test content"
        test_file = figures_dir / "deterministic.png"
        test_file.write_bytes(content)

        manifest_path = tmp_path / "data" / "artifact_hashes.json"

        # Create initial manifest
        initial_manifest = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {},
        }
        with open(manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        # Run checksum script first time
        result1 = subprocess.run(
            [
                sys.executable,
                str(project_root / "code" / "checksum_visualizations.py"),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PROJECT_ROOT": str(tmp_path)},
        )

        assert result1.returncode == 0

        # Read first checksum
        with open(manifest_path, "r") as f:
            manifest1 = json.load(f)
        checksum1 = manifest1["artifact_hashes"]["visualizations"]["artifacts"][
            "data/analysis/figures/deterministic.png"
        ]["checksum"]

        # Run checksum script second time
        result2 = subprocess.run(
            [
                sys.executable,
                str(project_root / "code" / "checksum_visualizations.py"),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PROJECT_ROOT": str(tmp_path)},
        )

        assert result2.returncode == 0

        # Read second checksum
        with open(manifest_path, "r") as f:
            manifest2 = json.load(f)
        checksum2 = manifest2["artifact_hashes"]["visualizations"]["artifacts"][
            "data/analysis/figures/deterministic.png"
        ]["checksum"]

        # Checksums should be identical
        assert checksum1 == checksum2
