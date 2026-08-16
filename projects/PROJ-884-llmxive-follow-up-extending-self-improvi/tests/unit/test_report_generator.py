"""
Unit tests for the Report Generator (T031).
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the dependencies or create temp files
# Since we can't easily import the real stats/metrics without running them first,
# we will test the ReportGenerator logic by creating fake CSV files.

from analysis.report_generator import ReportGenerator


class TestReportGenerator:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def mock_metrics_csv(self, temp_dir):
        """Create a mock experiment_metrics.csv."""
        path = Path(temp_dir) / "experiment_metrics.csv"
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['method', 'success_count', 'total_attempts', 'wall_clock_time_seconds', 'energy_joules'])
            writer.writerow(['symbolic', 45, 50, 0.05, 10.0])
            writer.writerow(['neural', 30, 50, 0.12, 25.0])
            writer.writerow(['symbolic', 48, 50, 0.06, 11.0])
            writer.writerow(['neural', 32, 50, 0.11, 24.0])
        return str(path)

    @pytest.fixture
    def mock_scaling_csv(self, temp_dir):
        """Create a mock scaling_analysis.csv."""
        path = Path(temp_dir) / "scaling_analysis.csv"
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['method', 'problem_size', 'avg_time_seconds', 'complexity_class'])
            writer.writerow(['symbolic', 100, 0.05, 'O(n)'])
            writer.writerow(['symbolic', 200, 0.10, 'O(n)'])
            writer.writerow(['neural', 100, 0.12, 'O(n^2)'])
            writer.writerow(['neural', 200, 0.48, 'O(n^2)'])
        return str(path)

    def test_load_metrics(self, temp_dir, mock_metrics_csv):
        """Test loading metrics from CSV."""
        # Temporarily change the path logic or mock the file location
        # Since ReportGenerator looks in 'data/processed', we'll copy the file there or
        # adjust the test to use a specific instance.
        
        # Let's create a generator instance pointing to temp_dir
        generator = ReportGenerator(output_dir=temp_dir)
        
        # Copy mock file to expected location
        import shutil
        shutil.copy(mock_metrics_csv, Path(temp_dir) / "experiment_metrics.csv")

        rows = generator.load_metrics()
        assert rows is not None
        assert len(rows) == 4
        assert rows[0]['method'] == 'symbolic'

    def test_calculate_success_rates(self, temp_dir, mock_metrics_csv):
        """Test success rate calculation."""
        generator = ReportGenerator(output_dir=temp_dir)
        shutil.copy(mock_metrics_csv, Path(temp_dir) / "experiment_metrics.csv")
        
        rows = generator.load_metrics()
        rates = generator.calculate_success_rates(rows)
        
        # Symbolic: (45+48)/(50+50) = 93/100 = 0.93
        # Neural: (30+32)/(50+50) = 62/100 = 0.62
        assert abs(rates['symbolic'] - 0.93) < 0.001
        assert abs(rates['neural'] - 0.62) < 0.001

    def test_calculate_costs(self, temp_dir, mock_metrics_csv):
        """Test cost calculation."""
        generator = ReportGenerator(output_dir=temp_dir)
        shutil.copy(mock_metrics_csv, Path(temp_dir) / "experiment_metrics.csv")
        
        rows = generator.load_metrics()
        costs = generator.calculate_costs(rows)
        
        # Symbolic time: (0.05+0.06)/2 = 0.055
        # Neural time: (0.12+0.11)/2 = 0.115
        assert abs(costs['symbolic_avg_time'] - 0.055) < 0.001
        assert abs(costs['neural_avg_time'] - 0.115) < 0.001

    def test_generate_report_with_data(self, temp_dir, mock_metrics_csv, mock_scaling_csv):
        """Test full report generation."""
        generator = ReportGenerator(output_dir=temp_dir)
        shutil.copy(mock_metrics_csv, Path(temp_dir) / "experiment_metrics.csv")
        shutil.copy(mock_scaling_csv, Path(temp_dir) / "scaling_analysis.csv")

        report_path = generator.generate_report()
        
        assert report_path.exists()
        
        content = report_path.read_text()
        assert "Final Report" in content
        assert "Success Rate Comparison" in content
        assert "Cost Comparison" in content
        assert "Complexity Analysis" in content
        assert "Statistical Significance" in content
        assert "O(n)" in content  # From scaling
        assert "O(n^2)" in content

    def test_generate_report_missing_data(self, temp_dir):
        """Test report generation when files are missing."""
        generator = ReportGenerator(output_dir=temp_dir)
        report_path = generator.generate_report()
        
        assert report_path.exists()
        content = report_path.read_text()
        assert "Data Missing" in content
        assert "Unable to calculate" in content