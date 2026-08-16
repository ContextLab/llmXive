"""
Tests for the validate_prompt_orderings script.

These tests verify that the duplicate ordering detection logic works correctly:
- Detects when the same ordering appears across multiple seeds for a strategy
- Allows different orderings for the same strategy across seeds
- Handles edge cases (empty manifest, single entry, etc.)
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_prompt_orderings import (
    load_prompt_manifest,
    extract_ordering_key,
    validate_no_duplicates,
    main
)
from code.src.parser_utils import load_json_file, save_json_file


@pytest.fixture
def sample_manifest_no_duplicates():
    """Sample manifest with unique orderings across seeds."""
    return {
        "entries": [
            {
                "seed": 42,
                "strategy": "Logical Ascending",
                "examples": [
                    {"id": "ex_1"},
                    {"id": "ex_2"},
                    {"id": "ex_3"}
                ]
            },
            {
                "seed": 123,
                "strategy": "Logical Ascending",
                "examples": [
                    {"id": "ex_2"},
                    {"id": "ex_1"},
                    {"id": "ex_3"}  # Different ordering
                ]
            },
            {
                "seed": 456,
                "strategy": "Logical Random",
                "examples": [
                    {"id": "ex_3"},
                    {"id": "ex_1"},
                    {"id": "ex_2"}
                ]
            }
        ]
    }


@pytest.fixture
def sample_manifest_with_duplicates():
    """Sample manifest with duplicate orderings across seeds."""
    return {
        "entries": [
            {
                "seed": 42,
                "strategy": "Logical Ascending",
                "examples": [
                    {"id": "ex_1"},
                    {"id": "ex_2"},
                    {"id": "ex_3"}
                ]
            },
            {
                "seed": 123,
                "strategy": "Logical Ascending",
                "examples": [
                    {"id": "ex_1"},
                    {"id": "ex_2"},
                    {"id": "ex_3"}  # Same ordering as seed 42 - DUPLICATE
                ]
            },
            {
                "seed": 456,
                "strategy": "Logical Random",
                "examples": [
                    {"id": "ex_3"},
                    {"id": "ex_1"},
                    {"id": "ex_2"}
                ]
            }
        ]
    }


@pytest.fixture
def sample_manifest_single_strategy_duplicates():
    """Manifest with multiple duplicates in one strategy."""
    return {
        "entries": [
            {
                "seed": 1,
                "strategy": "Original CDS",
                "examples": [{"id": "a"}, {"id": "b"}]
            },
            {
                "seed": 2,
                "strategy": "Original CDS",
                "examples": [{"id": "a"}, {"id": "b"}]  # Duplicate
            },
            {
                "seed": 3,
                "strategy": "Original CDS",
                "examples": [{"id": "a"}, {"id": "b"}]  # Duplicate
            },
            {
                "seed": 4,
                "strategy": "Logical Ascending",
                "examples": [{"id": "x"}, {"id": "y"}]
            }
        ]
    }


@pytest.fixture
def temp_manifest_file(sample_manifest_no_duplicates):
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False
    ) as f:
        json.dump(sample_manifest_no_duplicates, f)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


def test_extract_ordering_key_basic():
    """Test that ordering key extraction works correctly."""
    entry = {
        "seed": 42,
        "strategy": "Logical Ascending",
        "examples": [{"id": "ex_1"}, {"id": "ex_2"}]
    }
    
    strategy, ordering_sig, seed = extract_ordering_key(entry)
    
    assert strategy == "Logical Ascending"
    assert seed == 42
    assert ordering_sig == ("ex_1", "ex_2")


def test_extract_ordering_key_with_hash():
    """Test ordering key extraction when examples have hashes instead of IDs."""
    entry = {
        "seed": 99,
        "strategy": "Logical Random",
        "examples": [{"hash": "abc123"}, {"hash": "def456"}]
    }
    
    strategy, ordering_sig, seed = extract_ordering_key(entry)
    
    assert strategy == "Logical Random"
    assert seed == 99
    assert ordering_sig == ("abc123", "def456")


def test_validate_no_duplicates_passes(sample_manifest_no_duplicates):
    """Test validation passes when there are no duplicates."""
    is_valid, duplicates = validate_no_duplicates(sample_manifest_no_duplicates)
    
    assert is_valid is True
    assert len(duplicates) == 0


def test_validate_no_duplicates_fails(sample_manifest_with_duplicates):
    """Test validation fails when duplicates are found."""
    is_valid, duplicates = validate_no_duplicates(sample_manifest_with_duplicates)
    
    assert is_valid is False
    assert len(duplicates) == 1
    
    # Check the duplicate details
    dup = duplicates[0]
    assert dup['strategy'] == "Logical Ascending"
    assert dup['count'] == 2
    assert len(dup['occurrences']) == 2
    
    # Check that the seeds are reported correctly
    seeds = [occ['seed'] for occ in dup['occurrences']]
    assert 42 in seeds
    assert 123 in seeds


def test_validate_multiple_duplicates(sample_manifest_single_strategy_duplicates):
    """Test validation handles multiple duplicates in the same strategy."""
    is_valid, duplicates = validate_no_duplicates(sample_manifest_single_strategy_duplicates)
    
    assert is_valid is False
    assert len(duplicates) == 1  # One ordering signature repeated
    
    dup = duplicates[0]
    assert dup['strategy'] == "Original CDS"
    assert dup['count'] == 3  # Appears 3 times


def test_validate_empty_manifest():
    """Test validation handles empty manifest."""
    empty_manifest = {"entries": []}
    is_valid, duplicates = validate_no_duplicates(empty_manifest)
    
    assert is_valid is True
    assert len(duplicates) == 0


def test_validate_single_entry():
    """Test validation with a single entry (no possibility of duplicates)."""
    single_entry = {
        "entries": [
            {
                "seed": 42,
                "strategy": "Logical Ascending",
                "examples": [{"id": "ex_1"}]
            }
        ]
    }
    
    is_valid, duplicates = validate_no_duplicates(single_entry)
    
    assert is_valid is True
    assert len(duplicates) == 0


def test_validate_different_strategies_same_ordering():
    """Test that same ordering in different strategies is not flagged as duplicate."""
    manifest = {
        "entries": [
            {
                "seed": 42,
                "strategy": "Logical Ascending",
                "examples": [{"id": "ex_1"}, {"id": "ex_2"}]
            },
            {
                "seed": 123,
                "strategy": "Logical Random",
                "examples": [{"id": "ex_1"}, {"id": "ex_2"}]  # Same ordering, different strategy
            }
        ]
    }
    
    is_valid, duplicates = validate_no_duplicates(manifest)
    
    assert is_valid is True  # Different strategies, so not a duplicate
    assert len(duplicates) == 0


def test_main_success(temp_manifest_file):
    """Test main function with valid manifest (no duplicates)."""
    output_path = temp_manifest_file.parent / "test_report.json"
    
    with patch('sys.argv', [
        'validate_prompt_orderings.py',
        '--manifest', str(temp_manifest_file),
        '--output', str(output_path)
    ]):
        main()
    
    assert output_path.exists()
    
    # Verify report content
    report = load_json_file(output_path)
    assert report['validation_status'] == 'passed'
    assert report['duplicate_count'] == 0
    
    output_path.unlink()


def test_main_with_duplicates(temp_manifest_file, sample_manifest_with_duplicates):
    """Test main function detects duplicates."""
    # Overwrite temp file with duplicate data
    with open(temp_manifest_file, 'w') as f:
        json.dump(sample_manifest_with_duplicates, f)
    
    output_path = temp_manifest_file.parent / "test_report_dup.json"
    
    with patch('sys.argv', [
        'validate_prompt_orderings.py',
        '--manifest', str(temp_manifest_file),
        '--output', str(output_path)
    ]):
        main()
    
    assert output_path.exists()
    
    report = load_json_file(output_path)
    assert report['validation_status'] == 'failed'
    assert report['duplicate_count'] == 1
    
    output_path.unlink()


def test_main_fail_on_duplicate_flag(temp_manifest_file, sample_manifest_with_duplicates):
    """Test main function exits with code 1 when --fail-on-duplicate is set."""
    # Overwrite temp file with duplicate data
    with open(temp_manifest_file, 'w') as f:
        json.dump(sample_manifest_with_duplicates, f)
    
    output_path = temp_manifest_file.parent / "test_report_fail.json"
    
    with patch('sys.argv', [
        'validate_prompt_orderings.py',
        '--manifest', str(temp_manifest_file),
        '--output', str(output_path),
        '--fail-on-duplicate'
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    output_path.unlink()
    temp_manifest_file.unlink()
