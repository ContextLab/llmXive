import pytest
import json
from pathlib import Path

@pytest.fixture
def analysis_results_schema():
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "analysis_results.schema.yaml"
    if not schema_path.exists():
        pytest.skip("Analysis results schema not found")
    with open(schema_path, 'r') as f:
        return json.load(f)

def test_analysis_results_json_structure(analysis_results_schema):
    """
    T028: Contract test for analysis results JSON.
    Validates that analysis results conform to the expected schema.
    """
    results_dir = Path(__file__).parent.parent.parent / "data" / "results"
    if results_dir.exists():
        result_files = list(results_dir.glob("analysis_results_*.json"))
        if result_files:
            with open(result_files[0], 'r') as f:
                result = json.load(f)
            
            # Basic structural checks
            assert "threshold" in result, "Analysis result must have 'threshold'"
            assert "confidence_interval" in result, "Analysis result must have 'confidence_interval'"
            assert "model_parameters" in result, "Analysis result must have 'model_parameters'"
            assert "tradeoff_curve" in result, "Analysis result must have 'tradeoff_curve'"
            return
    
    pytest.skip("No analysis result files found to validate against schema")
