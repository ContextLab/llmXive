"""
Integration test for associational labeling (T024).
Verifies that all result objects contain the 'association_label' field.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_project_root, get_output_path
from analysis.associational_labeler import (
    apply_labeling_to_all_outputs,
    label_result_object,
    label_list_of_results,
    ASSOCIATION_LABEL
)

@pytest.fixture
def mock_results_dir():
    """Create a temporary directory with mock result files."""
    temp_dir = tempfile.mkdtemp()
    results_subdir = Path(temp_dir) / "results"
    results_subdir.mkdir()
    
    # Create mock LMM summary
    lmm_df = pd.DataFrame({
        "metric": ["fixation_duration", "saccade_amplitude"],
        "valence": ["positive", "negative"],
        "coef": [0.5, -0.3],
        "p_raw": [0.02, 0.15]
    })
    lmm_df.to_csv(results_subdir / "lmm_summary.csv", index=False)
    
    # Create mock correction results
    correction_data = {
        "results": [
            {"metric": "fixation_duration", "valence": "positive", "p_corrected": 0.06},
            {"metric": "saccade_amplitude", "valence": "negative", "p_corrected": 0.45}
        ]
    }
    with open(results_subdir / "correction_results.json", "w") as f:
        json.dump(correction_data, f)
    
    # Create mock sensitivity analysis
    sensitivity_data = [
        {"threshold": 0.01, "significant_count": 1},
        {"threshold": 0.05, "significant_count": 2}
    ]
    with open(results_subdir / "sensitivity_analysis.json", "w") as f:
        json.dump(sensitivity_data, f)
    
    # Create a dummy manifest to avoid overwrite issues in real run if needed, 
    # but here we just set up the inputs.
    
    return results_subdir

def test_label_result_object():
    """Test that a single dict gets the label."""
    data = {"metric": "test", "value": 1.0}
    labeled = label_result_object(data)
    assert labeled["association_label"] == ASSOCIATION_LABEL
    assert labeled["metric"] == "test"

def test_label_list_of_results():
    """Test that a list of dicts gets labeled."""
    data = [{"id": 1}, {"id": 2}]
    labeled = label_list_of_results(data)
    assert all(item.get("association_label") == ASSOCIATION_LABEL for item in labeled)

def test_apply_labeling_to_mock_files(mock_results_dir):
    """Test the full pipeline on mock files."""
    # Temporarily override the output path for the test
    original_get_output_path = get_output_path
    
    # We need to mock the get_output_path function to return our temp dir
    # Since get_output_path is imported in the module, we patch it
    import analysis.associational_labeler as labeler_module
    
    # Mock the function
    def mock_get_output_path():
        return mock_results_dir.parent
    
    # Patch
    original_func = labeler_module.get_output_path
    labeler_module.get_output_path = mock_get_output_path
    
    try:
        apply_labeling_to_all_outputs()
        
        # Check LMM Summary
        lmm_path = mock_results_dir / "lmm_summary.csv"
        df = pd.read_csv(lmm_path)
        assert "association_label" in df.columns
        assert all(df["association_label"] == ASSOCIATION_LABEL)
        
        # Check Correction Results
        corr_path = mock_results_dir / "correction_results.json"
        with open(corr_path, "r") as f:
            corr_data = json.load(f)
        # The structure is {"results": [...]}
        assert "results" in corr_data
        for item in corr_data["results"]:
            assert item["association_label"] == ASSOCIATION_LABEL
        
        # Check Sensitivity Analysis
        sens_path = mock_results_dir / "sensitivity_analysis.json"
        with open(sens_path, "r") as f:
            sens_data = json.load(f)
        for item in sens_data:
            assert item["association_label"] == ASSOCIATION_LABEL
            
        # Check Manifest
        manifest_path = mock_results_dir / "associational_labeling_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        assert manifest["status"] == "completed"
        assert manifest["label_value"] == ASSOCIATION_LABEL
        
    finally:
        # Restore original function
        labeler_module.get_output_path = original_func
        # Cleanup
        shutil.rmtree(mock_results_dir.parent)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])