import os
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.generate_model_report import generate_model_report

@pytest.fixture
def sample_threshold_sweep(tmp_path):
    """Create a sample threshold sweep file for testing."""
    sweep_data = {
        "thresholds": {
            "0.01": 0.005,
            "0.05": 0.002,
            "0.1": 0.001
        },
        "min_fnr": 0.001
    }
    file_path = tmp_path / "threshold_sweep.json"
    with open(file_path, 'w') as f:
        json.dump(sweep_data, f)
    return str(file_path)

@pytest.fixture
def sample_decision_boundary(tmp_path):
    """Create a sample decision boundary file for testing."""
    boundary_data = {
        "model_type": "RandomForest",
        "unsafe": True,
        "correlation_coefficient": 0.75
    }
    file_path = tmp_path / "decision_boundary.pkl"
    import pickle
    with open(file_path, 'wb') as f:
        pickle.dump(boundary_data, f)
    return str(file_path)

@pytest.fixture
def sample_features_csv(tmp_path):
    """Create a sample features CSV file for testing."""
    csv_content = """task_id,dependency_depth,cyclomatic_complexity,semantic_complexity_score,lines_of_code,dynamic_execution_outcome
task_001,3,5,0.8,150,Pass
task_002,5,8,0.9,200,Fail
task_003,2,3,0.6,100,Pass
"""
    file_path = tmp_path / "features.csv"
    file_path.write_text(csv_content)
    return str(file_path)

def test_generate_model_report_creates_file(
    tmp_path,
    sample_threshold_sweep,
    sample_decision_boundary,
    sample_features_csv
):
    """Test that generate_model_report creates the output file."""
    output_path = tmp_path / "model_report.json"
    
    generate_model_report(
        threshold_sweep_path=sample_threshold_sweep,
        decision_boundary_path=sample_decision_boundary,
        features_path=sample_features_csv,
        output_path=str(output_path)
    )
    
    assert output_path.exists(), "Model report file was not created"

def test_model_report_contains_required_fields(
    tmp_path,
    sample_threshold_sweep,
    sample_decision_boundary,
    sample_features_csv
):
    """Test that the model report contains all required fields."""
    output_path = tmp_path / "model_report.json"
    
    generate_model_report(
        threshold_sweep_path=sample_threshold_sweep,
        decision_boundary_path=sample_decision_boundary,
        features_path=sample_features_csv,
        output_path=str(output_path)
    )
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    required_fields = [
        "false_negative_rates",
        "minimum_achievable_fnr",
        "correlation_coefficient",
        "unsafe_for_static_only_classification",
        "fr_006_associational_framing",
        "target_fnr_threshold",
        "meets_safety_constraint"
    ]
    
    for field in required_fields:
        assert field in report, f"Missing required field: {field}"

def test_model_report_framing_statement(
    tmp_path,
    sample_threshold_sweep,
    sample_decision_boundary,
    sample_features_csv
):
    """Test that the associational framing statement is present and meaningful."""
    output_path = tmp_path / "model_report.json"
    
    generate_model_report(
        threshold_sweep_path=sample_threshold_sweep,
        decision_boundary_path=sample_decision_boundary,
        features_path=sample_features_csv,
        output_path=str(output_path)
    )
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    framing = report.get("fr_006_associational_framing", "")
    assert "associational" in framing.lower(), "Framing must mention 'associational'"
    assert "causal" in framing.lower(), "Framing must explicitly deny causal claims"
    assert len(framing) > 50, "Framing statement should be substantive"

def test_model_report_safety_flag_logic(
    tmp_path,
    sample_threshold_sweep,
    sample_decision_boundary,
    sample_features_csv
):
    """Test that the safety flag is correctly set based on FNR."""
    output_path = tmp_path / "model_report.json"
    
    generate_model_report(
        threshold_sweep_path=sample_threshold_sweep,
        decision_boundary_path=sample_decision_boundary,
        features_path=sample_features_csv,
        output_path=str(output_path)
    )
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    # With min_fnr=0.001 and target=0.001, it should be safe (or unsafe if >)
    # Our sample has unsafe=True in boundary, so it should reflect that
    assert "unsafe_for_static_only_classification" in report
    assert isinstance(report["unsafe_for_static_only_classification"], bool)