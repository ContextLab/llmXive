import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.report import (
    generate_bland_altman_report,
    generate_stability_report,
    generate_cross_dataset_comparison
)
from src.config import PROJECT_ROOT


class TestBlandAltmanReport:
    def test_generate_bland_altman_plot(self):
        """Test that Bland-Altman plot is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bland_altman_test.png"
            
            parametric_pvals = [0.01, 0.05, 0.1, 0.2, 0.3]
            empirical_pvals = [0.02, 0.04, 0.12, 0.18, 0.32]
            
            result_path = generate_bland_altman_report(
                parametric_pvals,
                empirical_pvals,
                output_path
            )
            
            assert Path(result_path).exists()
            assert result_path == str(output_path)
    
    def test_generate_bland_altman_empty_lists(self):
        """Test handling of empty p-value lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bland_altman_empty.png"
            
            result_path = generate_bland_altman_report([], [], output_path)
            
            assert Path(result_path).exists()
    
    def test_generate_bland_altman_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bland_altman_mismatch.png"
            
            with pytest.raises(ValueError):
                generate_bland_altman_report(
                    [0.01, 0.05],
                    [0.02, 0.04, 0.1],
                    output_path
                )

class TestStabilityReport:
    def test_generate_stability_report(self):
        """Test that stability report is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "stability_report_test.csv"
            
            metrics = {
                'stability_correlation': 0.75,
                'num_genes': 20000,
                'num_samples': 100
            }
            
            result_path = generate_stability_report(metrics, output_path)
            
            assert Path(result_path).exists()
            assert result_path == str(output_path)
            
            # Verify CSV content
            df = pd.read_csv(result_path)
            assert 'stability_correlation' in df.columns
            assert df['stability_correlation'].iloc[0] == 0.75

class TestCrossDatasetComparison:
    def test_generate_cross_dataset_visualization(self):
        """Test that cross-dataset comparison visualization is generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cross_dataset_test.png"
            
            results = [
                {'source': 'GEO', 'stability_correlation': 0.65},
                {'source': 'TCGA', 'stability_correlation': 0.72},
                {'source': 'ENCODE', 'stability_correlation': 0.58}
            ]
            
            result_path = generate_cross_dataset_comparison(results, output_path)
            
            assert Path(result_path).exists()
            assert result_path == str(output_path)
    
    def test_generate_cross_dataset_empty_results(self):
        """Test handling of empty results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cross_dataset_empty.png"
            
            result_path = generate_cross_dataset_comparison([], output_path)
            
            assert Path(result_path).exists()
    
    def test_generate_cross_dataset_missing_columns(self):
        """Test that missing required columns raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cross_dataset_missing.png"
            
            results = [
                {'source': 'GEO'},  # Missing stability_correlation
            ]
            
            with pytest.raises(ValueError):
                generate_cross_dataset_comparison(results, output_path)
    
    def test_generate_cross_dataset_single_source(self):
        """Test visualization with a single source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cross_dataset_single.png"
            
            results = [
                {'source': 'GEO', 'stability_correlation': 0.65}
            ]
            
            result_path = generate_cross_dataset_comparison(results, output_path)
            
            assert Path(result_path).exists()
    
    def test_generate_cross_dataset_with_optional_columns(self):
        """Test that optional columns don't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cross_dataset_optional.png"
            
            results = [
                {
                    'source': 'GEO',
                    'stability_correlation': 0.65,
                    'num_genes': 20000,
                    'num_samples': 50
                },
                {
                    'source': 'TCGA',
                    'stability_correlation': 0.72,
                    'num_genes': 18000,
                    'num_samples': 300
                }
            ]
            
            result_path = generate_cross_dataset_comparison(results, output_path)
            
            assert Path(result_path).exists()