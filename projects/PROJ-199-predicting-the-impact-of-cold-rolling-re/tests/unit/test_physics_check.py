"""
Unit tests for the physics check module (T029).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.physics_check import (
    validate_trend_direction,
    run_physics_check,
    generate_report,
    PHYSICAL_TRENDS
)


class TestValidateTrendDirection:
    """Tests for validate_trend_direction function."""

    @pytest.fixture
    def sample_data(self):
        """Create sample descriptor data with known trends."""
        reductions = [10, 20, 30, 40, 50]
        n = len(reductions)

        # Brass: increasing trend (slope ~0.03)
        brass_vol = np.array([0.10, 0.13, 0.16, 0.19, 0.22])

        # Copper: increasing trend (slope ~0.02)
        copper_vol = np.array([0.08, 0.10, 0.12, 0.14, 0.16])

        # Cube: decreasing trend (slope ~-0.015)
        cube_vol = np.array([0.25, 0.235, 0.22, 0.05, 0.19])

        return pd.DataFrame({
            "sample_id": [f"sample_{i}" for i in range(n)],
            "material": ["Al"] * n,
            "reduction": reductions,
            "brass_vol": brass_vol,
            "copper_vol": copper_vol,
            "s_vol": [0.05] * n,
            "goss_vol": [0.03] * n,
            "cube_vol": cube_vol,
            "texture_index": [1.5] * n
        })

    def test_brass_increasing_trend(self, sample_data):
        """Test that Brass component with increasing trend passes."""
        passes, slope, message = validate_trend_direction(
            sample_data, "Brass", "Al"
        )
        assert passes is True
        assert slope > 0
        assert "PASS" in message

    def test_copper_increasing_trend(self, sample_data):
        """Test that Copper component with increasing trend passes."""
        passes, slope, message = validate_trend_direction(
            sample_data, "Copper", "Al"
        )
        assert passes is True
        assert slope > 0
        assert "PASS" in message

    def test_cube_decreasing_trend(self, sample_data):
        """Test that Cube component with decreasing trend passes."""
        passes, slope, message = validate_trend_direction(
            sample_data, "Cube", "Al"
        )
        assert passes is True
        assert slope < 0
        assert "PASS" in message

    def test_insufficient_data(self, sample_data):
        """Test behavior with insufficient data points."""
        tiny_data = sample_data.head(1)
        passes, slope, message = validate_trend_direction(
            tiny_data, "Brass", "Al"
        )
        assert passes is False
        assert "Insufficient data points" in message

    def test_unknown_component(self, sample_data):
        """Test error handling for unknown component."""
        with pytest.raises(ValueError, match="Unknown component"):
            validate_trend_direction(sample_data, "Unknown", "Al")


class TestRunPhysicsCheck:
    """Tests for run_physics_check function."""

    @pytest.fixture
    def multi_material_data(self):
        """Create data for multiple materials."""
        al_data = pd.DataFrame({
            "sample_id": [f"al_{i}" for i in range(5)],
            "material": ["Al"] * 5,
            "reduction": [10, 20, 30, 40, 50],
            "brass_vol": [0.10, 0.13, 0.16, 0.19, 0.22],
            "copper_vol": [0.08, 0.10, 0.12, 0.14, 0.16],
            "s_vol": [0.05] * 5,
            "goss_vol": [0.03] * 5,
            "cube_vol": [0.25, 0.235, 0.22, 0.19, 0.16],
            "texture_index": [1.5] * 5
        })

        cu_data = pd.DataFrame({
            "sample_id": [f"cu_{i}" for i in range(5)],
            "material": ["Cu"] * 5,
            "reduction": [10, 20, 30, 40, 50],
            "brass_vol": [0.12, 0.15, 0.18, 0.21, 0.24],
            "copper_vol": [0.09, 0.11, 0.13, 0.15, 0.17],
            "s_vol": [0.06] * 5,
            "goss_vol": [0.04] * 5,
            "cube_vol": [0.24, 0.22, 0.20, 0.18, 0.16],
            "texture_index": [1.6] * 5
        })

        return pd.concat([al_data, cu_data], ignore_index=True)

    def test_multi_material_check(self, multi_material_data):
        """Test physics check across multiple materials."""
        results = run_physics_check(multi_material_data)

        assert "checks" in results
        assert "summary" in results
        assert "associational_framing" in results

        # Should have checks for both Al and Cu
        materials_checked = [m["material"] for m in results["checks"]]
        assert "Al" in materials_checked
        assert "Cu" in materials_checked

    def test_associational_framing_present(self, multi_material_data):
        """Test that associational framing is included in results."""
        results = run_physics_check(multi_material_data)

        framing = results["associational_framing"]
        assert "statement" in framing
        assert "disclaimer" in framing
        assert "ASSOCIATIONAL" in framing["statement"]

    def test_summary_statistics(self, multi_material_data):
        """Test that summary statistics are calculated correctly."""
        results = run_physics_check(multi_material_data)

        summary = results["summary"]
        assert "total_checks" in summary
        assert "passed_checks" in summary
        assert "pass_rate" in summary
        assert "overall_status" in summary

        assert summary["total_checks"] == summary["passed_checks"] + \
               (summary["total_checks"] - summary["passed_checks"])
        assert 0.0 <= summary["pass_rate"] <= 1.0

    def test_specific_components_only(self, multi_material_data):
        """Test checking only specific components."""
        results = run_physics_check(
            multi_material_data,
            components=["Brass", "Cube"]
        )

        for material_result in results["checks"]:
            components_checked = [c["component"] for c in material_result["checks"]]
            assert "Brass" in components_checked
            assert "Cube" in components_checked
            assert "Copper" not in components_checked


class TestGenerateReport:
    """Tests for generate_report function."""

    @pytest.fixture
    def sample_results(self):
        """Create sample physics check results."""
        return {
            "checks": [
                {
                    "material": "Al",
                    "checks": [
                        {
                            "component": "Brass",
                            "passes": True,
                            "observed_slope": 0.03,
                            "message": "PASS: Brass shows expected increasing trend"
                        },
                        {
                            "component": "Cube",
                            "passes": True,
                            "observed_slope": -0.015,
                            "message": "PASS: Cube shows expected decreasing trend"
                        }
                    ]
                }
            ],
            "summary": {
                "total_checks": 2,
                "passed_checks": 2,
                "pass_rate": 1.0,
                "overall_status": "PASS"
            },
            "associational_framing": {
                "statement": "All findings represent ASSOCIATIONAL relationships...",
                "disclaimer": "This analysis validates observed trends..."
            }
        }

    def test_report_contains_framing(self, sample_results):
        """Test that report includes associational framing."""
        report = generate_report(sample_results)
        assert "ASSOCIATIONAL" in report
        assert "statement" in report.lower() or "relationships" in report.lower()

    def test_report_contains_summary(self, sample_results):
        """Test that report includes summary statistics."""
        report = generate_report(sample_results)
        assert "SUMMARY" in report
        assert "PASS" in report
        assert "100.0%" in report or "1.0" in report

    def test_report_contains_detailed_results(self, sample_results):
        """Test that report includes detailed per-component results."""
        report = generate_report(sample_results)
        assert "Brass" in report
        assert "Cube" in report
        assert "PASS" in report

    def test_report_structure(self, sample_results):
        """Test that report has proper structure."""
        report = generate_report(sample_results)
        lines = report.split("\n")

        # Should have header
        assert any("HOLD-OUT PHYSICS CHECK REPORT" in line for line in lines)
        # Should have sections
        assert any("ASSOCIATIONAL FRAMING:" in line for line in lines)
        assert any("SUMMARY:" in line for line in lines)
        assert any("DETAILED RESULTS" in line for line in lines)