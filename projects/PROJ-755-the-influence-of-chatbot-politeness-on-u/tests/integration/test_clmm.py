"""
Integration test for CLMM execution and result schema validation.

This test verifies that:
1. The CLMM fitting script (code/02_fit_clmm.py) executes successfully.
2. The output file `data/processed/clmm_results.csv` is created.
3. The output file adheres to the schema defined in `contracts/output.schema.yaml`.
4. The convergence metrics are present and valid.
"""
import os
import sys
import csv
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd

# Add project root to path to allow imports if needed for setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Import schema validator utilities if available, otherwise define minimal schema check
try:
    from utils.schema_validator import load_schema, validate_dataset_schema
except ImportError:
    # Fallback if utils are not fully integrated yet, we define the expected keys locally
    def load_schema(path: Path) -> Dict[str, Any]:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def validate_dataset_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
        # Minimal validation: check columns exist
        required_columns = schema.get("required_columns", [])
        for col in required_columns:
            if col not in df.columns:
                return False
        return True


class TestCLMMExecution:
    """Integration tests for the CLMM fitting pipeline."""

    @pytest.fixture(scope="class")
    def clmm_output_path(self) -> Path:
        """Returns the expected path for the CLMM results."""
        return PROJECT_ROOT / "data" / "processed" / "clmm_results.csv"

    @pytest.fixture(scope="class")
    def output_schema_path(self) -> Path:
        """Returns the path to the output schema definition."""
        return PROJECT_ROOT / "contracts" / "output.schema.yaml"

    @pytest.fixture(scope="class")
    def run_clmm_script(self, clmm_output_path) -> None:
        """
        Executes the CLMM fitting script.
        Skips if the input data is missing (T023/T024 dependency).
        """
        script_path = PROJECT_ROOT / "code" / "02_fit_clmm.py"
        
        if not script_path.exists():
            pytest.skip("Implementation of 02_fit_clmm.py is missing.")

        # Check for input data (scored_dialogues.parquet)
        input_data = PROJECT_ROOT / "data" / "processed" / "scored_dialogues.parquet"
        if not input_data.exists():
            pytest.skip("Input data 'scored_dialogues.parquet' not found. US1 (T015-T020) must be completed first.")

        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for R model fitting
            )
            
            # If the script failed, we still proceed to check if it created partial output or failed loudly
            # But for a successful integration test, we expect exit code 0
            if result.returncode != 0:
                # If it failed, we check if it's a data issue or code issue
                # For the purpose of this test, we assume the code is correct if the input exists
                # and the script crashes, the test fails.
                pytest.fail(f"CLMM script execution failed.\nStdout: {result.stdout}\nStderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            pytest.fail("CLMM script execution timed out.")
        except Exception as e:
            pytest.fail(f"Error running CLMM script: {e}")

    def test_output_file_exists(self, clmm_output_path):
        """Verifies that the output CSV file is created."""
        assert clmm_output_path.exists(), f"Output file {clmm_output_path} was not created."

    def test_output_schema_validation(self, clmm_output_path, output_schema_path):
        """Validates the structure of the output CSV against the schema."""
        assert output_schema_path.exists(), "Schema file missing."
        
        # Load schema
        schema = load_schema(output_schema_path)
        
        # Load data
        try:
            df = pd.read_csv(clmm_output_path)
        except Exception as e:
            pytest.fail(f"Failed to read output CSV: {e}")

        # Validate columns
        required_columns = schema.get("required_columns", [])
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        assert not missing_columns, f"Missing required columns in output: {missing_columns}"
        
        # Additional schema checks if defined in YAML (e.g., types)
        # For now, we ensure the critical fields for US2 are present
        critical_fields = [
            "effect", "estimate", "std_error", "p_value", 
            "p_value_bh", "converged", "convergence_rate"
        ]
        
        for field in critical_fields:
            assert field in df.columns, f"Critical field '{field}' missing from output."

    def test_convergence_metrics(self, clmm_output_path):
        """Verifies that convergence metrics are present and valid."""
        df = pd.read_csv(clmm_output_path)
        
        # Check that convergence_rate exists and is a valid number
        assert "convergence_rate" in df.columns, "convergence_rate column missing."
        
        # If the file has rows, check the rate is between 0 and 1
        if not df.empty:
            rate = df["convergence_rate"].iloc[0]
            assert isinstance(rate, (int, float)), "convergence_rate must be numeric."
            assert 0.0 <= rate <= 1.0, f"convergence_rate {rate} is out of bounds [0, 1]."

    def test_result_content_validity(self, clmm_output_path):
        """Ensures the results contain plausible statistical values."""
        df = pd.read_csv(clmm_output_path)
        
        if df.empty:
            pytest.skip("Output file is empty (no fixed effects found).")

        # Check for at least one fixed effect row
        assert len(df) > 0, "Result dataframe is empty."

        # Verify p-values are within [0, 1]
        if "p_value" in df.columns:
            assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1).all(), "p-values out of range."
        
        if "p_value_bh" in df.columns:
            assert (df["p_value_bh"] >= 0).all() and (df["p_value_bh"] <= 1).all(), "BH-corrected p-values out of range."

        # Verify estimates are numeric
        if "estimate" in df.columns:
            assert pd.to_numeric(df["estimate"], errors='raise').notna().all(), "Non-numeric estimates found."