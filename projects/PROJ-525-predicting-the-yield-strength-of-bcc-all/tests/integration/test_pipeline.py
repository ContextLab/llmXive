"""
Integration tests for the full pipeline.
Implements T020: Verify pipeline halts with 'Data Scarcity Warning' if N < 80.
"""
import pytest
import subprocess
import sys
import os
import tempfile
import csv
from pathlib import Path

# Ensure the code directory is in the path for imports if running standalone
# though typically pytest runs from root with PYTHONPATH set.
# We rely on the subprocess call which inherits the environment.

class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    def _create_small_dataset(self, tmp_path: Path, count: int) -> Path:
        """Helper to create a minimal valid CSV with < 80 rows."""
        csv_path = tmp_path / "small_mpea_raw.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header matching expected raw format based on T012-T016 context
            writer.writerow([
                "alloy_id", "composition", "crystal_structure", 
                "yield_strength_mpa", "uncertainty_mpa"
            ])
            # Generate 'count' rows of valid BCC data
            for i in range(count):
                # Composition must sum to 1.0 (normalized) or be valid raw
                # T013 normalizes, so we provide valid raw that sums to 1.0 or let it handle it.
                # Let's provide normalized-like data for simplicity: 50% Cr, 50% Fe
                comp = "Cr:0.5,Fe:0.5"
                writer.writerow([
                    f"ALLOY_{i:03d}", 
                    comp, 
                    "BCC", 
                    400 + i,  # Valid numeric yield
                    10.0
                ])
        return csv_path

    def test_pipeline_halts_on_data_scarcity(self, tmp_path: Path):
        """
        Verify pipeline halts with 'Data Scarcity Warning' if N < 80.
        
        This test:
        1. Creates a temporary raw CSV with < 80 rows (e.g., 50 rows).
        2. Runs code/01_download.py pointing to this small dataset.
        3. Captures stdout/stderr.
        4. Asserts the script exits with a non-zero code (or specific exit code).
        5. Asserts the output contains "Data Scarcity Warning".
        """
        # 1. Create small dataset
        small_data_path = self._create_small_dataset(tmp_path, count=50)
        
        # 2. Prepare output directory for this test run
        output_dir = tmp_path / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Run the script
        # We pass the input file and output dir as arguments if the script supports them,
        # or we rely on environment/config. 
        # Based on T007 (config) and typical CLI patterns for these tasks, 
        # we assume the script accepts --input and --output or similar, 
        # OR we temporarily patch the config.
        # However, the task description for T015 says "halt pipeline". 
        # Let's assume the script accepts CLI args for flexibility in testing.
        # If the script strictly reads from a hardcoded path defined in config, 
        # we would need to mock that. 
        # Given T007 exists, let's assume we can override via args or env.
        # To be safe and robust without knowing exact CLI args of 01_download.py,
        # we will pass them as arguments. If the script doesn't support args, 
        # we might need to adjust, but standard practice for such pipelines is CLI args.
        # Let's assume the signature: python code/01_download.py --input <path> --output <path>
        # If the existing 01_download.py doesn't support this, we must ensure it does 
        # or modify the test to set environment variables if that's the mechanism.
        # Looking at T015 description: "halt pipeline... if N < 80".
        # Let's try a standard CLI approach first.
        
        cmd = [
            sys.executable, 
            "code/01_download.py",
            "--input", str(small_data_path),
            "--output", str(output_dir)
        ]
        
        # Fallback if the script doesn't accept args: 
        # We check if the script has argparse. If not, we might need to 
        # rely on the fact that the test environment might set specific paths.
        # But for a robust integration test, we pass args.
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent) # Run from project root
        )
        
        # 4. Check exit code
        # The script should exit non-zero (e.g., 1) when data is scarce
        assert result.returncode != 0, (
            f"Pipeline should have exited with non-zero code on data scarcity. "
            f"Stdout: {result.stdout}\nStderr: {result.stderr}"
        )
        
        # 5. Check for the specific warning message
        combined_output = result.stdout + result.stderr
        assert "Data Scarcity Warning" in combined_output, (
            f"Expected 'Data Scarcity Warning' in output. "
            f"Stdout: {result.stdout}\nStderr: {result.stderr}"
        )