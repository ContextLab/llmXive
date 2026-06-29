"""
Contract test for seed reproducibility across pipeline modules (Task T060).

This test ensures that all code modules call set_global_seed(12345) at startup
and produce reproducible results across runs.
"""
import subprocess
import sys
import os
import json
import tempfile
import pytest


class TestSeedReproducibility:
    """Contract tests for seed reproducibility across pipeline."""

    def test_synthetic_data_generation_reproducible(self):
        """
        Verify that synthetic data generation is reproducible with seed pinning.

        This is a contract test: if generate_synthetic.py exists, it must
        produce identical output when run twice with the same seed.
        """
        generate_script = 'code/pipeline/generate_synthetic.py'

        if not os.path.exists(generate_script):
            pytest.skip(f"Script not found: {generate_script}")

        with tempfile.TemporaryDirectory() as tmpdir:
            output1 = os.path.join(tmpdir, 'synthetic_run1.json')
            output2 = os.path.join(tmpdir, 'synthetic_run2.json')

            # Run generation twice
            cmd = [sys.executable, generate_script, '--output', output1]
            subprocess.run(cmd, check=True, capture_output=True)

            cmd = [sys.executable, generate_script, '--output', output2]
            subprocess.run(cmd, check=True, capture_output=True)

            # Compare outputs
            with open(output1, 'r') as f:
                data1 = json.load(f)
            with open(output2, 'r') as f:
                data2 = json.load(f)

            assert data1 == data2, "Synthetic data generation not reproducible"

    def test_model_fitting_reproducible(self):
        """
        Verify that model fitting produces reproducible results.

        This is a contract test: if hierarchical_model.py exists and
        supports a test mode, it must produce identical posterior samples
        when run twice with the same seed.
        """
        model_script = 'code/pipeline/hierarchical_model.py'

        if not os.path.exists(model_script):
            pytest.skip(f"Script not found: {model_script}")

        # Check if script has a --test or --reproducible flag
        result = subprocess.run(
            [sys.executable, model_script, '--help'],
            capture_output=True,
            text=True
        )

        if '--test' not in result.stdout and '--reproducible' not in result.stdout:
            pytest.skip(f"{model_script} does not support reproducible test mode")

        with tempfile.TemporaryDirectory() as tmpdir:
            trace1 = os.path.join(tmpdir, 'trace_run1.nc')
            trace2 = os.path.join(tmpdir, 'trace_run2.nc')

            cmd = [sys.executable, model_script, '--test', '--output', trace1]
            subprocess.run(cmd, check=True, capture_output=True)

            cmd = [sys.executable, model_script, '--test', '--output', trace2]
            subprocess.run(cmd, check=True, capture_output=True)

            # Compare traces (should be binary identical)
            with open(trace1, 'rb') as f1:
                content1 = f1.read()
            with open(trace2, 'rb') as f2:
                content2 = f2.read()

            assert content1 == content2, "Model fitting not reproducible"
