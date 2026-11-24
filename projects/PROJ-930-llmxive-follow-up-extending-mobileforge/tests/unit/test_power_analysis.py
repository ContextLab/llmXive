import json
from pathlib import Path

import pytest

from utils.power_analysis import calculate_required_n, main, _ensure_no_extraction_artifacts

def test_calculate_required_n_defaults():
    """Ensure the calculation returns a sensible integer and proper parameter block."""
    result = calculate_required_n()
    assert isinstance(result, dict)
    assert "n_required" in result and isinstance(result["n_required"], int)
    assert result["n_required"] >= 1
    params = result["parameters"]
    assert params["power_target"] == 0.8
    assert params["effect_size"] == 0.2
    assert params["significance_level"] == 0.05
    assert params["baseline_rate"] == 0.5
    assert "p0_source" in params

def test_ensure_no_extraction_artifacts_raises_when_processed_exists(tmp_path, monkeypatch):
    """Simulate a non‑empty data/processed directory and verify error is raised."""
    # Create a temporary processed directory with a dummy file.
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    (processed_dir / "dummy.txt").write_text("dummy")
    # Monkeypatch the paths.data function to point to our temp directory.
    monkeypatch.setattr("llmxive_toolkit.paths.data", lambda *parts: processed_dir)
    with pytest.raises(RuntimeError):
        _ensure_no_extraction_artifacts()

def test_main_writes_output(tmp_path, monkeypatch):
    """Run main() and verify that the expected JSON file is created with correct schema keys."""
    # Redirect outputs path to a temporary location.
    output_path = tmp_path / "outputs"
    output_path.mkdir(parents=True)
    monkeypatch.setattr("llmxive_toolkit.paths.outputs", lambda *parts: output_path / Path(*parts))
    # Ensure processed directory is empty.
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    monkeypatch.setattr("llmxive_toolkit.paths.data", lambda *parts: processed_dir)

    # Execute main()
    main()

    # Verify file exists and contains required keys.
    result_file = output_path / "power_analysis.json"
    assert result_file.is_file()
    data = json.loads(result_file.read_text())
    assert "n_required" in data
    assert "parameters" in data
    assert "timestamp" in data
    # Simple schema sanity check
    assert isinstance(data["n_required"], int) and data["n_required"] >= 1
    for key in ("power_target", "effect_size", "significance_level", "baseline_rate", "p0_source"):
        assert key in data["parameters"]