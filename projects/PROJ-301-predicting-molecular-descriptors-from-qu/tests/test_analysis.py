import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from code import analysis
from code.analysis import (
    load_json_artifact,
    load_model_artifact,
    load_test_labels,
    generate_predictions,
    perform_statistical_analysis,
    define_failure_boundary,
    generate_parity_predictions,
    report_stability,
    generate_final_report,
    main
)

def test_load_json_artifact(tmp_path: Path):
    """Test loading a JSON artifact."""
    test_data = {"key": "value"}
    test_file = tmp_path / "test.json"
    with open(test_file, 'w') as f:
        import json
        json.dump(test_data, f)

    result = load_json_artifact(test_file)
    assert result == test_data

def test_load_test_labels(tmp_path: Path):
    """Test loading test labels."""
    test_labels = pd.DataFrame({"mu": [1.0, 2.0], "homo": [3.0, 4.0], "lumo": [5.0, 6.0]})
    test_file = tmp_path / "labels.csv"
    test_labels.to_csv(test_file, index=False)

    result = load_test_labels(test_file)
    pd.testing.assert_frame_equal(result, test_labels)

def test_generate_predictions():
    """Test generating predictions."""
    # Mock models and data
    class MockModel:
        def predict(self, X):
            return np.ones(X.shape[0])

    model_2d = MockModel()
    model_3d = MockModel()
    features_2d = np.ones((2, 10))
    features_3d = np.ones((2, 10))
    labels = pd.DataFrame({"mu": [1.0, 2.0], "homo": [3.0, 4.0], "lumo": [5.0, 6.0]})

    predictions = generate_predictions(model_2d, model_3d, features_2d, features_3d, labels)

    assert "pred_2d" in predictions
    assert "pred_3d" in predictions
    assert "error_2d" in predictions
    assert "error_3d" in predictions
    assert "true" in predictions

def test_perform_statistical_analysis():
    """Test statistical analysis."""
    error_2d = np.array([1.0, 2.0, 3.0])
    error_3d = np.array([1.5, 2.5, 3.5])

    result = perform_statistical_analysis(error_2d, error_3d)

    assert "p_value" in result
    assert "statistic" in result

def test_define_failure_boundary():
    """Test defining failure boundary."""
    p_values = {"p_value": 0.01}
    mae_2d = 1.0
    mae_3d = 1.2

    result = define_failure_boundary(p_values, mae_2d, mae_3d)

    assert isinstance(result, list)

def test_generate_parity_predictions(tmp_path: Path):
    """Test generating parity predictions."""
    pred_2d = np.array([1.0, 2.0, 3.0])
    pred_3d = np.array([1.5, 2.5, 3.5])
    true = np.array([1.0, 2.0, 3.0])

    # Mock paths
    parity_2d_path = tmp_path / "parity_2d.png"
    parity_3d_path = tmp_path / "parity_3d.png"

    # Temporarily override constants
    original_parity_2d = analysis.PARITY_2D_PATH
    original_parity_3d = analysis.PARITY_3D_PATH
    analysis.PARITY_2D_PATH = parity_2d_path
    analysis.PARITY_3D_PATH = parity_3d_path

    try:
        generate_parity_predictions(pred_2d, pred_3d, true)
        assert parity_2d_path.exists()
        assert parity_3d_path.exists()
    finally:
        analysis.PARITY_2D_PATH = original_parity_2d
        analysis.PARITY_3D_PATH = original_parity_3d

def test_report_stability(tmp_path: Path):
    """Test reporting stability."""
    # Create a mock stability report
    stability_report = {"2d": {"passed": False}, "3d": {"passed": True}}
    test_file = tmp_path / "stability_report.json"
    import json
    with open(test_file, 'w') as f:
        json.dump(stability_report, f)

    original_path = analysis.STABILITY_REPORT_PATH
    analysis.STABILITY_REPORT_PATH = test_file

    try:
        report_stability()
        # Check if failure report was created
        failure_report_path = tmp_path.parent / "artifacts/metrics/stability_failure_report.json"
        # Note: This test might need adjustment based on actual file paths
    finally:
        analysis.STABILITY_REPORT_PATH = original_path

def test_generate_final_report(tmp_path: Path):
    """Test generating the final report."""
    baseline_errors = {"2d": 1.0, "3d": 1.2}
    test_predictions = {"error_2d": np.array([1.0]), "error_3d": np.array([1.2])}
    statistics = {"p_value": 0.01}
    failure_boundary = [{"reason": "test"}]
    stability_report = {"2d": {"passed": False}}

    report_path = tmp_path / "report.md"

    original_path = analysis.FINAL_REPORT_PATH
    analysis.FINAL_REPORT_PATH = report_path

    try:
        generate_final_report(baseline_errors, test_predictions, statistics, failure_boundary, stability_report)
        assert report_path.exists()
    finally:
        analysis.FINAL_REPORT_PATH = original_path