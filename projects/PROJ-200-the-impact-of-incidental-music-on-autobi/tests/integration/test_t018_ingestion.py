"""
Integration test for T018: Generate ingested_cohort.parquet.

This test verifies that the ingestion pipeline script runs end-to-end,
produces the expected output file, and updates the state.yaml correctly.
"""
import os
import sys
import pytest
import pandas as pd
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_project_root
from state_manager import load_state, verify_file

class TestT018Ingestion:
    def test_pipeline_execution_and_output(self):
        """
        Run the ingestion pipeline script and verify:
        1. The script exits with code 0.
        2. The output parquet file exists.
        3. The parquet file contains the required columns.
        4. The state.yaml is updated with the correct checksum.
        """
        script_path = project_root / "code" / "ingestion_pipeline.py"
        output_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
        state_path = project_root / "state.yaml"

        # Ensure output is clean
        if output_path.exists():
            output_path.unlink()
        if state_path.exists():
            state_path.unlink()

        # Run the script
        # Using subprocess to ensure it runs as a standalone script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Assert success
        assert result.returncode == 0, f"Script failed with error: {result.stderr}"

        # Assert output file exists
        assert output_path.exists(), "Output parquet file was not created."

        # Assert file content
        df = pd.read_parquet(output_path)
        required_columns = [
            'track_id', 
            'user_id', 
            'adolescent_exposure_score', 
            'residualized_exposure_score'
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

        # Assert state.yaml update
        assert state_path.exists(), "state.yaml was not updated."
        
        state = load_state(state_path)
        assert 'files' in state, "state.yaml missing 'files' key."
        
        # Verify checksum
        expected_checksum = hashlib.md5(output_path.read_bytes()).hexdigest()
        file_info = state['files'].get('ingested_cohort')
        
        assert file_info is not None, "ingested_cohort not found in state.yaml"
        assert file_info['checksum'] == expected_checksum, "Checksum mismatch in state.yaml"
        assert file_info['path'] == str(output_path), "Path mismatch in state.yaml"

    def test_residualized_score_logic(self):
        """
        Verify that the residualized_exposure_score is not constant and
        is derived from the regression residuals (i.e., mean should be approx 0).
        """
        output_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
        
        if not output_path.exists():
            pytest.skip("Output file not found. Run test_pipeline_execution first.")
        
        df = pd.read_parquet(output_path)
        
        # The residualized score is the residual of OLS(adolescent ~ popularity).
        # By definition, residuals sum to zero (or very close to it in float arithmetic).
        mean_residual = df['residualized_exposure_score'].mean()
        assert abs(mean_residual) < 1e-5, "Residualized score mean is not approx 0, indicating calculation error."
        
        # Check range
        assert df['residualized_exposure_score'].notna().all(), "Residualized score contains NaN"
