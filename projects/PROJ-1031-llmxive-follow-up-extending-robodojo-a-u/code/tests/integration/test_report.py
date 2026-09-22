"""
Integration test for full statistical report generation.

This test verifies that the statistical report generation module
produces a complete, correctly formatted report containing all
required sections including power analysis, hypothesis testing,
and failure rate analysis.
"""
import pytest
import sys
import tempfile
from pathlib import Path
import os

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stats_analysis import (
    generate_statistical_report,
    StatisticalMetrics,
    load_baseline_results,
    load_symbolic_results
)


class TestReportGeneration:
    """Integration tests for statistical report generation."""

    def test_report_generation_text(self):
        """Verify report generation produces expected text."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.8,
            symbolic_success_rate=0.85,
            wilcoxon_stat=1.5,
            p_value=0.03,
            effect_size=0.4,
            compute_reduction_pct=50.0,
            catastrophic_failure_rate=0.02,
            physics_fidelity_gap=0.1
        )

        report_text = generate_statistical_report(metrics)

        # Check for required content
        assert "Power Analysis: N=18" in report_text
        assert "Wilcoxon signed-rank test" in report_text
        assert "null hypothesis" in report_text
        assert "0.05" in report_text  # Alpha level
        assert "success rate" in report_text.lower()
        assert "compute reduction" in report_text.lower()
        assert "catastrophic failure" in report_text.lower()
        assert "physics fidelity gap" in report_text.lower()

    def test_report_generation_completeness(self):
        """Verify report contains all required sections."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.75,
            symbolic_success_rate=0.82,
            wilcoxon_stat=2.1,
            p_value=0.04,
            effect_size=0.35,
            compute_reduction_pct=45.0,
            catastrophic_failure_rate=0.03,
            physics_fidelity_gap=0.12
        )

        report_text = generate_statistical_report(metrics)

        # Check for section headers
        assert "## Statistical Analysis Report" in report_text
        assert "## Executive Summary" in report_text
        assert "## Methodology" in report_text
        assert "## Results" in report_text
        assert "## Conclusion" in report_text

        # Check specific numerical values are present
        assert "0.75" in report_text
        assert "0.82" in report_text
        assert "0.04" in report_text
        assert "45.0" in report_text

    def test_report_with_rejected_null_hypothesis(self):
        """Test report when null hypothesis is rejected (p < 0.05)."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.70,
            symbolic_success_rate=0.88,
            wilcoxon_stat=3.5,
            p_value=0.001,
            effect_size=0.6,
            compute_reduction_pct=60.0,
            catastrophic_failure_rate=0.01,
            physics_fidelity_gap=0.15
        )

        report_text = generate_statistical_report(metrics)

        assert "rejected" in report_text.lower()
        assert "statistically significant" in report_text.lower()
        assert "0.001" in report_text

    def test_report_with_failed_null_hypothesis(self):
        """Test report when null hypothesis is NOT rejected (p >= 0.05)."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.82,
            wilcoxon_stat=0.8,
            p_value=0.45,
            effect_size=0.1,
            compute_reduction_pct=10.0,
            catastrophic_failure_rate=0.04,
            physics_fidelity_gap=0.05
        )

        report_text = generate_statistical_report(metrics)

        assert "failed to reject" in report_text.lower() or "not rejected" in report_text.lower()
        assert "statistically significant" not in report_text.lower() or "no statistically significant" in report_text.lower()
        assert "0.45" in report_text

    def test_report_catastrophic_failure_threshold(self):
        """Test report correctly flags catastrophic failure rate."""
        # Test with rate below threshold (5%)
        metrics_pass = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.85,
            wilcoxon_stat=1.5,
            p_value=0.03,
            effect_size=0.4,
            compute_reduction_pct=50.0,
            catastrophic_failure_rate=0.02,  # 2% < 5%
            physics_fidelity_gap=0.1
        )

        report_pass = generate_statistical_report(metrics_pass)
        assert "Pass" in report_pass or "PASS" in report_pass
        assert "5%" in report_pass

        # Test with rate above threshold
        metrics_fail = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.85,
            wilcoxon_stat=1.5,
            p_value=0.03,
            effect_size=0.4,
            compute_reduction_pct=50.0,
            catastrophic_failure_rate=0.08,  # 8% > 5%
            physics_fidelity_gap=0.1
        )

        report_fail = generate_statistical_report(metrics_fail)
        assert "Fail" in report_fail or "FAIL" in report_fail
        assert "5%" in report_fail

    def test_report_file_output(self):
        """Test that report can be written to a file."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.85,
            wilcoxon_stat=1.5,
            p_value=0.03,
            effect_size=0.4,
            compute_reduction_pct=50.0,
            catastrophic_failure_rate=0.02,
            physics_fidelity_gap=0.1
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "statistical_report.txt"
            
            report_text = generate_statistical_report(metrics)
            output_path.write_text(report_text)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000  # Report should be substantial
            
            written_content = output_path.read_text()
            assert "Power Analysis: N=18" in written_content
            assert "Wilcoxon signed-rank test" in written_content

    def test_report_effect_size_interpretation(self):
        """Test that effect size is correctly interpreted in report."""
        # Small effect size
        metrics_small = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.82,
            wilcoxon_stat=0.9,
            p_value=0.04,
            effect_size=0.1,
            compute_reduction_pct=5.0,
            catastrophic_failure_rate=0.02,
            physics_fidelity_gap=0.1
        )
        
        report_small = generate_statistical_report(metrics_small)
        assert "small" in report_small.lower() or "0.1" in report_small

        # Large effect size
        metrics_large = StatisticalMetrics(
            baseline_success_rate=0.70,
            symbolic_success_rate=0.90,
            wilcoxon_stat=3.8,
            p_value=0.0005,
            effect_size=0.7,
            compute_reduction_pct=70.0,
            catastrophic_failure_rate=0.01,
            physics_fidelity_gap=0.15
        )
        
        report_large = generate_statistical_report(metrics_large)
        assert "large" in report_large.lower() or "0.7" in report_large

    def test_report_physics_fidelity_gap_analysis(self):
        """Test that physics fidelity gap is properly analyzed."""
        metrics = StatisticalMetrics(
            baseline_success_rate=0.80,
            symbolic_success_rate=0.85,
            wilcoxon_stat=1.5,
            p_value=0.03,
            effect_size=0.4,
            compute_reduction_pct=50.0,
            catastrophic_failure_rate=0.02,
            physics_fidelity_gap=0.12
        )

        report_text = generate_statistical_report(metrics)

        assert "0.12" in report_text
        assert "physics fidelity gap" in report_text.lower()
        assert "gap" in report_text.lower()