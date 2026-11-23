import os
import tempfile
import pandas as pd
import pytest
import subprocess
import sys
from pathlib import Path

def test_fdr_overlap_analysis_script():
    """
    Test that code/07b_fdr_overlap_analysis.R runs successfully and produces
    the expected output file with valid data.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        results_dir.mkdir()
        
        # Create a mock GLS results file
        # We need enough rows to generate top-20 lists for each threshold
        mock_data = []
        for i in range(50):
            # Ensure we have varying q_values to filter correctly
            q_val = 0.001 * (i + 1)  # 0.001, 0.002, ... 0.05
            if q_val > 0.15: q_val = 0.15
            
            mock_data.append({
                "cre_id": f"CRE_{i:03d}",
                "beta1": float(i),
                "q_value": q_val
            })
        
        df_mock = pd.DataFrame(mock_data)
        input_file = results_dir / "gls_results.csv"
        df_mock.to_csv(input_file, index=False)
        
        # Prepare the R script path
        # We assume the script is in the project root relative to this test
        # In a real run, the script is at code/07b_fdr_overlap_analysis.R
        script_path = Path(__file__).parent.parent.parent / "code" / "07b_fdr_overlap_analysis.R"
        
        if not script_path.exists():
            pytest.skip("R script not found, skipping test (expected in CI)")
        
        # Copy the mock data to the expected location relative to the script
        # Or modify the script to accept args? No, spec implies fixed paths.
        # We will temporarily copy the mock file to the project's results/ 
        # But since we are in a temp dir, we need to run the script in a way that finds the file.
        # The simplest way for a unit test of a script with fixed paths is to:
        # 1. Create the file in the actual expected location if possible, or
        # 2. Mock the filesystem, or
        # 3. Run the script in the temp dir if we copy the script there.
        
        # Approach: Copy script to temp dir, update paths if needed, or just run it 
        # assuming the test runner sets up the environment.
        # For this specific test, we will assume the `results/` directory is relative to cwd.
        # We need to run the script from the temp dir's parent or similar?
        # Let's just run the script from the temp dir if we copy the script there.
        
        temp_script = Path(tmpdir) / "07b_fdr_overlap_analysis.R"
        temp_script.write_text(script_path.read_text())
        
        # The script expects "results/gls_results.csv" relative to CWD.
        # We will change CWD to tmpdir.
        
        try:
            result = subprocess.run(
                ["Rscript", str(temp_script)],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            # Check for success
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            
            # Check output file exists
            output_file = Path(tmpdir) / "results" / "fdr_overlap_stats.csv"
            assert output_file.exists(), "Output file not created"
            
            # Check content
            df_out = pd.read_csv(output_file)
            assert not df_out.empty, "Output file is empty"
            
            # Check required columns
            required_cols = ["threshold_1", "threshold_2", "overlap_percentage"]
            for col in required_cols:
                assert col in df_out.columns, f"Missing column: {col}"
                
            # Check logic: overlap should be between 0 and 100
            assert (df_out["overlap_percentage"] >= 0).all()
            assert (df_out["overlap_percentage"] <= 100).all()
            
        except FileNotFoundError:
            pytest.skip("Rscript not found in PATH")