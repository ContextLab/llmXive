import pytest
import math
import json
import tempfile
from pathlib import Path
import pandas as pd

# Import the functions to test
from analysis.power import (
    calculate_variance_from_metrics,
    calculate_mde,
    calculate_required_sample_size,
    run_power_analysis
)

class TestPowerAnalysis:
    def test_calculate_variance_from_metrics(self):
        # Test variance calculation from MAE
        # MAE = 0.8 * sigma => sigma = MAE / 0.8
        # Variance = sigma^2
        metrics = {'mae': 0.8}
        variance = calculate_variance_from_metrics(metrics, 100)
        # sigma = 0.8 / sqrt(2/pi) = 0.8 * sqrt(pi/2)
        # variance = (0.8 * sqrt(pi/2))^2 = 0.64 * pi/2
        expected_variance = (0.8 * math.sqrt(math.pi / 2.0)) ** 2
        assert math.isclose(variance, expected_variance, rel_tol=1e-5)

    def test_calculate_mde(self):
        # Test MDE calculation
        variance = 1.0
        n_samples = 100
        mde = calculate_mde(variance, n_samples)
        # MDE = (1.96 + 0.84) * 1 / 10 = 2.8 / 10 = 0.28
        expected_mde = (1.96 + 0.84) * math.sqrt(variance) / math.sqrt(n_samples)
        assert math.isclose(mde, expected_mde, rel_tol=1e-5)

    def test_calculate_required_sample_size(self):
        # Test sample size calculation
        variance = 1.0
        effect_size = 0.5
        n = calculate_required_sample_size(variance, effect_size)
        # n = ((1.96 + 0.84) * 1 / 0.5)^2 = (2.8 / 0.5)^2 = 5.6^2 = 31.36 => 32
        expected_n = math.ceil(((1.96 + 0.84) * math.sqrt(variance) / effect_size) ** 2)
        assert n == expected_n

    def test_run_power_analysis_integration(self):
        # Test the full run_power_analysis function
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            metrics_path = tmpdir / "metrics.json"
            output_path = tmpdir / "power_report.csv"
            
            # Create a mock metrics file
            mock_metrics = {
                'mae': 0.8,
                'n_samples': 100
            }
            with open(metrics_path, 'w') as f:
                json.dump(mock_metrics, f)
            
            # Run the analysis
            run_power_analysis(metrics_path, output_path)
            
            # Check the output file exists and has content
            assert output_path.exists()
            df = pd.read_csv(output_path)
            assert len(df) > 0
            assert 'parameter' in df.columns
            assert 'value' in df.columns
            
            # Check for specific parameters
            parameters = df['parameter'].tolist()
            assert 'minimum_detectable_effect' in parameters
            assert 'required_sample_size' in parameters