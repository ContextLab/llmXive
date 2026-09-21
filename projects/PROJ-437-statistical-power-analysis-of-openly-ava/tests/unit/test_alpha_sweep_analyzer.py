"""
Unit tests for alpha-sweep sensitivity analysis.

These tests verify the core functionality of the alpha_sweep_analyzer module,
including rate recalculation, summary generation, and report rendering.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from analysis.alpha_sweep_analyzer import (
    recalculate_replication_rates,
    generate_sensitivity_summary,
    render_markdown_report,
    ALPHA_VALUES,
    PARADIGMS
)


class TestRecalculateReplicationRates:
    """Tests for the recalculate_replication_rates function."""

    def test_basic_rate_calculation(self):
        """Test basic replication rate calculation with known values."""
        # Create mock paradigm data
        paradigm_data = {
            'bootstrap_results': [
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.03,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.48
                },
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.08,
                    'replication_success': 0,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.3
                },
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.02,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.52
                }
            ]
        }

        # Test with alpha=0.05
        rate = recalculate_replication_rates(
            paradigm_data,
            alpha=0.05,
            sample_size=20,
            smoothing_kernel='4mm'
        )

        # Should be 2/3 = 0.667
        assert 0.66 <= rate <= 0.68

    def test_alpha_threshold_effect(self):
        """Test that changing alpha threshold affects replication rates."""
        paradigm_data = {
            'bootstrap_results': [
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.03,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.48
                },
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.07,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.48
                }
            ]
        }

        # With alpha=0.05, only first iteration passes (p=0.03)
        rate_005 = recalculate_replication_rates(
            paradigm_data,
            alpha=0.05,
            sample_size=20,
            smoothing_kernel='4mm'
        )
        assert rate_005 == 0.5  # 1/2

        # With alpha=0.10, both iterations pass (p=0.03 and p=0.07)
        rate_010 = recalculate_replication_rates(
            paradigm_data,
            alpha=0.10,
            sample_size=20,
            smoothing_kernel='4mm'
        )
        assert rate_010 == 1.0  # 2/2

    def test_magnitude_match_filtering(self):
        """Test that magnitude match criterion filters results correctly."""
        paradigm_data = {
            'bootstrap_results': [
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.03,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.6  # Within 20% (0.4-0.6)
                },
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.03,
                    'replication_success': 1,
                    'train_effect_size': 0.5,
                    'test_effect_size': 0.7  # Outside 20% (0.4-0.6)
                }
            ]
        }

        rate = recalculate_replication_rates(
            paradigm_data,
            alpha=0.05,
            sample_size=20,
            smoothing_kernel='4mm'
        )

        # First passes magnitude check (0.6/0.5 = 1.2), second fails (0.7/0.5 = 1.4)
        assert rate == 0.5  # 1/2

    def test_empty_results(self):
        """Test handling of empty bootstrap results."""
        paradigm_data = {
            'bootstrap_results': []
        }

        rate = recalculate_replication_rates(
            paradigm_data,
            alpha=0.05,
            sample_size=20,
            smoothing_kernel='4mm'
        )

        assert rate == 0.0

    def test_missing_keys(self):
        """Test handling of missing keys in iteration data."""
        paradigm_data = {
            'bootstrap_results': [
                {
                    'smoothing_kernel': '4mm',
                    'sample_size': 20,
                    'p_value': 0.03
                    # Missing replication_success, train_effect_size, test_effect_size
                }
            ]
        }

        rate = recalculate_replication_rates(
            paradigm_data,
            alpha=0.05,
            sample_size=20,
            smoothing_kernel='4mm'
        )

        # Should handle gracefully, likely return 0.0 or skip
        assert rate >= 0.0


class TestGenerateSensitivitySummary:
    """Tests for the generate_sensitivity_summary function."""

    def test_summary_structure(self):
        """Test that summary has correct structure."""
        all_paradigm_results = [
            {
                'paradigm': 'ds000030_motor',
                'alpha_sweep_results': [
                    {
                        'alpha': 0.05,
                        'kernel_sensitivity': {
                            '4mm': [{'sample_size': 20, 'replication_rate': 0.5}]
                        }
                    }
                ]
            }
        ]

        summary = generate_sensitivity_summary(all_paradigm_results)

        assert 'alpha_values' in summary
        assert 'paradigm_count' in summary
        assert 'paradigms' in summary
        assert 'cross_paradigm_stats' in summary
        assert summary['paradigm_count'] == 1

    def test_cross_paradigm_stats_calculation(self):
        """Test that cross-paradigm statistics are calculated correctly."""
        all_paradigm_results = [
            {
                'paradigm': 'paradigm1',
                'alpha_sweep_results': [
                    {
                        'alpha': 0.05,
                        'kernel_sensitivity': {
                            '4mm': [
                                {'sample_size': 20, 'replication_rate': 0.5},
                                {'sample_size': 30, 'replication_rate': 0.7}
                            ]
                        }
                    }
                ]
            },
            {
                'paradigm': 'paradigm2',
                'alpha_sweep_results': [
                    {
                        'alpha': 0.05,
                        'kernel_sensitivity': {
                            '4mm': [
                                {'sample_size': 20, 'replication_rate': 0.6},
                                {'sample_size': 30, 'replication_rate': 0.8}
                            ]
                        }
                    }
                ]
            }
        ]

        summary = generate_sensitivity_summary(all_paradigm_results)

        # For alpha=0.05, kernel=4mm: rates are [0.5, 0.7, 0.6, 0.8]
        stats = summary['cross_paradigm_stats']['0.05']['4mm']
        assert abs(stats['mean_power'] - 0.65) < 0.01
        assert abs(stats['min_power'] - 0.5) < 0.01
        assert abs(stats['max_power'] - 0.8) < 0.01


class TestRenderMarkdownReport:
    """Tests for the render_markdown_report function."""

    def test_report_generation(self):
        """Test that markdown report is generated correctly."""
        sensitivity_summary = {
            'alpha_values': [0.01, 0.05, 0.10],
            'paradigm_count': 2,
            'paradigms': [
                {
                    'name': 'ds000030_motor',
                    'alpha_results': [
                        {
                            'alpha': 0.05,
                            'kernel_sensitivity': {
                                '4mm': [{'sample_size': 20, 'replication_rate': 0.5}]
                            }
                        }
                    ]
                }
            ],
            'cross_paradigm_stats': {
                '0.05': {
                    '4mm': {
                        'mean_power': 0.5,
                        'std_power': 0.0,
                        'min_power': 0.5,
                        'max_power': 0.5
                    }
                }
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'
            render_markdown_report(sensitivity_summary, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for key sections
            assert '# Alpha-Sweep Sensitivity Analysis Report' in content
            assert '## Overview' in content
            assert '## Methodology' in content
            assert '## Cross-Paradigm Summary Statistics' in content
            assert '## Per-Paradigm Detailed Results' in content
            assert '## Sensitivity Analysis Conclusions' in content
            assert 'ds000030_motor' in content
            assert '0.05' in content

    def test_report_with_multiple_paradigms(self):
        """Test report generation with multiple paradigms."""
        sensitivity_summary = {
            'alpha_values': [0.05],
            'paradigm_count': 3,
            'paradigms': [
                {'name': 'paradigm1', 'alpha_results': []},
                {'name': 'paradigm2', 'alpha_results': []},
                {'name': 'paradigm3', 'alpha_results': []}
            ],
            'cross_paradigm_stats': {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'
            render_markdown_report(sensitivity_summary, output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            assert 'paradigm1' in content
            assert 'paradigm2' in content
            assert 'paradigm3' in content


class TestAlphaConstants:
    """Tests for module-level constants."""

    def test_alpha_values(self):
        """Test that ALPHA_VALUES contains expected thresholds."""
        assert 0.01 in ALPHA_VALUES
        assert 0.05 in ALPHA_VALUES
        assert 0.10 in ALPHA_VALUES
        assert len(ALPHA_VALUES) == 3

    def test_paradigm_count(self):
        """Test that PARADIGMS contains 5 distinct paradigms."""
        assert len(PARADIGMS) == 5
        assert 'ds000030_motor' in PARADIGMS
        assert 'ds000113_working_memory' in PARADIGMS
        assert 'ds000247_language' in PARADIGMS
        assert 'ds000173_emotion' in PARADIGMS
        assert 'ds000205_relational' in PARADIGMS
