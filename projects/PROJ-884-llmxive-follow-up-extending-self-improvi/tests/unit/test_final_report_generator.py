"""
Unit tests for T031b: Final Report Generator.
"""
import json
import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.final_report_generator import generate_report_content, load_json_file, main

class TestReportGeneration:
    def test_generate_report_content_with_data(self):
        """Test that the report generator produces a valid markdown string with all sections."""
        
        # Mock data
        stats_results = {
            "z_test": {
                "p_value": 0.03,
                "z_statistic": 2.15,
                "confidence_interval": {"lower": 0.01, "upper": 0.05},
            },
            "power_analysis": {
                "power": 0.85,
                "status": "PASS"
            }
        }
        
        symbolic_results = {
            "total_success": 45,
            "total_attempts": 50,
            "total_energy_joules": 120.5
        }
        
        neural_results = {
            "total_success": 30,
            "total_attempts": 50,
            "total_energy_joules": 150.0
        }
        
        scaling_analysis = {
            "results": [
                {"n": 10, "time": 0.1, "complexity_class": "O(n)", "r_squared": 0.99, "status": "PASS"},
                {"n": 100, "time": 1.0, "complexity_class": "O(n)", "r_squared": 0.98, "status": "PASS"}
            ],
            "overall_status": "PASS"
        }
        
        exclusion_stats = {
            "total_exclusions": 5,
            "reasons": {"PARSE_FAILURE": 3, "IMPOSSIBLE_GOAL": 2}
        }

        report = generate_report_content(
            stats_results=stats_results,
            symbolic_results=symbolic_results,
            neural_results=neural_results,
            scaling_analysis=scaling_analysis,
            exclusion_stats=exclusion_stats
        )

        assert "# Final Report" in report
        assert "Success Rate Comparison" in report
        assert "Cost Comparison" in report
        assert "Complexity Analysis" in report
        assert "Statistical Significance" in report
        assert "Exclusion Analysis" in report
        
        # Check specific values
        assert "0.9000" in report # 45/50
        assert "0.6000" in report # 30/50
        assert "0.03" in report   # p-value
        assert "O(n)" in report   # complexity class

    def test_generate_report_content_missing_data(self):
        """Test that the report handles missing data gracefully."""
        report = generate_report_content(
            stats_results=None,
            symbolic_results=None,
            neural_results=None,
            scaling_analysis=None,
            exclusion_stats=None
        )
        
        assert "Warning" in report
        assert "missing" in report.lower()

    def test_main_integration(self, tmp_path):
        """Test the main function creates the file correctly."""
        # Create temporary data directory structure
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        # Create mock input files
        stats_file = data_dir / "stats_results.json"
        stats_file.write_text(json.dumps({"z_test": {"p_value": 0.01}}))
        
        sym_file = data_dir / "symbolic_results.json"
        sym_file.write_text(json.dumps({"total_success": 10, "total_attempts": 20, "total_energy_joules": 100}))
        
        neu_file = data_dir / "neural_baseline_results.json"
        neu_file.write_text(json.dumps({"total_success": 5, "total_attempts": 20, "total_energy_joules": 200}))
        
        scaling_csv = data_dir / "scaling_analysis.csv"
        with open(scaling_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "time", "complexity_class", "r_squared", "status"])
            writer.writerow([50, 0.5, "O(n^2)", 0.95, "PASS"])
        
        exclusions_file = data_dir / "exclusions.json"
        exclusions_file.write_text(json.dumps([{"reason_code": "TEST"}]))

        # Mock the PROJECT_ROOT to point to our temp directory
        with patch('analysis.final_report_generator.PROJECT_ROOT', tmp_path):
            main()
        
        # Verify output
        report_path = data_dir / "final_report.md"
        assert report_path.exists()
        content = report_path.read_text()
        assert "Final Report" in content
        assert "0.5000" in content # 10/20
        assert "0.2500" in content # 5/20