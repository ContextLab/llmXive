import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from report_sensitivity import generate_report, load_sensitivity_data

class TestSensitivityReportGeneration:
    """Integration tests for sensitivity report generation."""

    @pytest.fixture
    def sample_sensitivity_data(self):
        """Create sample sensitivity data for testing."""
        data = {
            'threshold': [1.0, 1.25, 1.5, 1.75, 2.0],
            'mond_pass_rate': [0.85, 0.90, 0.92, 0.94, 0.95],
            'nfw_pass_rate': [0.70, 0.75, 0.80, 0.82, 0.85]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_report_generation_basic(self, sample_sensitivity_data, temp_output_dir):
        """Test basic report generation with sample data."""
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_sensitivity_data,
            output_path=output_path,
            thresholds=[1.0, 1.5, 2.0]
        )
        
        # Verify file was created
        assert Path(output_path).exists(), "Report file was not created"
        
        # Verify file has content
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert len(content) > 100, "Report content is too short"
        assert "# Sensitivity Analysis Report" in content, "Missing report title"
        assert "Executive Summary" in content, "Missing executive summary section"
        assert "Key Findings" in content, "Missing key findings section"
        assert "Methodology" in content, "Missing methodology section"
        assert "Visualizations" in content, "Missing visualizations section"
        assert "Threshold-Specific Analysis" in content, "Missing threshold analysis section"

    def test_report_contains_threshold_table(self, sample_sensitivity_data, temp_output_dir):
        """Test that report contains the threshold comparison table."""
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_sensitivity_data,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check for table structure
        assert "| Threshold |" in content, "Missing threshold table header"
        assert "| MOND Pass Rate |" in content, "Missing MOND column"
        assert "| NFW Pass Rate |" in content, "Missing NFW column"
        
        # Check for data rows
        assert "1.00" in content, "Missing threshold 1.00"
        assert "1.25" in content, "Missing threshold 1.25"
        assert "1.50" in content, "Missing threshold 1.50"
        assert "1.75" in content, "Missing threshold 1.75"

    def test_report_contains_ascii_chart(self, sample_sensitivity_data, temp_output_dir):
        """Test that report contains ASCII visualization."""
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_sensitivity_data,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check for ASCII chart elements
        assert "Pass Rate Comparison" in content, "Missing chart title"
        assert "█" in content or "#" in content, "Missing bar chart characters"
        assert "Threshold" in content, "Missing chart axis labels"

    def test_report_with_different_thresholds(self, sample_sensitivity_data, temp_output_dir):
        """Test report generation with custom threshold list."""
        output_path = os.path.join(temp_output_dir, "test_report.md")
        custom_thresholds = [1.1, 1.6]
        
        generate_report(
            sensitivity_df=sample_sensitivity_data,
            output_path=output_path,
            thresholds=custom_thresholds
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check that custom thresholds are analyzed
        assert "1.10" in content or "1.60" in content, "Custom thresholds not analyzed"
        assert "Threshold-Specific Analysis" in content, "Missing threshold analysis section"

    def test_report_handles_ties(self, temp_output_dir):
        """Test report generation when models have equal performance."""
        data = {
            'threshold': [1.0, 1.5, 2.0],
            'mond_pass_rate': [0.8, 0.8, 0.8],
            'nfw_pass_rate': [0.8, 0.8, 0.8]
        }
        sample_df = pd.DataFrame(data)
        
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_df,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "Tie" in content or "equivalent" in content.lower(), "Tie handling missing"

    def test_report_file_content_validity(self, sample_sensitivity_data, temp_output_dir):
        """Test that the generated report is valid markdown and contains expected sections."""
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_sensitivity_data,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Verify markdown structure
        lines = content.split('\n')
        
        # Should have headers
        headers = [line for line in lines if line.startswith('#')]
        assert len(headers) >= 5, f"Expected at least 5 headers, found {len(headers)}"
        
        # Should have statistics
        assert "MOND Pass Rate" in content, "Missing MOND statistics"
        assert "NFW Pass Rate" in content, "Missing NFW statistics"
        
        # Should have recommendations
        assert "Recommendations" in content, "Missing recommendations section"

    def test_report_with_realistic_data(self, temp_output_dir):
        """Test report generation with more realistic sensitivity data."""
        # Simulate realistic data with some variance
        thresholds = np.linspace(0.8, 2.5, 10)
        mond_rates = 0.7 + 0.2 * (thresholds - 0.8) / (2.5 - 0.8) + np.random.normal(0, 0.02, len(thresholds))
        nfw_rates = 0.6 + 0.25 * (thresholds - 0.8) / (2.5 - 0.8) + np.random.normal(0, 0.02, len(thresholds))
        
        # Clip to valid range
        mond_rates = np.clip(mond_rates, 0, 1)
        nfw_rates = np.clip(nfw_rates, 0, 1)
        
        data = {
            'threshold': thresholds,
            'mond_pass_rate': mond_rates,
            'nfw_pass_rate': nfw_rates
        }
        sample_df = pd.DataFrame(data)
        
        output_path = os.path.join(temp_output_dir, "test_report.md")
        
        generate_report(
            sensitivity_df=sample_df,
            output_path=output_path,
            thresholds=[1.0, 1.5, 2.0]
        )
        
        assert Path(output_path).exists(), "Report not created with realistic data"
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert len(content) > 500, "Report too short for realistic data"
        assert "Statistical Robustness" in content, "Missing robustness section"

class TestLoadSensitivityData:
    """Tests for loading sensitivity data."""

    def test_load_from_existing_file(self, temp_output_dir):
        """Test loading data from an existing CSV file."""
        # Create a test CSV
        csv_path = os.path.join(temp_output_dir, "test_sensitivity.csv")
        data = {
            'threshold': [1.0, 1.5, 2.0],
            'mond_pass_rate': [0.8, 0.9, 0.95],
            'nfw_pass_rate': [0.7, 0.8, 0.85]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Load and verify
        df = load_sensitivity_data(csv_path)
        
        assert len(df) == 3, "Incorrect number of rows loaded"
        assert 'threshold' in df.columns, "Missing threshold column"
        assert 'mond_pass_rate' in df.columns, "Missing mond_pass_rate column"
        assert 'nfw_pass_rate' in df.columns, "Missing nfw_pass_rate column"

    def test_load_from_missing_file(self, temp_output_dir):
        """Test that loading from a missing file raises an error."""
        missing_path = os.path.join(temp_output_dir, "nonexistent.csv")
        
        with pytest.raises(FileNotFoundError):
            load_sensitivity_data(missing_path)