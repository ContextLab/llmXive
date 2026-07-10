"""
Unit tests for the low-complexity filtering utility.

Tests the Shannon entropy calculation and sequence filtering functionality
of code/data/filter_complexity.py.
"""

import pytest
import numpy as np
from pathlib import Path
import json
import tempfile

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.data.filter_complexity import (
    calculate_shannon_entropy,
    filter_sequence_by_entropy,
    filter_manifest_entries,
    load_manifest
)


class TestShannonEntropy:
    """Tests for Shannon entropy calculation."""

    def test_perfectly_repetitive_sequence(self):
        """A sequence of all the same base should have entropy 0."""
        sequence = "AAAAA"
        entropy = calculate_shannon_entropy(sequence)
        assert entropy == 0.0, f"Expected 0.0, got {entropy}"

    def test_perfectly_diverse_sequence(self):
        """A sequence with equal A, C, G, T should have max entropy (normalized to 1.0)."""
        sequence = "ACGTACGT"
        entropy = calculate_shannon_entropy(sequence)
        # Max entropy for 4 bases is 2, normalized to 1.0
        assert abs(entropy - 1.0) < 1e-6, f"Expected ~1.0, got {entropy}"

    def test_empty_sequence(self):
        """Empty sequence should return 0 entropy."""
        entropy = calculate_shannon_entropy("")
        assert entropy == 0.0

    def test_case_insensitivity(self):
        """Entropy calculation should be case-insensitive."""
        upper_seq = "ACGTACGT"
        lower_seq = "acgtacgt"
        mixed_seq = "AcGtAcGt"

        assert calculate_shannon_entropy(upper_seq) == calculate_shannon_entropy(lower_seq)
        assert calculate_shannon_entropy(upper_seq) == calculate_shannon_entropy(mixed_seq)

    def test_non_standard_characters_ignored(self):
        """Non-standard characters (N, etc.) should be ignored in calculation."""
        sequence_with_n = "ACGTNACGT"
        sequence_without_n = "ACGTACGT"
        assert calculate_shannon_entropy(sequence_with_n) == calculate_shannon_entropy(sequence_without_n)

    def test_two_base_sequence(self):
        """A sequence with only 2 bases should have entropy ~0.5 (normalized)."""
        sequence = "AAAAACCCCC"
        entropy = calculate_shannon_entropy(sequence)
        # Two bases with equal frequency: max entropy is 1, normalized to 0.5
        assert abs(entropy - 0.5) < 0.01, f"Expected ~0.5, got {entropy}"


class TestFilterSequenceByEntropy:
    """Tests for the sliding window entropy filtering."""

    def test_high_complexity_sequence(self):
        """A diverse sequence should pass the filter."""
        sequence = "ACGTACGTACGTACGT" * 10
        is_high, min_entropy = filter_sequence_by_entropy(sequence, window_size=20, threshold=0.8)
        assert is_high is True
        assert min_entropy >= 0.8

    def test_low_complexity_sequence(self):
        """A repetitive sequence should fail the filter."""
        sequence = "AAAAA" * 100
        is_high, min_entropy = filter_sequence_by_entropy(sequence, window_size=20, threshold=0.8)
        assert is_high is False
        assert min_entropy < 0.8

    def test_shorter_than_window(self):
        """Sequence shorter than window should be evaluated as a whole."""
        sequence = "ACGT"
        is_high, min_entropy = filter_sequence_by_entropy(sequence, window_size=100, threshold=0.8)
        assert is_high is True  # Max entropy for 4 bases
        assert abs(min_entropy - 1.0) < 1e-6

    def test_mixed_complexity_sequence(self):
        """A sequence with both high and low complexity regions should be filtered."""
        high_comp = "ACGT" * 25
        low_comp = "AAAA" * 25
        mixed = high_comp + low_comp
        is_high, min_entropy = filter_sequence_by_entropy(mixed, window_size=50, threshold=0.8)
        assert is_high is False
        assert min_entropy < 0.8


class TestFilterManifestEntries:
    """Tests for manifest filtering functionality."""

    def test_filter_manifest(self):
        """Test filtering of manifest entries."""
        # Create a temporary manifest
        manifest = {
            'entries': [
                {
                    'accession_id': 'test1',
                    'sequence': 'ACGT' * 100,  # High complexity
                    'cell_type': 'K562'
                },
                {
                    'accession_id': 'test2',
                    'sequence': 'AAAA' * 100,  # Low complexity
                    'cell_type': 'HEK293'
                },
                {
                    'accession_id': 'test3',
                    'sequence': 'ACGTACGT' * 50,  # High complexity
                    'cell_type': 'GM12878'
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest, f)
            temp_path = Path(f.name)

        try:
            filtered_manifest = filter_manifest_entries(
                manifest,
                threshold=0.8,
                output_path=temp_path
            )

            # Check that filtering summary exists
            assert 'filtering_summary' in filtered_manifest
            assert filtered_manifest['filtering_summary']['entries_filtered'] == 1
            assert filtered_manifest['filtering_summary']['entries_retained'] == 2

            # Check that entries have complexity metadata
            for entry in filtered_manifest['entries']:
                assert 'complexity' in entry
                assert 'is_high_complexity' in entry['complexity']
                assert 'min_entropy' in entry['complexity']
                assert 'filtered' in entry['complexity']

            # Verify specific entries
            test1_entry = next(e for e in filtered_manifest['entries'] if e['accession_id'] == 'test1')
            assert test1_entry['complexity']['is_high_complexity'] is True
            assert test1_entry['complexity']['filtered'] is False

            test2_entry = next(e for e in filtered_manifest['entries'] if e['accession_id'] == 'test2')
            assert test2_entry['complexity']['is_high_complexity'] is False
            assert test2_entry['complexity']['filtered'] is True

        finally:
            temp_path.unlink()

    def test_manifest_without_entries(self):
        """Test handling of manifest without 'entries' field."""
        manifest = {'metadata': {'version': '1.0'}}
        result = filter_manifest_entries(manifest, threshold=0.8)
        assert 'filtering_summary' not in result

    def test_manifest_without_sequence_field(self):
        """Test handling of entries without sequence field."""
        manifest = {
            'entries': [
                {'accession_id': 'test1', 'cell_type': 'K562'}
            ]
        }
        result = filter_manifest_entries(manifest, threshold=0.8)
        # Should not crash, just skip the entry
        assert 'filtering_summary' in result
        assert result['filtering_summary']['total_entries_processed'] == 0