"""
Unit tests for code/generation/power_analysis.py
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.generation.power_analysis import calculate_power_gap, generate_report


class TestPowerAnalysis:
    """Tests for power analysis calculations."""

    def test_calculate_power_gap_basic(self):
        """Test basic gap calculation with standard parameters."""
        result = calculate_power_gap(spec_n=80, ci_n=20, num_prompts=4, num_strategies=4)
        
        assert result["spec_total"] == 80 * 4 * 4  # 1280
        assert result["ci_total"] == 20 * 4 * 4    # 320
        assert result["gap_per_condition"] == 60
        assert result["total_gap"] == 960
        assert abs(result["coverage_pct"] - 25.0) < 0.1

    def test_calculate_power_gap_edge_cases(self):
        """Test edge cases where CI equals Spec."""
        result = calculate_power_gap(spec_n=50, ci_n=50, num_prompts=2, num_strategies=2)
        
        assert result["spec_total"] == 200
        assert result["ci_total"] == 200
        assert result["gap_per_condition"] == 0
        assert result["total_gap"] == 0
        assert abs(result["coverage_pct"] - 100.0) < 0.1

    def test_generate_report_contains_sections(self):
        """Test that the generated report contains required sections."""
        metrics = calculate_power_gap(spec_n=80, ci_n=20, num_prompts=4, num_strategies=4)
        report = generate_report(metrics)
        
        assert "Power Analysis & Gap Resolution Report" in report
        assert "Executive Summary" in report
        assert "Calculated Metrics" in report
        assert "Execution Paths" in report
        assert "Pilot Mode" in report
        assert "Full Study" in report
        assert "Recommendations" in report
        assert "1280" in report  # Spec total
        assert "320" in report   # CI total

    def test_report_formatting(self):
        """Test that the report is valid Markdown structure."""
        metrics = calculate_power_gap(spec_n=80, ci_n=20, num_prompts=4, num_strategies=4)
        report = generate_report(metrics)
        
        # Check for table structure
        assert "| Metric | Value |" in report
        assert "| --- | --- |" in report
        
        # Check for list items
        assert "- **Target**:" in report
        assert "- **Volume**:" in report
        
        # Check for numeric values in report
        assert "N=80" in report
        assert "N=20" in report