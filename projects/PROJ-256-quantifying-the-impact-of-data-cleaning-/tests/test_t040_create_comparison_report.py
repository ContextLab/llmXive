import json
from pathlib import Path

import pytest

from t040_create_comparison_report import _build_report, main


@pytest.fixture
def dummy_metrics(tmp_path: Path):
    """Create minimal baseline and cleaned metric JSON files."""
    baseline = {"p_value": 0.04, "effect_size": 0.5}
    cleaned = {"p_value": 0.06, "effect_size": 0.45}
    baseline_path = tmp_path / "baseline.json"
    cleaned_path = tmp_path / "cleaned.json"
    baseline_path.write_text(json.dumps(baseline))
    cleaned_path.write_text(json.dumps(cleaned))
    return baseline_path, cleaned_path


def test_build_report_structure(dummy_metrics):
    baseline_path, cleaned_path = dummy_metrics
    report = _build_report(baseline_path, cleaned_path)

    # Basic schema checks
    assert "baseline_metrics" in report
    assert "cleaned_metrics" in report
    assert "absolute_diff" in report
    assert "relative_diff" in report
    assert "sensitivity_analysis" in report

    # Verify that absolute/relative diffs contain expected keys
    assert "p_value" in report["absolute_diff"]
    assert "p_value" in report["relative_diff"]


def test_main_writes_file(tmp_path: Path, monkeypatch):
    # Prepare dummy config via monkeypatching get_config()
    from config import Config

    dummy_cfg = Config()
    dummy_cfg._data = {
        "BASELINE_METRICS_PATH": str(tmp_path / "baseline.json"),
        "CLEANED_METRICS_PATH": str(tmp_path / "cleaned.json"),
        "COMPARISON_REPORT_PATH": str(tmp_path / "comparison_report.json"),
    }

    monkeypatch.setattr("config.get_config", lambda: dummy_cfg)

    # Write dummy metric files
    (tmp_path / "baseline.json").write_text(json.dumps({"p_value": 0.03}))
    (tmp_path / "cleaned.json").write_text(json.dumps({"p_value": 0.07}))

    # Run the script
    main()

    out_file = tmp_path / "comparison_report.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["baseline_metrics"]["p_value"] == 0.03
    assert data["cleaned_metrics"]["p_value"] == 0.07


if __name__ == "__main__":
    pytest.main([__file__])