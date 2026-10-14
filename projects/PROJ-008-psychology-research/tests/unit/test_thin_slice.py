import json
import os
from pathlib import Path

import pytest

# Import the thin_slice module directly
from code.data.thin_slice import main, find_study_with_results

def test_thin_slice_runs_and_produces_output(tmp_path, monkeypatch):
    """
    Run the thin‑slice pipeline and verify that a JSON result file is created
    with the expected keys. The test uses the real API; if the API is
    unreachable the test will fail loudly – this is intentional because the
    task requires real data, not a synthetic fallback.
    """
    # Monkey‑patch the output location to a temporary directory
    output_dir = tmp_path / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Patch the llmxive_toolkit.paths.data function to point to our temp dir
    from llmxive_toolkit import paths as original_paths

    class PatchedPaths:
        @staticmethod
        def data(*parts):
            # Return a Path inside the temporary directory
            return output_dir.joinpath(*parts)

    monkeypatch.setattr("llmxive_toolkit.paths", PatchedPaths, raising=False)

    # Run the pipeline
    main()

    # Verify that the output file exists
    result_file = output_dir / "thin_slice_result.json"
    assert result_file.is_file(), "thin_slice_result.json was not created"

    # Load and verify contents
    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    required_keys = {
        "study_id", "hedges_g", "se", "ci_lower", "ci_upper",
        "n_treatment", "n_control", "mean_treatment", "mean_control",
        "sd_treatment", "sd_control"
    }
    assert required_keys.issubset(result.keys()), f"Missing keys in result: {required_keys - result.keys()}"

    # Basic sanity checks on numeric values
    assert isinstance(result["hedges_g"], float)
    assert result["n_treatment"] > 0
    assert result["n_control"] > 0
    assert result["sd_treatment"] > 0
    assert result["sd_control"] > 0

def test_find_study_returns_dict():
    """
    Ensure that the helper returns a dictionary (i.e. it found a study).
    This test will also raise an error if the external API cannot be
    reached, which satisfies the “no fabrication” requirement.
    """
    result = find_study_with_results()
    assert isinstance(result, dict)
    assert "study_id" in result
    assert "hedges_g" in result