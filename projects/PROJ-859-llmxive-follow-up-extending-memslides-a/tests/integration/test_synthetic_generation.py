"""
Integration test for the synthetic trace generation pipeline.
Validates the end-to-end flow of T012 (synthetic_trace.py).

This test:
1. Executes the generation script.
2. Verifies output files exist in data/raw/.
3. Validates the schema of generated files against contracts/trace.schema.yaml.
4. Ensures statistical variance (sequence lengths, tool types) are present.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Project root detection (assumes running from project root or tests/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "trace.schema.yaml"

# Add code directory to path for imports if running directly
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from utils.validators import TraceValidator
from config import Config


class TestSyntheticGenerationPipeline:
    """Integration tests for the synthetic data generation pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure directories exist before tests run."""
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        # Clean up any previous generation runs for a clean test state
        for f in DATA_RAW_DIR.glob("session_*.json"):
            f.unlink()

    def test_01_script_execution(self):
        """Test that the generation script runs without error."""
        script_path = CODE_DIR / "generators" / "synthetic_trace.py"
        
        if not script_path.exists():
            pytest.fail(f"Generation script not found at {script_path}. "
                        "T012 implementation is missing.")

        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Script execution failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_02_output_files_created(self):
        """Test that session files are created in data/raw/."""
        # Re-run to ensure fresh data if previous test passed
        script_path = CODE_DIR / "generators" / "synthetic_trace.py"
        subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT), check=True)

        session_files = list(DATA_RAW_DIR.glob("session_*.json"))
        
        assert len(session_files) > 0, "No session files were generated in data/raw/."
        assert len(session_files) >= 5, f"Expected at least 5 sessions for variance testing, found {len(session_files)}."

    def test_03_schema_compliance(self):
        """Test that all generated files adhere to the trace schema."""
        script_path = CODE_DIR / "generators" / "synthetic_trace.py"
        subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT), check=True)

        session_files = list(DATA_RAW_DIR.glob("session_*.json"))
        validator = TraceValidator(schema_path=SCHEMA_PATH)

        failed_files = []
        for file_path in session_files:
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    failed_files.append((file_path.name, f"Invalid JSON: {e}"))
                    continue

            is_valid, errors = validator.validate(data)
            if not is_valid:
                failed_files.append((file_path.name, errors))

        if failed_files:
            error_msg = "Schema validation failed for:\n"
            for fname, err in failed_files:
                error_msg += f" - {fname}: {err}\n"
            pytest.fail(error_msg)

    def test_04_variance_in_generation(self):
        """Test that the generator produces variance in sequence length and tool types."""
        script_path = CODE_DIR / "generators" / "synthetic_trace.py"
        subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT), check=True)

        session_files = list(DATA_RAW_DIR.glob("session_*.json"))
        assert len(session_files) > 0

        sequence_lengths = []
        tool_types_seen = set()

        for file_path in session_files:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check for exact_tool_sequence
            if "exact_tool_sequence" in data and isinstance(data["exact_tool_sequence"], list):
                sequence_lengths.append(len(data["exact_tool_sequence"]))
                for step in data["exact_tool_sequence"]:
                    if isinstance(step, dict) and "tool_type" in step:
                        tool_types_seen.add(step["tool_type"])
                    elif isinstance(step, str):
                        # Handle potential string-only format if schema allows
                        tool_types_seen.add(step)

        # Assert variance exists
        assert len(sequence_lengths) > 1, "Only one session generated; cannot test variance."
        unique_lengths = len(set(sequence_lengths))
        assert unique_lengths > 1, (
            f"All generated sessions have the same length ({sequence_lengths[0]}). "
            "T013 (variation logic) may not be implemented."
        )

        # Assert multiple tool types are used
        assert len(tool_types_seen) > 1, (
            f"Only one tool type ({tool_types_seen}) was used. "
            "T013 (variation logic) may not be implemented."
        )

    def test_05_required_fields_present(self):
        """Test that critical fields defined in the task description are present."""
        script_path = CODE_DIR / "generators" / "synthetic_trace.py"
        subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT), check=True)

        session_files = list(DATA_RAW_DIR.glob("session_*.json"))
        required_fields = ["exact_tool_sequence", "raw_arg_variance"]

        for file_path in session_files:
            with open(file_path, 'r') as f:
                data = json.load(f)

            missing = [field for field in required_fields if field not in data]
            assert not missing, f"File {file_path.name} is missing required fields: {missing}"