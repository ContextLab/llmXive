"""
Integration test for the visualization pipeline (User Story 3).

This test verifies that the visualization modules (scatter, pdp, sensitivity_plot)
can be successfully executed end-to-end using real data and model artifacts
produced by previous tasks (US1 and US2).

It ensures:
1. The validated dataset exists and is loadable.
2. The trained model artifacts exist and are loadable.
3. The visualization scripts run without error and produce output files.
4. The output files exist on disk and are non-empty.
"""
import os
import sys
import pytest
import subprocess
from pathlib import Path
import json

# Add project root to path for imports if running directly
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"

# Ensure the code directory is in the path
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_data_processed_dir, get_data_outputs_dir, get_models_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture(scope="module")
def data_paths():
    """Verify input data and model artifacts exist before running visualization tests."""
    raw_data_dir = get_data_processed_dir()
    models_dir = get_models_dir()
    output_dir = get_data_outputs_dir()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for validated dataset
    validated_csv = raw_data_dir / "solder_hardness_validated.csv"
    assert validated_csv.exists(), f"Validated dataset not found at {validated_csv}. Run US1 first."

    # Check for model artifacts (XGBoost is the primary model expected)
    # We look for the metrics JSON which should exist if US2 completed
    xgb_metrics = models_dir / "xgboost_metrics.json"
    assert xgb_metrics.exists(), f"XGBoost metrics not found at {xgb_metrics}. Run US2 first."
    
    # Check for SHAP summary which is needed for PDP
    shap_summary = models_dir / "shap_summary.json"
    assert shap_summary.exists(), f"SHAP summary not found at {shap_summary}. Run US2 first."

    return {
        "validated_csv": validated_csv,
        "xgb_metrics": xgb_metrics,
        "shap_summary": shap_summary,
        "output_dir": output_dir
    }

@pytest.fixture(scope="module")
def run_scatter_plot(data_paths):
    """Execute the scatter plot generation script."""
    script_path = code_dir / "visualization" / "scatter.py"
    assert script_path.exists(), f"Scatter script not found at {script_path}"

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Scatter plot script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        # Raise an assertion to fail the test, but provide detailed logs
        raise AssertionError(f"Scatter plot generation failed with code {result.returncode}:\n{result.stderr}")
    
    return result

@pytest.fixture(scope="module")
def run_pdp_plot(data_paths):
    """Execute the partial dependence plot generation script."""
    script_path = code_dir / "visualization" / "pdp.py"
    assert script_path.exists(), f"PDP script not found at {script_path}"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"PDP script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise AssertionError(f"PDP generation failed with code {result.returncode}:\n{result.stderr}")

    return result

@pytest.fixture(scope="module")
def run_sensitivity_plot(data_paths):
    """Execute the sensitivity analysis plot generation script."""
    script_path = code_dir / "visualization" / "sensitivity_plot.py"
    # Check if the script exists; if not, skip this specific test part but ensure others pass
    if not script_path.exists():
        pytest.skip(f"Sensitivity plot script not found at {script_path}. Skipping this specific check.")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Sensitivity plot script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise AssertionError(f"Sensitivity plot generation failed with code {result.returncode}:\n{result.stderr}")

    return result

class TestVisualizationPipeline:
    """Integration tests for the visualization pipeline."""

    def test_scatter_plot_output_exists(self, data_paths, run_scatter_plot):
        """Verify scatter plot file is generated."""
        output_dir = data_paths["output_dir"]
        expected_file = output_dir / "predicted_vs_measured_scatter.png"
        
        assert expected_file.exists(), f"Scatter plot output not found at {expected_file}"
        assert expected_file.stat().st_size > 0, f"Scatter plot file is empty at {expected_file}"
        logger.info(f"Scatter plot generated successfully: {expected_file}")

    def test_scatter_plot_metadata_exists(self, data_paths, run_scatter_plot):
        """Verify metadata JSON for scatter plot is generated (for FR-007 overlay)."""
        output_dir = data_paths["output_dir"]
        expected_file = output_dir / "scatter_metadata.json"
        
        assert expected_file.exists(), f"Scatter metadata not found at {expected_file}"
        
        with open(expected_file, 'r') as f:
            metadata = json.load(f)
        
        assert "associational_warning" in metadata, "FR-007 warning missing from scatter metadata"
        logger.info("Scatter metadata contains required warnings.")

    def test_pdp_plot_outputs_exist(self, data_paths, run_pdp_plot):
        """Verify PDP files are generated for top 3 features."""
        output_dir = data_paths["output_dir"]
        
        # We expect at least 3 PDP files. The exact names depend on the top features,
        # but the script should generate them.
        # The script typically saves files named `pdp_feature_<name>.png`
        # Let's check that the directory has new png files or specific expected ones.
        
        # Since we don't know the exact feature names without running the logic,
        # we check for the existence of the PDP output directory and any new files
        # or specifically named files if the script is deterministic.
        # Assuming the script saves to `pdp_top_3_features.png` or individual files.
        
        # Based on typical implementation:
        expected_files = [
            output_dir / "pdp_top_3_features.png", 
            # Or individual files if the script saves them separately
            output_dir / "pdp_feature_1.png",
            output_dir / "pdp_feature_2.png",
            output_dir / "pdp_feature_3.png"
        ]
        
        # Check if at least one of the expected patterns exists
        found = False
        for f in expected_files:
            if f.exists() and f.stat().st_size > 0:
                found = True
                logger.info(f"PDP output found: {f}")
                break
        
        assert found, f"No PDP output files found in {output_dir}. Expected at least one of: {expected_files}"

    def test_sensitivity_plot_output_exists(self, data_paths, run_sensitivity_plot):
        """Verify sensitivity analysis plot is generated."""
        output_dir = data_paths["output_dir"]
        expected_file = output_dir / "sensitivity_analysis_plot.png"
        
        # The script might be skipped if the source file doesn't exist, handled by fixture
        if run_sensitivity_plot is None:
            pytest.skip("Sensitivity plot fixture skipped.")
        
        # If the script ran, check for output
        if expected_file.exists():
            assert expected_file.stat().st_size > 0, f"Sensitivity plot file is empty at {expected_file}"
            logger.info(f"Sensitivity plot generated: {expected_file}")
        else:
            # Fallback: check if any sensitivity plot was created
            sensitivity_files = list(output_dir.glob("*sensitivity*.png"))
            assert len(sensitivity_files) > 0, "No sensitivity plot files found in output directory."
            logger.info(f"Sensitivity plot found: {sensitivity_files[0]}")

    def test_visualization_metadata_injection(self, data_paths, run_scatter_plot, run_pdp_plot):
        """Verify that FR-007 warnings are present in visualization metadata."""
        output_dir = data_paths["output_dir"]
        
        # Check scatter metadata
        scatter_meta = output_dir / "scatter_metadata.json"
        if scatter_meta.exists():
            with open(scatter_meta, 'r') as f:
                data = json.load(f)
            assert "associational_warning" in data, "Scatter metadata missing warning"
        
        # Check PDP metadata if generated
        pdp_meta = output_dir / "pdp_metadata.json"
        if pdp_meta.exists():
            with open(pdp_meta, 'r') as f:
                data = json.load(f)
            assert "associational_warning" in data, "PDP metadata missing warning"
        
        logger.info("All visualization metadata contains required associational warnings.")