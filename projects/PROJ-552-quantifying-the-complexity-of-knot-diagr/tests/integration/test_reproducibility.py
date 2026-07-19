"""Integration test for reproducibility documentation generation (T035).

This test verifies that the reproducibility pipeline scripts run end-to-end
and generate the required artifacts as specified in US4.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Paths to verify
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs" / "reproducibility"
CHECKSUMS_JSON = DATA_DIR / "checksums.json"
CHECKSUMS_MD = DOCS_DIR / "checksums.md"
STATE_FILE = PROJECT_ROOT / "state" / "manifest.yaml"


def run_script(script_path: Path) -> subprocess.CompletedProcess:
    """Run a Python script and return the result."""
    return subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


class TestReproducibilityGeneration:
    """Test that reproducibility scripts generate correct artifacts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure data directory exists for the test."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Create a dummy file if no data exists to ensure the script runs
        dummy_file = DATA_DIR / "dummy_test.txt"
        if not list(DATA_DIR.glob("*")):
            dummy_file.write_text("test")
        yield
        # Cleanup dummy if we created it
        if dummy_file.exists() and not list(DATA_DIR.glob("*.json")):
            dummy_file.unlink()

    def test_checksum_generator_runs_successfully(self):
        """Test that checksum_generator.py runs without errors."""
        script = PROJECT_ROOT / "code" / "reproducibility" / "checksum_generator.py"
        result = run_script(script)

        assert result.returncode == 0, (
            f"Script failed with rc={result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    def test_checksums_json_is_created(self):
        """Test that data/checksums.json is created and valid JSON."""
        script = PROJECT_ROOT / "code" / "reproducibility" / "checksum_generator.py"
        run_script(script)

        assert CHECKSUMS_JSON.exists(), "checksums.json was not created"

        with open(CHECKSUMS_JSON) as f:
            data = json.load(f)

        assert isinstance(data, dict), "checksums.json must be a JSON object"
        # Verify at least one entry if data exists
        if list(DATA_DIR.glob("*")):
            assert len(data) > 0, "checksums.json is empty but data exists"

    def test_checksums_md_is_created(self):
        """Test that docs/reproducibility/checksums.md is created."""
        script = PROJECT_ROOT / "code" / "reproducibility" / "checksum_generator.py"
        run_script(script)

        assert CHECKSUMS_MD.exists(), "checksums.md was not created"
        content = CHECKSUMS_MD.read_text()
        assert "# Checksums for Data Artifacts" in content, "Markdown header missing"
        assert "SHA-256" in content or "hash" in content.lower(), "Hash content missing"

    def test_state_manifest_updated(self):
        """Test that state/manifest.yaml is updated with checksums."""
        script = PROJECT_ROOT / "code" / "reproducibility" / "checksum_generator.py"
        run_script(script)

        assert STATE_FILE.exists(), "state/manifest.yaml was not created/updated"

        # Verify it contains JSON content (as written by the script)
        content = STATE_FILE.read_text()
        # The script writes JSON to the state file
        try:
            data = json.loads(content)
            assert isinstance(data, dict), "state manifest must be a JSON object"
        except json.JSONDecodeError:
            # If it's not JSON, check if it's empty or a simple YAML (unlikely given script)
            # But the script explicitly writes JSON
            assert False, "state/manifest.yaml is not valid JSON as expected"

    def test_integration_pipeline_flow(self):
        """Test the full flow: run script -> verify artifacts exist and match."""
        script = PROJECT_ROOT / "code" / "reproducibility" / "checksum_generator.py"
        result = run_script(script)

        assert result.returncode == 0

        # Verify consistency between JSON and MD
        with open(CHECKSUMS_JSON) as f:
            json_data = json.load(f)

        md_content = CHECKSUMS_MD.read_text()

        # Check that keys in JSON appear in MD
        for key in json_data:
            # Simple check: key should appear in markdown
            # The markdown format is `- `path``: `hash``
            assert key in md_content, f"Path {key} from JSON not found in MD"