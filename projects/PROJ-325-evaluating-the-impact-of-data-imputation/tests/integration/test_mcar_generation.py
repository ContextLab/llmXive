import os
import json
import subprocess
import sys
import tempfile
import pytest

def test_cli_mcar_generation():
    """
    Integration test: Run the CLI to generate MCAR data and verify outputs.
    """
    # Create a temporary directory for outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "synthetic_mcar_v1.csv")
        meta_path = os.path.join(tmpdir, "synthetic_mcar_v1_meta.json")

        cmd = [
            sys.executable,
            "code/data/synthetic.py",
            "--generate",
            "--validate-schema",
            "--mechanism", "MCAR",
            "--n-rows", "500",
            "--true-mean", "100",
            "--true-variance", "250",
            "--missing-rate", "0.15",
            "--seed", "42",
            "--output-csv", csv_path,
            "--output-meta", meta_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check exit code
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"

        # Verify CSV exists
        assert os.path.exists(csv_path), "CSV output file not found"

        # Verify Meta exists
        assert os.path.exists(meta_path), "Meta output file not found"

        # Verify content
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert len(df) == 500
        assert 'value' in df.columns
        assert 'missing' in df.columns

        with open(meta_path, 'r') as f:
            meta = json.load(f)

        assert meta['mechanism'] == 'MCAR' or meta['missingness_mechanism'] == 'MCAR'
        assert meta['true_mean'] == 100
        assert meta['true_variance'] == 250
        # Check observed rate is close to 0.15
        assert abs(meta['missing_rate'] - 0.15) < 0.05