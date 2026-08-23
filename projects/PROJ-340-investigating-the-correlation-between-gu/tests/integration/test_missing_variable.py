"""
Integration test for missing variable error handling.

This test verifies that the pipeline halts with a specific error when a required
variable (e.g., "SWS duration") is missing from the input data.

Depends on T107 (generate_synthetic_data.py) to create the test dataset.
"""
import os
import sys
import subprocess
import tempfile
import pytest
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

def test_halt_on_missing_sws_duration():
    """
    Test that the pipeline halts with a specific error when "SWS duration" is missing.
    
    Steps:
    1. Generate synthetic data with "SWS duration" missing (using T107 script).
    2. Run the ingestion script against this data.
    3. Assert that the process exits with a SystemExit containing the expected error message.
    """
    # Path to the synthetic data generator
    generator_script = code_dir / "generate_synthetic_data.py"
    ingest_script = code_dir / "ingest.py"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_csv = os.path.join(tmpdir, "test_missing.csv")
        
        # 1. Generate synthetic data with missing "SWS duration"
        gen_cmd = [
            sys.executable, str(generator_script),
            "--output", output_csv,
            "--missing-variable", "sws_duration",
            "--seed", "42"
        ]
        
        result_gen = subprocess.run(gen_cmd, capture_output=True, text=True)
        assert result_gen.returncode == 0, f"Data generation failed: {result_gen.stderr}"
        assert os.path.exists(output_csv), "Generated CSV file not found."
        
        # 2. Run ingestion with the missing variable data
        # We expect this to fail because "sws_duration" is required but missing
        ingest_cmd = [
            sys.executable, str(ingest_script),
            "--input", output_csv,
            "--mode", "real"  # Force real mode to trigger validation
        ]
        
        result_ingest = subprocess.run(ingest_cmd, capture_output=True, text=True)
        
        # 3. Verify the failure
        # The process should exit with non-zero code
        assert result_ingest.returncode != 0, "Pipeline should have halted on missing variable."
        
        # Check for specific error message in stderr or stdout
        output = result_ingest.stderr + result_ingest.stdout
        
        # The error message should contain the missing variable name
        assert "sws_duration" in output.lower(), \
            f"Expected error message to contain 'sws_duration'. Got: {output}"
        
        # Should also contain a halt/fail indication
        assert any(
            term in output.lower() 
            for term in ["halt", "error", "missing", "required"]
        ), f"Expected error indication in output. Got: {output}"

        print("Test passed: Pipeline correctly halted on missing 'sws_duration'.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])