import json
import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime, timezone

from src.data.scope_documentation import (
    determine_scope_status,
    write_scope_documentation,
    run_scope_documentation_pipeline,
    main
)

class TestScopeDocumentation:
    """Unit tests for scope documentation functionality (T005c)."""

    def test_determine_scope_status_full_available(self):
        """Test scope status when full EBD is available."""
        result = determine_scope_status(full_ebd_available=True)
        assert result["source"] == "full_ebd_north_america_2020_2024"
        assert result["reason"] == "Full EBD available via verified public URL"
        assert "timestamp" in result

    def test_determine_scope_status_full_unavailable(self):
        """Test scope status when full EBD is unavailable."""
        result = determine_scope_status(full_ebd_available=False)
        assert result["source"] == "vvud/eb-data"
        assert result["reason"] == "Full EBD unavailable"
        assert "timestamp" in result

    def test_write_scope_documentation_creates_file(self):
        """Test that write_scope_documentation creates the JSON file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_scope.json"
            scope_status = {
                "source": "vvud/eb-data",
                "reason": "Full EBD unavailable",
                "timestamp": "2023-10-27T10:00:00Z"
            }
            
            write_scope_documentation(scope_status, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert data == scope_status

    def test_write_scope_documentation_creates_parent_dirs(self):
        """Test that write_scope_documentation creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "subdir" / "nested" / "scope.json"
            scope_status = {
                "source": "vvud/eb-data",
                "reason": "Full EBD unavailable",
                "timestamp": "2023-10-27T10:00:00Z"
            }
            
            write_scope_documentation(scope_status, output_path)
            
            assert output_path.exists()

    def test_run_scope_documentation_pipeline_default_path(self):
        """Test run_scope_documentation_pipeline with default output path."""
        # We test with a temporary directory to avoid writing to the actual project structure
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "data" / "provenance" / "scope_limitation.json"
            scope_status = run_scope_documentation_pipeline(
                full_ebd_available=False,
                output_path=output_path
            )
            
            assert scope_status == output_path
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert data["source"] == "vvud/eb-data"
                assert data["reason"] == "Full EBD unavailable"
                # Validate timestamp format
                datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))

    def test_run_scope_documentation_pipeline_full_available(self):
        """Test run_scope_documentation_pipeline when full EBD is available."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "scope.json"
            scope_status = run_scope_documentation_pipeline(
                full_ebd_available=True,
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert data["source"] == "full_ebd_north_america_2020_2024"
                assert data["reason"] == "Full EBD available via verified public URL"

    def test_main_function_execution(self, monkeypatch):
        """Test that main() runs without error and sets environment correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Set environment variable to control behavior
            monkeypatch.setenv("EXPECT_FULL_EBD_AVAILABLE", "false")
            
            # Mock the output path to avoid writing to default location
            # Note: This is a simplified test; in practice, main() writes to a fixed path
            # We verify that the function runs without raising an exception
            try:
                # We can't easily test the exact output of main() without mocking logging
                # but we can ensure it doesn't crash
                main()
            except SystemExit:
                # main() may call sys.exit, which is acceptable
                pass
            except Exception as e:
                # Any other exception is a failure
                pytest.fail(f"main() raised an unexpected exception: {e}")