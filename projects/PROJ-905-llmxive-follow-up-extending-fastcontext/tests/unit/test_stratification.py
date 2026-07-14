"""
Unit tests for the stratification module.
"""
import pytest
import csv
import tempfile
from pathlib import Path
import sys

# Ensure we can import from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stratification import split_repos, load_scores_from_csv, save_sets_to_csv


class TestSplitRepos:
    """Tests for the split_repos function."""

    def test_empty_input(self):
        """Test that empty input returns empty lists."""
        regular, irregular = split_repos([])
        assert regular == []
        assert irregular == []

    def test_single_item(self):
        """Test splitting a single item (all goes to irregular if median split)."""
        data = [{'repo_id': 'repo1', 'regularity_score': 0.9}]
        regular, irregular = split_repos(data)
        # With 1 item, mid_point = 0, so all go to irregular
        assert len(regular) == 0
        assert len(irregular) == 1
        assert irregular[0]['repo_id'] == 'repo1'

    def test_two_items_equal_split(self):
        """Test splitting two items."""
        data = [
            {'repo_id': 'repo1', 'regularity_score': 0.9},
            {'repo_id': 'repo2', 'regularity_score': 0.1}
        ]
        regular, irregular = split_repos(data)
        assert len(regular) == 1
        assert len(irregular) == 1
        assert regular[0]['repo_id'] == 'repo1'
        assert irregular[0]['repo_id'] == 'repo2'

    def test_uneven_split_rounding(self):
        """Test that odd number of items rounds correctly (floor for regular)."""
        data = [
            {'repo_id': 'r1', 'regularity_score': 0.9},
            {'repo_id': 'r2', 'regularity_score': 0.8},
            {'repo_id': 'r3', 'regularity_score': 0.1}
        ]
        regular, irregular = split_repos(data)
        # 3 items -> mid = 1 -> 1 regular, 2 irregular
        assert len(regular) == 1
        assert len(irregular) == 2
        assert regular[0]['repo_id'] == 'r1'

    def test_explicit_threshold(self):
        """Test splitting using an explicit threshold."""
        data = [
            {'repo_id': 'r1', 'regularity_score': 0.9},
            {'repo_id': 'r2', 'regularity_score': 0.5},
            {'repo_id': 'r3', 'regularity_score': 0.4}
        ]
        # Threshold at 0.6
        regular, irregular = split_repos(data, threshold=0.6)
        assert len(regular) == 1
        assert len(irregular) == 2
        assert regular[0]['repo_id'] == 'r1'

    def test_threshold_includes_equal(self):
        """Test that threshold is inclusive for regular set."""
        data = [
            {'repo_id': 'r1', 'regularity_score': 0.5},
            {'repo_id': 'r2', 'regularity_score': 0.5}
        ]
        regular, irregular = split_repos(data, threshold=0.5)
        # Both should be regular
        assert len(regular) == 2
        assert len(irregular) == 0

    def test_sorting_order(self):
        """Test that the regular set contains the highest scores."""
        data = [
            {'repo_id': 'r1', 'regularity_score': 0.3},
            {'repo_id': 'r2', 'regularity_score': 0.9},
            {'repo_id': 'r3', 'regularity_score': 0.5},
            {'repo_id': 'r4', 'regularity_score': 0.8}
        ]
        regular, irregular = split_repos(data)
        # Sorted: 0.9, 0.8, 0.5, 0.3
        # Regular: 0.9, 0.8
        scores_regular = [r['regularity_score'] for r in regular]
        scores_irregular = [r['regularity_score'] for r in irregular]

        assert min(scores_regular) >= max(scores_irregular)


class TestLoadScoresFromCsv:
    """Tests for loading scores from CSV."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['repo_id', 'regularity_score'])
            writer.writerow(['repo1', '0.9'])
            writer.writerow(['repo2', '0.1'])
            temp_path = Path(f.name)

        try:
            data = load_scores_from_csv(temp_path)
            assert len(data) == 2
            assert data[0]['repo_id'] == 'repo1'
            assert data[0]['regularity_score'] == 0.9
            assert data[1]['regularity_score'] == 0.1
        finally:
            temp_path.unlink()

    def test_load_invalid_score_defaults_to_zero(self):
        """Test that invalid scores default to 0.0."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['repo_id', 'regularity_score'])
            writer.writerow(['repo1', 'invalid'])
            temp_path = Path(f.name)

        try:
            data = load_scores_from_csv(temp_path)
            assert len(data) == 1
            assert data[0]['regularity_score'] == 0.0
        finally:
            temp_path.unlink()


class TestSaveSetsToCsv:
    """Tests for saving sets to CSV."""

    def test_save_empty_sets(self):
        """Test saving empty sets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            regular_path, irregular_path = save_sets_to_csv([], [], output_dir)

            assert regular_path.exists()
            assert irregular_path.exists()

            # Check headers exist
            with open(regular_path) as f:
                reader = csv.reader(f)
                header = next(reader)
                assert 'repo_id' in header

    def test_save_populated_sets(self):
        """Test saving populated sets."""
        regular_data = [
            {'repo_id': 'r1', 'regularity_score': 0.9, 'extra_field': 'val1'}
        ]
        irregular_data = [
            {'repo_id': 'r2', 'regularity_score': 0.1, 'extra_field': 'val2'}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            regular_path, irregular_path = save_sets_to_csv(regular_data, irregular_data, output_dir)

            assert regular_path.exists()
            assert irregular_path.exists()

            # Verify content
            with open(regular_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['repo_id'] == 'r1'
                assert rows[0]['extra_field'] == 'val1'

            with open(irregular_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['repo_id'] == 'r2'