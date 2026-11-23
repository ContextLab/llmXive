"""
Unit tests for sensitivity report generation.
"""
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import yaml
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_sensitivity_report import (
    load_sensitivity_results,
    load_proxy_status,
    generate_report_content
)

class TestLoadSensitivityResults:
    def test_load_valid_csv(self):
        """Test loading a valid sensitivity results CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("threshold,accuracy,precision,recall,f1,fpr,fnr\n")
            f.write("0.3,0.85,0.82,0.88,0.85,0.12,0.12\n")
            f.write("0.5,0.88,0.87,0.89,0.88,0.11,0.11\n")
            f.write("0.7,0.82,0.90,0.75,0.82,0.05,0.25\n")
            temp_path = f.name
        
        try:
            df = load_sensitivity_results(temp_path)
            assert df is not None
            assert len(df) == 3
            assert 'threshold' in df.columns
            assert 'f1' in df.columns
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file returns None."""
        result = load_sensitivity_results("/nonexistent/path/file.csv")
        assert result is None
    
    def test_load_invalid_csv(self):
        """Test loading an invalid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,content\n")
            f.write("not,numeric,data\n")
            temp_path = f.name
        
        try:
            # Should still load but with potential type issues
            df = load_sensitivity_results(temp_path)
            assert df is not None
            assert len(df) == 2
        finally:
            os.unlink(temp_path)

class TestLoadProxyStatus:
    def test_load_valid_yaml(self):
        """Test loading a valid proxy status YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("has_proxy: true\n")
            f.write("proxy_variable: survival_rate\n")
            f.write("threshold_value: 0.5\n")
            f.write("classification_skipped: false\n")
            temp_path = f.name
        
        try:
            status = load_proxy_status(temp_path)
            assert status['has_proxy'] is True
            assert status['proxy_variable'] == 'survival_rate'
            assert status['classification_skipped'] is False
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file returns default status."""
        status = load_proxy_status("/nonexistent/path/file.yaml")
        assert status['has_proxy'] is False
        assert status['classification_skipped'] is True
    
    def test_load_invalid_yaml(self):
        """Test loading an invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:\n")
            f.write("  - broken\n")
            temp_path = f.name
        
        try:
            status = load_proxy_status(temp_path)
            # Should return default status on error
            assert isinstance(status, dict)
        finally:
            os.unlink(temp_path)

class TestGenerateReportContent:
    def test_generate_report_no_proxy(self):
        """Test report generation when no proxy is found."""
        proxy_status = {
            "has_proxy": False,
            "classification_skipped": True
        }
        
        content = generate_report_content(None, proxy_status, "/tmp/report.md")
        
        assert "Classification Status: SKIPPED" in content
        assert "No independent tolerance proxy" in content
        assert "N/A" in content
        assert "Circular classification" in content.lower()
    
    def test_generate_report_with_proxy_no_results(self):
        """Test report generation with proxy but no sensitivity results."""
        proxy_status = {
            "has_proxy": True,
            "proxy_variable": "survival_rate",
            "threshold_value": 0.5,
            "classification_skipped": False
        }
        
        content = generate_report_content(None, proxy_status, "/tmp/report.md")
        
        assert "Classification Status: PERFORMED" in content
        assert "No sensitivity sweep results" in content
    
    def test_generate_report_with_proxy_and_results(self):
        """Test report generation with proxy and sensitivity results."""
        proxy_status = {
            "has_proxy": True,
            "proxy_variable": "survival_rate",
            "threshold_value": 0.5,
            "classification_skipped": False
        }
        
        sensitivity_df = pd.DataFrame({
            'threshold': [0.3, 0.5, 0.7],
            'accuracy': [0.85, 0.88, 0.82],
            'precision': [0.82, 0.87, 0.90],
            'recall': [0.88, 0.89, 0.75],
            'f1': [0.85, 0.88, 0.82],
            'fpr': [0.12, 0.11, 0.05],
            'fnr': [0.12, 0.11, 0.25]
        })
        
        content = generate_report_content(sensitivity_df, proxy_status, "/tmp/report.md")
        
        assert "Classification Status: PERFORMED" in content
        assert "Threshold Sweep Results" in content
        assert "Optimal Threshold" in content
        assert "0.5" in content  # Optimal threshold
        assert "Robustness Analysis" in content
        assert "False Positive/Negative Trade-off" in content

class TestSensitivityReportIntegration:
    def test_report_contains_threshold_justification(self):
        """Test that report contains threshold justification."""
        proxy_status = {
            "has_proxy": True,
            "proxy_variable": "survival_rate",
            "threshold_value": 0.5,
            "classification_skipped": False
        }
        
        sensitivity_df = pd.DataFrame({
            'threshold': [0.3, 0.5, 0.7],
            'f1': [0.85, 0.88, 0.82]
        })
        
        content = generate_report_content(sensitivity_df, proxy_status, "/tmp/report.md")
        
        assert "Justification" in content
        assert "F1-score" in content
    
    def test_report_contains_impact_analysis(self):
        """Test that report contains impact analysis."""
        proxy_status = {
            "has_proxy": True,
            "proxy_variable": "survival_rate",
            "threshold_value": 0.5,
            "classification_skipped": False
        }
        
        sensitivity_df = pd.DataFrame({
            'threshold': [0.3, 0.5, 0.7],
            'f1': [0.85, 0.88, 0.82],
            'fpr': [0.12, 0.11, 0.05],
            'fnr': [0.12, 0.11, 0.25]
        })
        
        content = generate_report_content(sensitivity_df, proxy_status, "/tmp/report.md")
        
        assert "Trade-off" in content or "robustness" in content.lower()
    
    def test_skipped_classification_has_n_a_justification(self):
        """Test that skipped classification has N/A justification."""
        proxy_status = {
            "has_proxy": False,
            "classification_skipped": True
        }
        
        content = generate_report_content(None, proxy_status, "/tmp/report.md")
        
        assert "N/A" in content
        assert "not applicable" in content.lower()
        assert "no independent tolerance proxy" in content.lower()