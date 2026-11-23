"""
Unit tests for conditional synthesis routing logic.
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from code.analysis.conditional_synthesis import check_sample_size_and_route
from code.analysis.descriptive_synthesis import perform_descriptive_synthesis, format_synthesis_report


@pytest.fixture
def small_studies_csv(tmp_path):
    """Create a CSV with fewer than 10 studies."""
    data = {
        'id': [f'study_{i}' for i in range(5)],
        'title': [f'Study {i}' for i in range(5)],
        'registry': ['ClinicalTrials.gov'] * 5,
        'age_range': [{'min': 8, 'max': 12}] * 5,
        'diagnosis': ['ASD'] * 5,
        'outcomes': [['social skill']] * 5,
        'intervention_components': [['breathing']] * 5,
        'delivery_format': ['caregiver-mediated'] * 5,
        'social_skill_domain': ['communication'] * 5,
        'follow_up': [None] * 5,
        'abstract_text': [None] * 5,
        'blinded_assessment_flag': [True] * 5,
        'rater_type': ['blinded'] * 5
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "small_studies.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def large_studies_csv(tmp_path):
    """Create a CSV with 10 or more studies."""
    data = {
        'id': [f'study_{i}' for i in range(12)],
        'title': [f'Study {i}' for i in range(12)],
        'registry': ['ClinicalTrials.gov'] * 12,
        'age_range': [{'min': 8, 'max': 12}] * 12,
        'diagnosis': ['ASD'] * 12,
        'outcomes': [['social skill']] * 12,
        'intervention_components': [['breathing']] * 12,
        'delivery_format': ['caregiver-mediated'] * 12,
        'social_skill_domain': ['communication'] * 12,
        'follow_up': [None] * 12,
        'abstract_text': [None] * 12,
        'blinded_assessment_flag': [True] * 12,
        'rater_type': ['blinded'] * 12
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "large_studies.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


def test_small_sample_routes_to_descriptive(small_studies_csv, tmp_path):
    """Test that small sample size routes to descriptive synthesis."""
    output_docs = str(tmp_path / "docs")
    
    result = check_sample_size_and_route(small_studies_csv, output_docs, min_sample_size=10)
    
    assert result['n_studies'] == 5
    assert result['route'] == 'descriptive_synthesis'
    assert result['analysis_results']['type'] == 'descriptive_synthesis'
    
    # Verify report file was created
    report_path = Path(output_docs) / "native_synthesis.md"
    assert report_path.exists()
    
    # Verify report content is non-empty
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert len(content) > 0
    assert "Descriptive Synthesis" in content


def test_large_sample_routes_to_meta_analysis(large_studies_csv, tmp_path):
    """Test that large sample size routes to meta-analysis."""
    output_docs = str(tmp_path / "docs")
    
    result = check_sample_size_and_route(large_studies_csv, output_docs, min_sample_size=10)
    
    assert result['n_studies'] == 12
    assert result['route'] == 'meta_analysis'
    assert result['analysis_results']['type'] == 'meta_analysis'
    assert "Meta-analysis path not implemented" in result['analysis_results']['note']


def test_custom_threshold(small_studies_csv, tmp_path):
    """Test with a custom threshold."""
    output_docs = str(tmp_path / "docs")
    
    # With threshold of 5, small sample should route to meta-analysis
    result = check_sample_size_and_route(small_studies_csv, output_docs, min_sample_size=5)
    
    assert result['n_studies'] == 5
    assert result['route'] == 'meta_analysis'


def test_missing_input_file(tmp_path):
    """Test error handling for missing input file."""
    output_docs = str(tmp_path / "docs")
    
    with pytest.raises(FileNotFoundError):
        check_sample_size_and_route("nonexistent.csv", output_docs)