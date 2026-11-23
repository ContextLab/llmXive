"""
Integration test for T025: Generate statistical_results.json

Verifies that the script correctly aggregates statistical test results
into the required JSON artifact structure.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np

# Add parent to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_generate_statistical_results_structure():
    """
    Verify that the generated JSON has the correct schema:
    - metadata object
    - bins array containing test results
    - Each bin result has: frequency, material, ks_stat, ks_pvalue, ks_rejected,
                          chi2_stat, chi2_pvalue, chi2_rejected, fdr_adjusted
    """
    # We need to ensure the dependencies (ingestion -> stats -> generate)
    # are mocked or the data exists. Since we are testing T025 specifically,
    # we assume T021-T024 (stats.py) works correctly and focus on the
    # aggregation logic in generate_statistical_results.py.

    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        artifacts_dir = tmpdir / "artifacts"
        data_dir = tmpdir / "data" / "derived"
        config_dir = tmpdir / "data"

        artifacts_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)

        # Create a minimal config.yaml
        config_path = config_dir / "config.yaml"
        config_path.write_text("""
        materials:
          steel:
            mass: 0.01
            radius: 0.0025
          polymer:
            mass: 0.005
            radius: 0.0025
        frequency_bins:
          - 10
          - 20
          - 30
        """)

        # Create a minimal energy_samples.csv
        # This simulates the output of T017
        csv_path = data_dir / "energy_samples.csv"
        data = {
            "particle_id": [1, 1, 1, 2, 2, 2],
            "timestamp": [1.0, 1.1, 1.2, 1.0, 1.1, 1.2],
            "E_trans": [0.1, 0.12, 0.11, 0.05, 0.06, 0.055],
            "E_rot": [0.01, 0.011, 0.01, 0.005, 0.006, 0.005],
            "E_pot": [0.02, 0.021, 0.02, 0.01, 0.011, 0.01],
            "E_vib": [0.005, 0.005, 0.005, 0.002, 0.002, 0.002],
            "frequency_bin": [10, 10, 10, 20, 20, 20],
            "material": ["steel", "steel", "steel", "polymer", "polymer", "polymer"],
            "pot_incomplete": [False, False, False, False, False, False]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Mock the stats module to return deterministic results
        # to avoid flaky statistical tests on tiny data
        import stats as stats_module
        original_run = stats_module.run_statistical_analysis

        def mock_run_statistical_analysis(input_path, config):
            return [
                {
                    "frequency": 10,
                    "material": "steel",
                    "n_samples": 3,
                    "ks_statistic": 0.15,
                    "ks_pvalue": 0.25,
                    "ks_rejected": False,
                    "chi2_statistic": 2.5,
                    "chi2_pvalue": 0.40,
                    "chi2_rejected": False,
                    "fdr_adjusted_pvalue": 0.25,
                    "fdr_rejected": False
                },
                {
                    "frequency": 20,
                    "material": "polymer",
                    "n_samples": 3,
                    "ks_statistic": 0.80,
                    "ks_pvalue": 0.001,
                    "ks_rejected": True,
                    "chi2_statistic": 15.0,
                    "chi2_pvalue": 0.0001,
                    "chi2_rejected": True,
                    "fdr_adjusted_pvalue": 0.001,
                    "fdr_rejected": True
                }
            ]

        stats_module.run_statistical_analysis = mock_run_statistical_analysis

        try:
            # Import and run the T025 script logic
            # We need to adjust paths dynamically for the test
            import generate_statistical_results as gen_script
            gen_script.OUTPUT_PATH = artifacts_dir / "statistical_results.json"
            gen_script.INPUT_PATH = csv_path
            gen_script.CONFIG_PATH = config_path

            result_code = gen_script.main()
            assert result_code == 0, "Script returned non-zero exit code"

            # Verify the output file exists
            output_file = artifacts_dir / "statistical_results.json"
            assert output_file.exists(), "statistical_results.json was not created"

            # Verify the content structure
            with open(output_file) as f:
                results = json.load(f)

            assert "metadata" in results
            assert "bins" in results
            assert isinstance(results["bins"], list)
            assert len(results["bins"]) == 2

            # Check first bin structure
            bin1 = results["bins"][0]
            assert "frequency" in bin1
            assert "material" in bin1
            assert "ks_statistic" in bin1
            assert "ks_pvalue" in bin1
            assert "ks_rejected" in bin1
            assert "chi2_statistic" in bin1
            assert "chi2_pvalue" in bin1
            assert "chi2_rejected" in bin1
            assert "fdr_adjusted_pvalue" in bin1
            assert "fdr_rejected" in bin1

            # Verify specific values from mock
            assert bin1["frequency"] == 10
            assert bin1["material"] == "steel"
            assert bin1["ks_rejected"] is False

            bin2 = results["bins"][1]
            assert bin2["frequency"] == 20
            assert bin2["material"] == "polymer"
            assert bin2["ks_rejected"] is True

        finally:
            # Restore original function
            stats_module.run_statistical_analysis = original_run

def test_empty_bins_handling():
    """
    Verify that if no bins are found, the script still generates
    a valid JSON with an empty bins array and appropriate metadata.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        artifacts_dir = tmpdir / "artifacts"
        data_dir = tmpdir / "data" / "derived"
        config_dir = tmpdir / "data"

        artifacts_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)

        # Create config
        config_path = config_dir / "config.yaml"
        config_path.write_text("""
        materials:
          steel:
            mass: 0.01
            radius: 0.0025
        frequency_bins: []
        """)

        # Create empty CSV (headers only)
        csv_path = data_dir / "energy_samples.csv"
        pd.DataFrame(columns=["particle_id", "timestamp", "E_trans", "E_rot", "E_pot", "E_vib", "frequency_bin", "material", "pot_incomplete"]).to_csv(csv_path, index=False)

        import stats as stats_module
        def mock_empty_run(*args, **kwargs):
            return []

        stats_module.run_statistical_analysis = mock_empty_run

        try:
            import generate_statistical_results as gen_script
            gen_script.OUTPUT_PATH = artifacts_dir / "statistical_results.json"
            gen_script.INPUT_PATH = csv_path
            gen_script.CONFIG_PATH = config_path

            result_code = gen_script.main()
            assert result_code == 0

            output_file = artifacts_dir / "statistical_results.json"
            with open(output_file) as f:
                results = json.load(f)

            assert results["metadata"]["status"] == "no_data_bins"
            assert results["bins"] == []
        finally:
            stats_module.run_statistical_analysis = original_run if 'original_run' in locals() else lambda *a, **k: []