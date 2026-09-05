"""
Integration test for full statistical report generation.
"""
import pytest
import sys
import tempfile
from pathlib import Path

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stats_analysis import generate_statistical_report, StatisticalMetrics


class TestReportGeneration:
    """Integration tests for report generation."""

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
        assert "0.05" in report_text # Alpha level
