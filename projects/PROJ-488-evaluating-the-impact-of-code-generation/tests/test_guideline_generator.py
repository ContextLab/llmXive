"""
Tests for the guideline_generator module.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from guideline_generator import (
    load_statistical_results,
    determine_recommendation,
    generate_guidelines_content,
    run_guideline_generation,
    SIGNIFICANCE_THRESHOLD,
    EFFECT_SIZE_THRESHOLD
)

@pytest.fixture
def temp_metrics_dir(tmp_path):
    """Create a temporary directory with mock statistical results."""
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()

    # Create mock Mann-Whitney U results
    mw_data = {
        'cyclomatic_complexity': {'p_value': 0.01, 'u_statistic': 1500.0},
        'maintainability_index': {'p_value': 0.03, 'u_statistic': 2200.0},
        'potential_bugs': {'p_value': 0.45, 'u_statistic': 3000.0}
    }
    with open(metrics_dir / "mann_whitney_u_results.json", 'w') as f:
        json.dump(mw_data, f)

    # Create mock Cliff's delta results
    cd_data = {
        'cyclomatic_complexity': {'cliffs_delta': 0.25, 'magnitude': 'medium'},
        'maintainability_index': {'cliffs_delta': -0.15, 'magnitude': 'small'},
        'potential_bugs': {'cliffs_delta': 0.05, 'magnitude': 'negligible'}
    }
    with open(metrics_dir / "cliffs_delta_results.json", 'w') as f:
        json.dump(cd_data, f)

    # Create mock BH corrected results
    bh_data = {
        'cyclomatic_complexity': {'adjusted_p_value': 0.015},
        'maintainability_index': {'adjusted_p_value': 0.04},
        'potential_bugs': {'adjusted_p_value': 0.5}
    }
    with open(metrics_dir / "bh_corrected_results.json", 'w') as f:
        json.dump(bh_data, f)

    return metrics_dir

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    return output_dir

def test_load_statistical_results(temp_metrics_dir):
    """Test loading statistical results from mock files."""
    results = load_statistical_results(temp_metrics_dir)

    assert 'cyclomatic_complexity' in results
    assert results['cyclomatic_complexity']['raw_p_value'] == 0.01
    assert results['cyclomatic_complexity']['cliffs_delta'] == 0.25
    assert results['cyclomatic_complexity']['adjusted_p_value'] == 0.015

    assert 'maintainability_index' in results
    assert results['maintainability_index']['magnitude'] == 'small'

    assert 'potential_bugs' in results
    assert results['potential_bugs']['adjusted_p_value'] == 0.5

def test_determine_recommendation_higher_complexity():
    """Test recommendation generation for higher complexity."""
    rec = determine_recommendation('cyclomatic_complexity', 0.25, 'medium')
    assert 'higher cyclomatic complexity' in rec.lower()
    assert 'complexity budgets' in rec.lower()

def test_determine_recommendation_lower_complexity():
    """Test recommendation generation for lower complexity."""
    rec = determine_recommendation('cyclomatic_complexity', -0.25, 'medium')
    assert 'lower cyclomatic complexity' in rec.lower()
    assert 'over-simplification' in rec.lower()

def test_determine_recommendation_higher_bugs():
    """Test recommendation generation for higher potential bugs."""
    rec = determine_recommendation('potential_bugs', 0.3, 'large')
    assert 'higher potential bug indicators' in rec.lower()
    assert 'mandatory security' in rec.lower()

def test_determine_recommendation_unknown_metric():
    """Test recommendation for an unknown metric."""
    rec = determine_recommendation('unknown_metric', 0.2, 'small')
    assert 'unknown_metric' in rec
    assert 'manual review' in rec.lower()

def test_generate_guidelines_content_with_significant_metrics(temp_metrics_dir, temp_output_dir):
    """Test generating guidelines content with significant metrics."""
    results = load_statistical_results(temp_metrics_dir)
    content = generate_guidelines_content(results)

    assert '# Code Review Guidelines' in content
    assert 'Executive Summary' in content
    assert 'cyclomatic_complexity' in content
    assert 'maintainability_index' in content
    assert 'Detailed Guidelines' in content
    assert 'Implementation Checklist' in content

def test_generate_guidelines_content_no_significant_metrics(temp_output_dir):
    """Test generating guidelines when no metrics are significant."""
    results = {
        'metric_a': {'adjusted_p_value': 0.5, 'cliffs_delta': 0.01, 'magnitude': 'negligible'}
    }
    content = generate_guidelines_content(results)

    assert 'No metrics showed statistically significant differences' in content
    assert 'General Recommendations' in content

def test_run_guideline_generation(temp_metrics_dir, temp_output_dir, caplog):
    """Test the full guideline generation workflow."""
    output_path = temp_output_dir / "guidelines.md"

    success, message = run_guideline_generation(
        metrics_dir=temp_metrics_dir,
        output_path=output_path
    )

    assert success is True
    assert output_path.exists()

    with open(output_path, 'r') as f:
        content = f.read()
        assert 'Code Review Guidelines' in content
        assert 'cyclomatic_complexity' in content

def test_run_guideline_generation_missing_files(temp_output_dir, caplog):
    """Test guideline generation when statistical files are missing."""
    empty_dir = temp_output_dir / "empty_metrics"
    empty_dir.mkdir()
    output_path = temp_output_dir / "guidelines_empty.md"

    success, message = run_guideline_generation(
        metrics_dir=empty_dir,
        output_path=output_path
    )

    assert success is True
    assert output_path.exists()
    assert 'No statistical results found' in message or 'No metrics showed statistically significant' in open(output_path).read()