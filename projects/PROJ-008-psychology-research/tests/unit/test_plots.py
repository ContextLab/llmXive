"""
Unit tests for visualization module, specifically focusing on funnel plot suppression logic.

This file extends the existing test suite for the plots module.
It includes tests for:
1. Forest plot generation (T031)
2. Funnel plot suppression when N < 10 (T032)
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from analysis.meta_analysis import MetaAnalysisStats
from data.models import EffectSize
from viz.plots import generate_forest_plot, generate_funnel_plot


class TestForestPlotGeneration:
    """Test cases for T031: Forest plot generation."""

    def test_forest_plot_with_valid_data(self, tmp_path):
        """Test that a forest plot is generated correctly with valid data."""
        # Create mock effect sizes
        effect_sizes = [
            EffectSize(
                study_id="Study_A",
                effect_size=0.5,
                se=0.1,
                ci_lower=0.3,
                ci_upper=0.7,
                n_intervention=30,
                n_control=30,
                domain="Social Skills"
            ),
            EffectSize(
                study_id="Study_B",
                effect_size=0.8,
                se=0.15,
                ci_lower=0.5,
                ci_upper=1.1,
                n_intervention=25,
                n_control=25,
                domain="Communication"
            ),
        ]
        
        output_path = tmp_path / "forest_plot.png"
        
        # Generate plot
        generate_forest_plot(effect_sizes, str(output_path))
        
        # Verify file exists and has content
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_forest_plot_with_single_study(self, tmp_path):
        """Test forest plot generation with a single study."""
        effect_sizes = [
            EffectSize(
                study_id="Single_Study",
                effect_size=0.3,
                se=0.1,
                ci_lower=0.1,
                ci_upper=0.5,
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            ),
        ]
        
        output_path = tmp_path / "forest_plot_single.png"
        
        generate_forest_plot(effect_sizes, str(output_path))
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

class TestFunnelPlotSuppression:
    """Test cases for T032: Funnel plot suppression logic when N < 10."""

    def test_funnel_plot_suppressed_when_n_less_than_10(self, tmp_path):
        """
        Verify that generate_funnel_plot raises a ValueError when N < 10.
        This enforces FR-014: suppress funnel plot if N < 10.
        """
        # Create only 5 effect sizes (N < 10)
        effect_sizes = [
            EffectSize(
                study_id=f"Study_{i}",
                effect_size=0.5 + (i * 0.1),
                se=0.1 + (i * 0.01),
                ci_lower=0.4 + (i * 0.1),
                ci_upper=0.6 + (i * 0.1),
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            )
            for i in range(5)
        ]
        
        output_path = tmp_path / "funnel_plot.png"
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            generate_funnel_plot(effect_sizes, str(output_path))
        
        assert "N < 10" in str(exc_info.value)
        assert "funnel plot" in str(exc_info.value).lower()
        assert str(exc_info.value).count("5") > 0  # Mention actual count
        
        # Verify no file was created
        assert not output_path.exists()
    
    def test_funnel_plot_suppressed_when_n_equals_9(self, tmp_path):
        """Verify suppression when N = 9 (just under threshold)."""
        effect_sizes = [
            EffectSize(
                study_id=f"Study_{i}",
                effect_size=0.5,
                se=0.1,
                ci_lower=0.3,
                ci_upper=0.7,
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            )
            for i in range(9)
        ]
        
        output_path = tmp_path / "funnel_plot_n9.png"
        
        with pytest.raises(ValueError) as exc_info:
            generate_funnel_plot(effect_sizes, str(output_path))
        
        assert "N < 10" in str(exc_info.value)
        assert not output_path.exists()
    
    def test_funnel_plot_allowed_when_n_equals_10(self, tmp_path):
        """Verify that funnel plot is generated when N >= 10."""
        effect_sizes = [
            EffectSize(
                study_id=f"Study_{i}",
                effect_size=0.5 + (i * 0.05),
                se=0.1 + (i * 0.005),
                ci_lower=0.4 + (i * 0.05),
                ci_upper=0.6 + (i * 0.05),
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            )
            for i in range(10)
        ]
        
        output_path = tmp_path / "funnel_plot_n10.png"
        
        # Should NOT raise an error
        generate_funnel_plot(effect_sizes, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_funnel_plot_allowed_when_n_greater_than_10(self, tmp_path):
        """Verify that funnel plot is generated when N > 10."""
        effect_sizes = [
            EffectSize(
                study_id=f"Study_{i}",
                effect_size=0.5 + (i * 0.05),
                se=0.1 + (i * 0.005),
                ci_lower=0.4 + (i * 0.05),
                ci_upper=0.6 + (i * 0.05),
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            )
            for i in range(15)
        ]
        
        output_path = tmp_path / "funnel_plot_n15.png"
        
        # Should NOT raise an error
        generate_funnel_plot(effect_sizes, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_error_message_contains_helpful_guidance(self, tmp_path):
        """Verify that the error message provides helpful guidance for users."""
        effect_sizes = [
            EffectSize(
                study_id=f"Study_{i}",
                effect_size=0.5,
                se=0.1,
                ci_lower=0.3,
                ci_upper=0.7,
                n_intervention=20,
                n_control=20,
                domain="Social Skills"
            )
            for i in range(3)
        ]
        
        output_path = tmp_path / "funnel_plot.png"
        
        with pytest.raises(ValueError) as exc_info:
            generate_funnel_plot(effect_sizes, str(output_path))
        
        error_msg = str(exc_info.value).lower()
        # Check for helpful keywords
        assert any(keyword in error_msg for keyword in ["n <", "threshold", "minimum", "sample size"])
        
        # Verify no file was created
        assert not output_path.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])