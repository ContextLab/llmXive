"""
Tests for the power analysis module.
"""
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from code.research.power_analysis import calculate_sample_size, generate_report, main


class TestCalculateSampleSize:
    def test_calculate_sample_size_default_values(self):
        """Test sample size calculation with default parameters."""
        n_per_group = calculate_sample_size(
            effect_size=0.25,
            alpha=0.05,
            power=0.80,
            k_groups=3
        )
        assert isinstance(n_per_group, int)
        assert n_per_group > 0

    def test_calculate_sample_size_small_effect(self):
        """Test sample size calculation with small effect size."""
        n_per_group = calculate_sample_size(
            effect_size=0.10,
            alpha=0.05,
            power=0.80,
            k_groups=3
        )
        assert isinstance(n_per_group, int)
        assert n_per_group > 0
        # Small effect should require larger sample size
        assert n_per_group > calculate_sample_size(0.25, 0.05, 0.80, 3)

    def test_calculate_sample_size_large_effect(self):
        """Test sample size calculation with large effect size."""
        n_per_group = calculate_sample_size(
            effect_size=0.40,
            alpha=0.05,
            power=0.80,
            k_groups=3
        )
        assert isinstance(n_per_group, int)
        assert n_per_group > 0
        # Large effect should require smaller sample size
        assert n_per_group < calculate_sample_size(0.25, 0.05, 0.80, 3)

    def test_calculate_sample_size_invalid_parameters(self):
        """Test that invalid parameters raise an error."""
        with pytest.raises(ValueError):
            calculate_sample_size(
                effect_size=0.0,  # Invalid effect size
                alpha=0.05,
                power=0.80,
                k_groups=3
            )


class TestGenerateReport:
    def test_generate_report_structure(self):
        """Test that the report contains required sections."""
        results = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "target_power": 0.80,
            "k_groups": 3,
            "n_per_group": 52,
            "total_required_n": 156,
            "analysis_method": "One-Way ANOVA (F-test)",
            "software": "statsmodels"
        }
        
        report = generate_report(results)
        
        assert "# Pre-Study Power Analysis Report" in report
        assert "## Study Design" in report
        assert "## Parameters" in report
        assert "## Results" in report
        assert "## Conclusion" in report
        
        # Check for specific values
        assert "0.25" in report
        assert "0.05" in report
        assert "0.80" in report
        assert "52" in report
        assert "156" in report

    def test_generate_report_formatting(self):
        """Test that the report is properly formatted markdown."""
        results = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "target_power": 0.80,
            "k_groups": 3,
            "n_per_group": 52,
            "total_required_n": 156,
            "analysis_method": "One-Way ANOVA (F-test)",
            "software": "statsmodels"
        }
        
        report = generate_report(results)
        
        # Check for markdown table formatting
        assert "| Parameter | Value | Description |" in report
        assert "| :--- | :--- | :--- |" in report


class TestMain:
    def test_main_creates_files(self):
        """Test that main() creates the expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the output directory
            with patch('code.research.power_analysis.os.makedirs') as mock_makedirs:
                with patch('code.research.power_analysis.open', create=True) as mock_open:
                    # Mock the file write operations
                    mock_file = mock_open.return_value.__enter__.return_value
                    
                    # Run main with test arguments
                    test_args = [
                        'power_analysis.py',
                        '--effect_size', '0.25',
                        '--alpha', '0.05',
                        '--power', '0.80',
                        '--test_type', 'anova'
                    ]
                    
                    with patch('sys.argv', test_args):
                        main()
                    
                    # Verify that open was called twice (JSON and MD)
                    assert mock_open.call_count >= 2

    def test_main_invalid_test_type(self):
        """Test that main() exits with error for unsupported test types."""
        test_args = [
            'power_analysis.py',
            '--test_type', 'ttest'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_output_files_content(self):
        """Test that the output files contain valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory to capture output
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create research directory
                os.makedirs('research', exist_ok=True)
                
                # Run main with test arguments
                test_args = [
                    'power_analysis.py',
                    '--effect_size', '0.25',
                    '--alpha', '0.05',
                    '--power', '0.80',
                    '--test_type', 'anova'
                ]
                
                with patch('sys.argv', test_args):
                    main()
                
                # Check JSON file
                json_path = os.path.join('research', 'power_calculation.json')
                assert os.path.exists(json_path)
                
                with open(json_path, 'r') as f:
                    results = json.load(f)
                
                assert 'effect_size' in results
                assert 'alpha' in results
                assert 'target_power' in results
                assert 'k_groups' in results
                assert 'n_per_group' in results
                assert 'total_required_n' in results
                
                # Check MD file
                md_path = os.path.join('research', 'power_report.md')
                assert os.path.exists(md_path)
                
                with open(md_path, 'r') as f:
                    report = f.read()
                
                assert "# Pre-Study Power Analysis Report" in report
                assert "## Conclusion" in report
                
            finally:
                os.chdir(original_dir)
