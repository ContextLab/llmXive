"""
Tests for the Data Validation Module.

These tests verify that attention check failures and identical response
patterns are correctly identified and flagged for exclusion.
"""

import os
import csv
import json
import tempfile
import pytest
from datetime import datetime

from src.data_validation import (
    load_experimental_results,
    check_attention_failures,
    check_identical_responses,
    validate_and_flag_data,
    DataValidationError
)


@pytest.fixture
def sample_valid_data():
    """Create sample valid experimental data."""
    return [
        {
            'participant_id': 'P001',
            'condition': 'battle',
            'attention_check_1': 'strongly disagree',
            'attention_check_2': 'strongly disagree',
            'cami_avoidance': 2.0,
            'cami_fear': 3.0,
            'cami_segregation': 2.5,
            'cami_benevolence': 4.0,
            'help_seeking_intent': 4.5
        },
        {
            'participant_id': 'P002',
            'condition': 'journey',
            'attention_check_1': 'strongly disagree',
            'attention_check_2': 'strongly disagree',
            'cami_avoidance': 3.0,
            'cami_fear': 2.5,
            'cami_segregation': 3.0,
            'cami_benevolence': 3.5,
            'help_seeking_intent': 4.0
        }
    ]


@pytest.fixture
def sample_attention_failure_data():
    """Create sample data with attention check failures."""
    return [
        {
            'participant_id': 'P003',
            'condition': 'medical',
            'attention_check_1': 'strongly agree',  # Failed!
            'attention_check_2': 'strongly disagree',
            'cami_avoidance': 4.0,
            'cami_fear': 4.5,
            'cami_segregation': 4.0,
            'cami_benevolence': 2.0,
            'help_seeking_intent': 2.5
        }
    ]


@pytest.fixture
def sample_identical_response_data():
    """Create sample data with identical responses."""
    return [
        {
            'participant_id': 'P004',
            'condition': 'battle',
            'attention_check_1': 'strongly disagree',
            'attention_check_2': 'strongly disagree',
            'cami_avoidance': 3.0,
            'cami_fear': 3.0,
            'cami_segregation': 3.0,
            'cami_benevolence': 3.0,
            'help_seeking_intent': 3.0
        }
    ]


def test_load_experimental_results_valid_file(sample_valid_data):
    """Test loading valid experimental results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=sample_valid_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_valid_data)
        temp_path = f.name

    try:
        data = load_experimental_results(temp_path)
        assert len(data) == 2
        assert data[0]['participant_id'] == 'P001'
        assert data[1]['condition'] == 'journey'
    finally:
        os.unlink(temp_path)


def test_load_experimental_results_missing_file():
    """Test loading from a non-existent file raises error."""
    with pytest.raises(DataValidationError):
        load_experimental_results('/nonexistent/path.csv')


def test_load_experimental_results_empty_file():
    """Test loading from an empty file raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('participant_id,condition\n')  # Header only
        temp_path = f.name

    try:
        with pytest.raises(DataValidationError):
            load_experimental_results(temp_path)
    finally:
        os.unlink(temp_path)


def test_check_attention_failures_valid():
    """Test that valid attention checks pass."""
    row = {
        'attention_check_1': 'strongly disagree',
        'attention_check_2': 'strongly disagree'
    }
    failed, checks = check_attention_failures(row)
    assert not failed
    assert len(checks) == 0


def test_check_attention_failures_failure():
    """Test that failed attention checks are detected."""
    row = {
        'attention_check_1': 'strongly agree',
        'attention_check_2': 'strongly disagree'
    }
    failed, checks = check_attention_failures(row)
    assert failed
    assert 'attention_check_1' in checks


def test_check_identical_responses_varied():
    """Test that varied responses are not flagged."""
    row = {
        'cami_avoidance': 2.0,
        'cami_fear': 3.0,
        'cami_segregation': 4.0,
        'cami_benevolence': 2.5,
        'help_seeking_intent': 4.5
    }
    is_identical, similarity = check_identical_responses(row)
    assert not is_identical
    assert similarity < 0.95


def test_check_identical_responses_identical():
    """Test that identical responses are flagged."""
    row = {
        'cami_avoidance': 3.0,
        'cami_fear': 3.0,
        'cami_segregation': 3.0,
        'cami_benevolence': 3.0,
        'help_seeking_intent': 3.0
    }
    is_identical, similarity = check_identical_responses(row)
    assert is_identical
    assert similarity == 1.0


def test_validate_and_flag_data_creates_output(sample_valid_data):
    """Test that validation creates output file with flags."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=sample_valid_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_valid_data)
        input_path = f.name

    output_path = input_path.replace('.csv', '_validated.csv')

    try:
        stats = validate_and_flag_data(input_path, output_path)

        assert os.path.exists(output_path)
        assert stats['total_participants'] == 2
        assert stats['excluded_total'] == 0

        # Verify output file has exclusion columns
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert 'exclude' in rows[0]
            assert 'attention_failed' in rows[0]
            assert 'identical_responses' in rows[0]
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_validate_and_flag_data_excludes_attention_failures(
    sample_attention_failure_data
):
    """Test that attention failures are correctly excluded."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=sample_attention_failure_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_attention_failure_data)
        input_path = f.name

    output_path = input_path.replace('.csv', '_validated.csv')

    try:
        stats = validate_and_flag_data(input_path, output_path)

        assert stats['attention_failures'] == 1
        assert stats['excluded_total'] == 1

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert rows[0]['exclude'] == 'True'
            assert 'attention_check_failure' in rows[0]['exclusion_reason']
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_validate_and_flag_data_excludes_identical_responses(
    sample_identical_response_data
):
    """Test that identical responses are correctly excluded."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=sample_identical_response_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_identical_response_data)
        input_path = f.name

    output_path = input_path.replace('.csv', '_validated.csv')

    try:
        stats = validate_and_flag_data(input_path, output_path)

        assert stats['identical_responses'] == 1
        assert stats['excluded_total'] == 1

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert rows[0]['exclude'] == 'True'
            assert 'identical_responses' in rows[0]['exclusion_reason']
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)