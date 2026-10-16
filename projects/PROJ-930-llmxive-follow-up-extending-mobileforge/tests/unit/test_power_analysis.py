import json
import os
from pathlib import Path

import pytest

from utils.power_analysis import (
    calculate_required_n,
    write_validated_n,
    _ensure_no_extraction_artifacts,
)
from utils.env_manager import get_project_root


class TestPowerAnalysis:
    def test_calculate_required_n_defaults(self):
        # Using the default parameters should produce a positive integer N
        result = calculate_required_n()
        assert isinstance(result, dict)
        assert "n_required" in result
        assert isinstance(result["n_required"], int)
        assert result["n_required"] > 0
        # Parameters block should be present and contain expected keys
        params = result.get("parameters", {})
        assert params.get("power_target") == 0.8
        assert params.get("effect_size") == 0.2
        assert params.get("significance_level") == 0.05
        assert params.get("baseline_rate") == 0.5

    def test_write_validated_n_creates_file(self, tmp_path: Path):
        # Prepare a dummy result
        dummy_result = {
            "n_required": 42,
            "parameters": {
                "power_target": 0.8,
                "effect_size": 0.2,
                "significance_level": 0.05,
                "baseline_rate": 0.5,
                "p0_source": "Conservative 0.5 assumption",
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }

        # Write to a temporary location
        output_path = tmp_path / "validated_n.json"
        written_path = write_validated_n(dummy_result, output_path)

        assert written_path == output_path
        assert written_path.exists()
        with open(written_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == dummy_result

    def test_ensure_no_extraction_artifacts_raises_when_processed_exists(self, tmp_path: Path):
        # Simulate a processed directory with a dummy file
        project_root = get_project_root()
        processed_dir = project_root / "data" / "processed"
        # Ensure the directory exists and contains a file
        processed_dir.mkdir(parents=True, exist_ok=True)
        dummy_file = processed_dir / "dummy.txt"
        dummy_file.write_text("placeholder")

        with pytest.raises(RuntimeError, match="Data‑extraction artifacts already exist"):
            _ensure_no_extraction_artifacts()

        # Clean up after test
        dummy_file.unlink()
        # If the directory becomes empty, the function should not raise
        # (but we leave the empty directory as it does not affect the test)
    def test_ensure_no_extraction_artifacts_passes_when_no_artifacts(self, tmp_path: Path):
        # Ensure the processed directory is empty or does not exist
        project_root = get_project_root()
        processed_dir = project_root / "data" / "processed"
        if processed_dir.exists():
            for p in processed_dir.iterdir():
                p.unlink()
        else:
            processed_dir.mkdir(parents=True, exist_ok=True)

        # Should not raise any exception
        _ensure_no_extraction_artifacts()