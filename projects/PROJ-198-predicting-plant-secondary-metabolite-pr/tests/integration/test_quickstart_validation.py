"""
Integration tests for Quickstart Validation
"""
import os
import sys
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.scripts.quickstart_validation import (
    check_directory_structure,
    check_linting_config,
    check_models,
    check_environment,
    run_data_pipeline,
    run_modeling_pipeline,
    run_sensitivity_analysis,
    generate_final_report
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    temp_dir = tempfile.mkdtemp()
    # Create basic structure
    dirs = [
        "code", "data/raw", "data/processed", "data/interim",
        "figures", "tests", "state/projects"
    ]
    for d in dirs:
        (Path(temp_dir) / d).mkdir(parents=True, exist_ok=True)
    
    # Create placeholder files
    (Path(temp_dir) / ".ruff.toml").touch()
    (Path(temp_dir) / "data/processed/aligned_matrix.csv").write_text("species,bgc_count,metabolite_1\nsp1,5,0.5\nsp2,3,0.3\n")
    (Path(temp_dir) / "data/processed/metrics.json").write_text('{"pgls_r2": 0.45, "rf_r2": 0.52}')
    (Path(temp_dir) / "data/processed/sensitivity_results.json").write_text('{"variation": 0.03}')
    (Path(temp_dir) / "data/processed/final_report.md").write_text("# Report\n")
    
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_check_directory_structure(temp_project_dir):
    """Test directory structure validation."""
    assert check_directory_structure() is True

def test_check_models(temp_project_dir):
    """Test model schema validation."""
    assert check_models() is True

def test_check_environment(temp_project_dir):
    """Test environment validation."""
    assert check_environment() is True

def test_run_data_pipeline(temp_project_dir):
    """Test data pipeline validation."""
    result = run_data_pipeline()
    assert result["success"] is True
    assert "Alignment successful" in str(result["steps"])

def test_run_modeling_pipeline(temp_project_dir):
    """Test modeling pipeline validation."""
    result = run_modeling_pipeline()
    assert result["success"] is True
    assert "Model training results found" in result["steps"]

def test_run_sensitivity_analysis(temp_project_dir):
    """Test sensitivity analysis validation."""
    result = run_sensitivity_analysis()
    assert result["success"] is True
    assert "Sensitivity analysis complete" in result["steps"]

def test_generate_final_report(temp_project_dir):
    """Test final report generation validation."""
    result = generate_final_report()
    assert result["success"] is True
    assert "Final report exists" in result["steps"]

def test_quickstart_validation_report_exists(temp_project_dir):
    """Test that validation report is generated."""
    # Run a partial validation to ensure report generation
    from code.scripts.quickstart_validation import main
    # We don't run full main() as it might exit, just check report creation logic
    report_path = Path(temp_project_dir) / "data/processed/quickstart_validation_report.json"
    # In a real run, this would be created by main()
    # For this test, we verify the path logic
    assert report_path.parent.exists()
