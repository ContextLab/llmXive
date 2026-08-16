"""
Unit tests for plan update functionality (T026a).

These tests verify that the plan.md file is correctly updated to include
the required artifacts in the "Single Source of Truth" section.
"""
import pytest
import tempfile
import os
from pathlib import Path
import shutil

# Import the function to test
from plan_updater import update_plan

@pytest.fixture
def temp_plan_file():
    """Create a temporary plan.md file for testing."""
    temp_dir = tempfile.mkdtemp()
    plan_path = Path(temp_dir) / "plan.md"
    
    # Create a sample plan.md content
    sample_content = """
    # Implementation Plan

    ## Single Source of Truth

    The following artifacts are the **Single Source of Truth**:

    - `data/evaluation/model_metrics.json`: Contains final R², MAE, RMSE.

    ## Success Criteria

    - SC-001: Dataset contains ≥1000 rows.
    """
    
    plan_path.write_text(sample_content)
    yield plan_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_plan_update_adds_new_artifacts(temp_plan_file):
    """Test that new artifacts are added to the Single Source of Truth section."""
    # Change to the temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(temp_plan_file.parent)
    
    try:
        # Run the update function
        success = update_plan()
        assert success, "Plan update should succeed"
        
        # Read the updated content
        updated_content = temp_plan_file.read_text()
        
        # Check that new artifacts are present
        required_artifacts = [
            "permutation_importance.json",
            "feature_ranking.json",
            "vif_scores.json"
        ]
        
        for artifact in required_artifacts:
            assert artifact in updated_content, f"Artifact {artifact} should be in plan.md"
    
    finally:
        os.chdir(original_cwd)

def test_plan_update_skips_if_already_present(temp_plan_file):
    """Test that update skips if artifacts are already present."""
    # Pre-populate the plan with the required artifacts
    original_content = temp_plan_file.read_text()
    updated_content = original_content + "\n- `data/evaluation/permutation_importance.json`\n"
    updated_content += "- `data/evaluation/feature_ranking.json`\n"
    updated_content += "- `data/evaluation/vif_scores.json`\n"
    temp_plan_file.write_text(updated_content)
    
    original_cwd = os.getcwd()
    os.chdir(temp_plan_file.parent)
    
    try:
        # Run the update function
        success = update_plan()
        assert success, "Plan update should succeed even if artifacts are present"
        
        # Content should remain unchanged
        final_content = temp_plan_file.read_text()
        assert final_content == updated_content, "Content should not change if artifacts are already present"
    
    finally:
        os.chdir(original_cwd)

def test_plan_update_handles_missing_section(temp_plan_file):
    """Test that update handles missing 'Single Source of Truth' section."""
    # Remove the section header
    content_without_section = temp_plan_file.read_text().replace("## Single Source of Truth", "## Other Section")
    temp_plan_file.write_text(content_without_section)
    
    original_cwd = os.getcwd()
    os.chdir(temp_plan_file.parent)
    
    try:
        # Run the update function
        success = update_plan()
        assert success, "Plan update should succeed even if section is missing"
        
        # Check that artifacts were appended
        updated_content = temp_plan_file.read_text()
        assert "permutation_importance.json" in updated_content, "Artifacts should be appended"
    
    finally:
        os.chdir(original_cwd)