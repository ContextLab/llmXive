"""
Unit tests for extract_metrics.py
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import csv
import tempfile
import os

from data.extract_metrics import (
    parse_timestamp,
    calculate_time_to_merge_minutes,
    calculate_review_cycles,
    extract_comment_count,
    extract_pr_metrics,
    load_prs_labeled,
    load_complexity_scores,
    join_and_save_metrics
)

class TestTimestampParsing:
    def test_parse_iso_with_z(self):
        """Test parsing ISO timestamp with Z suffix."""
        result = parse_timestamp("2023-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_with_timezone(self):
        """Test parsing ISO timestamp with timezone offset."""
        result = parse_timestamp("2023-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2023

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_timestamp("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None."""
        result = parse_timestamp(None)
        assert result is None

class TestTimeToMerge:
    def test_calculate_time_to_merge(self):
        """Test time to merge calculation."""
        created = "2023-01-15T10:00:00Z"
        merged = "2023-01-15T12:30:00Z"
        result = calculate_time_to_merge_minutes(created, merged)
        assert result == 150.0  # 2.5 hours = 150 minutes

    def test_time_to_merge_not_merged(self):
        """Test time to merge returns None if not merged."""
        created = "2023-01-15T10:00:00Z"
        result = calculate_time_to_merge_minutes(created, None)
        assert result is None

    def test_time_to_merge_invalid_timestamps(self):
        """Test time to merge returns None for invalid timestamps."""
        result = calculate_time_to_merge_minutes("invalid", "also_invalid")
        assert result is None

class TestReviewCycles:
    def test_no_reviews(self):
        """Test review cycles with no reviews."""
        result = calculate_review_cycles([])
        assert result == 0

    def test_single_review(self):
        """Test review cycles with single review."""
        reviews = [{'submitted_at': '2023-01-15T10:00:00Z'}]
        result = calculate_review_cycles(reviews)
        assert result == 1

    def test_multiple_reviews_same_cycle(self):
        """Test multiple reviews within same cycle (< 1 hour gap)."""
        reviews = [
            {'submitted_at': '2023-01-15T10:00:00Z'},
            {'submitted_at': '2023-01-15T10:30:00Z'},
            {'submitted_at': '2023-01-15T10:45:00Z'}
        ]
        result = calculate_review_cycles(reviews)
        assert result == 1

    def test_multiple_reviews_different_cycles(self):
        """Test reviews spanning multiple cycles (> 1 hour gap)."""
        reviews = [
            {'submitted_at': '2023-01-15T10:00:00Z'},
            {'submitted_at': '2023-01-15T12:00:00Z'},  # 2 hours later
            {'submitted_at': '2023-01-15T14:30:00Z'}   # 2.5 hours later
        ]
        result = calculate_review_cycles(reviews)
        assert result == 3

class TestCommentCount:
    def test_empty_comments(self):
        """Test comment count with empty list."""
        result = extract_comment_count([])
        assert result == 0

    def test_multiple_comments(self):
        """Test comment count with multiple comments."""
        comments = [{'id': 1}, {'id': 2}, {'id': 3}]
        result = extract_comment_count(comments)
        assert result == 3

class TestExtractPrMetrics:
    def test_extract_basic_metrics(self):
        """Test extraction of basic PR metrics."""
        pr = {
            'pr_id': 123,
            'created_at': '2023-01-15T10:00:00Z',
            'merged_at': '2023-01-15T12:00:00Z',
            'comments': [{'id': 1}, {'id': 2}],
            'reviews': [
                {'submitted_at': '2023-01-15T11:00:00Z'},
                {'submitted_at': '2023-01-15T11:30:00Z'}
            ]
        }
        result = extract_pr_metrics(pr)
        
        assert result is not None
        assert result['pr_id'] == 123
        assert result['comment_count'] == 2
        assert result['time_to_merge_minutes'] == 120.0
        assert result['review_cycles'] == 1

    def test_extract_missing_pr_id(self):
        """Test extraction returns None when pr_id is missing."""
        pr = {
            'created_at': '2023-01-15T10:00:00Z',
            'merged_at': '2023-01-15T12:00:00Z'
        }
        result = extract_pr_metrics(pr)
        assert result is None

class TestLoadData:
    def test_load_prs_labeled(self):
        """Test loading labeled PRs from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id', 'source_type'])
            writer.writeheader()
            writer.writerow({'pr_id': '1', 'source_type': 'llm'})
            writer.writerow({'pr_id': '2', 'source_type': 'human'})
            temp_path = f.name

        try:
            prs = load_prs_labeled(temp_path)
            assert len(prs) == 2
            assert prs[0]['pr_id'] == 1
            assert prs[1]['pr_id'] == 2
        finally:
            os.unlink(temp_path)

    def test_load_complexity_scores(self):
        """Test loading complexity scores from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['pr_id', 'complexity_score'])
            writer.writeheader()
            writer.writerow({'pr_id': '1', 'complexity_score': '15.5'})
            writer.writerow({'pr_id': '2', 'complexity_score': '22.3'})
            temp_path = f.name

        try:
            scores = load_complexity_scores(temp_path)
            assert len(scores) == 2
            assert scores[1] == 15.5
            assert scores[2] == 22.3
        finally:
            os.unlink(temp_path)

class TestJoinAndSave:
    def test_join_and_save_metrics(self):
        """Test joining labeled PRs with complexity scores and saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create labeled PRs file
            labeled_path = os.path.join(tmpdir, 'prs_labeled.csv')
            with open(labeled_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['pr_id', 'source_type', 'created_at', 'merged_at', 'comments', 'reviews'])
                writer.writeheader()
                writer.writerow({
                    'pr_id': '1',
                    'source_type': 'llm',
                    'created_at': '2023-01-15T10:00:00Z',
                    'merged_at': '2023-01-15T12:00:00Z',
                    'comments': json.dumps([{'id': 1}]),
                    'reviews': json.dumps([{'submitted_at': '2023-01-15T11:00:00Z'}])
                })
                writer.writerow({
                    'pr_id': '2',
                    'source_type': 'human',
                    'created_at': '2023-01-15T09:00:00Z',
                    'merged_at': '2023-01-15T15:00:00Z',
                    'comments': json.dumps([{'id': 1}, {'id': 2}]),
                    'reviews': json.dumps([{'submitted_at': '2023-01-15T10:00:00Z'}])
                })

            # Create complexity scores file
            complexity_path = os.path.join(tmpdir, 'complexity_scores.csv')
            with open(complexity_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['pr_id', 'complexity_score'])
                writer.writeheader()
                writer.writerow({'pr_id': '1', 'complexity_score': '15.5'})
                writer.writerow({'pr_id': '2', 'complexity_score': '22.3'})

            # Output path
            output_path = os.path.join(tmpdir, 'prs_metrics.csv')

            # Run join and save
            join_and_save_metrics(labeled_path, complexity_path, output_path)

            # Verify output
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]['pr_id'] == '1'
            assert rows[0]['comment_count'] == '1'
            assert rows[0]['time_to_merge_minutes'] == '120.0'
            assert rows[0]['complexity_score'] == '15.5'
            assert rows[1]['pr_id'] == '2'
            assert rows[1]['comment_count'] == '2'
            assert rows[1]['time_to_merge_minutes'] == '360.0'
            assert rows[1]['complexity_score'] == '22.3'