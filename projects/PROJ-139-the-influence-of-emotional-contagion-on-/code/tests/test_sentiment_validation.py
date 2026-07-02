"""
Tests for T014: VADER validation against human-annotated corpus.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from data.sentiment import (
    load_annotated_corpus,
    apply_vader_sentiment,
    validate_vader_against_corpus,
    main
)


@pytest.fixture
def sample_annotations():
    """Create sample annotated corpus data."""
    return pd.DataFrame({
        'text': [
            'I love this product!',
            'This is terrible.',
            'It is okay I guess.',
            'Absolutely fantastic experience!',
            'Worst purchase ever made.'
        ],
        'label': [
            'positive',
            'negative',
            'neutral',
            'positive',
            'negative'
        ]
    })


@pytest.fixture
def temp_corpus_file(sample_annotations, tmp_path):
    """Create a temporary annotations.json file."""
    corpus_path = tmp_path / 'annotations.json'
    sample_annotations.to_json(corpus_path, orient='records')
    return corpus_path


@pytest.fixture
def temp_report_file(tmp_path):
    """Create a temporary validation report with Kappa stats."""
    report_path = tmp_path / 'vader_validation_report.json'
    report = {
        'kappa': 0.85,
        'annotators': 2,
        'sample_size': 100
    }
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return report_path


def test_load_annotated_corpus_success(temp_corpus_file, sample_annotations):
    """Test loading annotations from JSON file."""
    df = load_annotated_corpus(temp_corpus_file)
    assert len(df) == len(sample_annotations)
    assert 'text' in df.columns
    assert 'label' in df.columns


def test_load_annotated_corpus_missing_file(tmp_path):
    """Test that missing corpus raises FileNotFoundError."""
    missing_path = tmp_path / 'nonexistent.json'
    with pytest.raises(FileNotFoundError):
        load_annotated_corpus(missing_path)


def test_load_annotated_corpus_missing_columns(tmp_path):
    """Test that missing required columns raises ValueError."""
    corpus_path = tmp_path / 'bad_annotations.json'
    data = pd.DataFrame({'text': ['hello']})  # Missing 'label'
    data.to_json(corpus_path, orient='records')

    with pytest.raises(ValueError, match="must contain columns"):
        load_annotated_corpus(corpus_path)


def test_apply_vader_sentiment(sample_annotations):
    """Test that VADER sentiment is applied correctly."""
    df = apply_vader_sentiment(sample_annotations, text_col='text')

    assert 'vader_compound' in df.columns
    assert 'vader_pos' in df.columns
    assert 'vader_neu' in df.columns
    assert 'vader_neg' in df.columns

    # Check compound scores are within valid range [-1, 1]
    assert df['vader_compound'].min() >= -1.0
    assert df['vader_compound'].max() <= 1.0


def test_apply_vader_sentiment_empty_text(sample_annotations):
    """Test handling of empty text."""
    sample_annotations.loc[0, 'text'] = ''
    df = apply_vader_sentiment(sample_annotations, text_col='text')

    # Empty text should result in neutral scores (0, 0, 0, 0)
    assert df.loc[0, 'vader_compound'] == 0.0
    assert df.loc[0, 'vader_pos'] == 0.0


def test_validate_vader_missing_report(tmp_path, sample_annotations):
    """Test that missing report file raises error."""
    corpus_path = tmp_path / 'annotations.json'
    sample_annotations.to_json(corpus_path, orient='records')

    report_path = tmp_path / 'missing_report.json'

    with pytest.raises(FileNotFoundError, match="T007b must complete"):
        validate_vader_against_corpus(sample_annotations, report_path)


def test_validate_vader_missing_kappa(tmp_path, sample_annotations):
    """Test that report without Kappa raises error."""
    corpus_path = tmp_path / 'annotations.json'
    sample_annotations.to_json(corpus_path, orient='records')

    report_path = tmp_path / 'no_kappa_report.json'
    with open(report_path, 'w') as f:
        json.dump({'some_key': 'value'}, f)

    with pytest.raises(ValueError, match="Kappa statistics missing"):
        validate_vader_against_corpus(sample_annotations, report_path)


def test_validate_vader_success(tmp_path, sample_annotations, temp_report_file):
    """Test successful VADER validation and report update."""
    corpus_path = tmp_path / 'annotations.json'
    sample_annotations.to_json(corpus_path, orient='records')

    report = validate_vader_against_corpus(
        sample_annotations,
        temp_report_file,
        label_col='label'
    )

    # Verify report was updated
    assert 'vader_validation' in report
    assert report['validation_status'] == 'complete'
    assert 'kappa_vs_human' in report['vader_validation']
    assert 'agreement_rate' in report['vader_validation']

    # Verify file was written
    assert temp_report_file.exists()
    with open(temp_report_file, 'r') as f:
        updated_report = json.load(f)
    assert 'vader_validation' in updated_report


def test_main_integration(tmp_path, sample_annotations, temp_report_file, monkeypatch):
    """Test the main function integration."""
    # Mock get_config to use our temp paths
    class MockPaths:
        raw = tmp_path
        processed = tmp_path

    class MockConfig:
        data_paths = MockPaths()

    def mock_get_config():
        return MockConfig()

    monkeypatch.setattr('data.sentiment.get_config', mock_get_config)

    # Save annotations to expected location
    corpus_path = tmp_path / 'annotations.json'
    sample_annotations.to_json(corpus_path, orient='records')

    # Run main
    with patch('data.sentiment.get_logger') as mock_logger:
        main()

    # Verify report was created
    report_path = tmp_path / 'vader_validation_report.json'
    assert report_path.exists()