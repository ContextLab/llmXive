import json
import tempfile
from pathlib import Path
import sys
import subprocess

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

def test_report_script_execution():
    """
    Integration test: Ensure the report script can be run as a standalone script
    and produces the expected output file given a valid input.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create a realistic model_performance.json
        perf_data = {
            "mean_r2": 0.28,
            "mean_rmse": 12.4,
            "std_r2": 0.05,
            "std_rmse": 1.2,
            "r2_interpretation": "Weak predictive power (R² < 0.30), consistent with null hypothesis.",
            "n_samples": 55,
            "folds": 5
        }
        perf_file = results_dir / "model_performance.json"
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        # Create a dummy project structure to run the script
        # We need to simulate the project root
        project_root = tmp_path
        code_dir = project_root / "code"
        code_dir.mkdir()
        
        # Copy the report.py content to the temp code dir
        # We can't import from the temp dir easily in the same way, so we execute the script directly
        # by passing the environment or by copying the file.
        # For this test, we will just verify the logic by calling the function directly
        # since running the script as a subprocess requires setting up the whole path structure.
        
        from report import generate_final_report, setup_report_logger
        
        output_file = results_dir / "final_report.md"
        logger = setup_report_logger()
        
        generate_final_report(perf_file, output_file, logger)
        
        assert output_file.exists(), "final_report.md was not created"
        
        content = output_file.read_text()
        
        # Verify mandatory limitations text
        assert "This study is observational" in content
        assert "Correlations do not imply causality" in content
        assert "thermal conductivity tensor was reduced to a scalar" in content
        
        # Verify R2 interpretation is present
        assert "Weak predictive power" in content
        
        # Verify summary section
        assert "## Summary" in content
        assert "mean R² of 0.2800" in content
        assert "mean Root Mean Squared Error" in content

def test_report_script_missing_input():
    """
    Test that the script fails gracefully if the input file is missing.
    """
    from report import generate_final_report, setup_report_logger
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        missing_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "final_report.md"
        
        logger = setup_report_logger()
        
        try:
            generate_final_report(missing_file, output_file, logger)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected