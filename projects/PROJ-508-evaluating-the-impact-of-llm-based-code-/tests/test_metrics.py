"""
Tests for metrics calculation functions.
"""
import pytest
from code.utils.metrics import (
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag
)


class TestAvgCommentLength:
    """Tests for calculate_avg_comment_length function."""

    def test_empty_comments(self):
        """Test with empty comment list."""
        result = calculate_avg_comment_length([])
        assert result == 0.0

    def test_single_comment(self):
        """Test with a single comment."""
        comments = [{'body': 'Hello world'}]
        result = calculate_avg_comment_length(comments)
        assert result == 11.0  # len('Hello world')

    def test_multiple_comments(self):
        """Test with multiple comments."""
        comments = [
            {'body': 'Short'},
            {'body': 'This is a longer comment'},
            {'body': 'Hi'}
        ]
        result = calculate_avg_comment_length(comments)
        expected = (5 + 24 + 2) / 3
        assert result == expected

    def test_missing_body_field(self):
        """Test with comments missing body field."""
        comments = [{'text': 'Using text field'}]
        result = calculate_avg_comment_length(comments)
        assert result == 16.0

    def test_empty_body(self):
        """Test with empty body."""
        comments = [{'body': ''}]
        result = calculate_avg_comment_length(comments)
        assert result == 0.0


class TestReviewThreadDepth:
    """Tests for calculate_review_thread_depth function."""

    def test_empty_threads(self):
        """Test with empty thread list."""
        result = calculate_review_thread_depth([])
        assert result == 0

    def test_single_thread_single_comment(self):
        """Test with a single thread containing one comment."""
        threads = [{'comments': [{'id': 1}]}]
        result = calculate_review_thread_depth(threads)
        assert result == 1

    def test_single_thread_multiple_comments(self):
        """Test with a single thread containing multiple comments."""
        threads = [{'comments': [{'id': 1}, {'id': 2}, {'id': 3}]}]
        result = calculate_review_thread_depth(threads)
        assert result == 3

    def test_multiple_threads(self):
        """Test with multiple threads of varying depths."""
        threads = [
            {'comments': [{'id': 1}]},
            {'comments': [{'id': 2}, {'id': 3}]},
            {'comments': [{'id': 4}, {'id': 5}, {'id': 6}, {'id': 7}]}
        ]
        result = calculate_review_thread_depth(threads)
        assert result == 4

    def test_missing_comments_field(self):
        """Test with threads missing comments field."""
        threads = [{} , {'review_comments': [{'id': 1}]}]
        result = calculate_review_thread_depth(threads)
        assert result == 1


class TestRevertFrequency:
    """Tests for calculate_revert_frequency function."""

    def test_empty_commits(self):
        """Test with empty commit list."""
        result = calculate_revert_frequency([])
        assert result == 0.0

    def test_no_reverts(self):
        """Test with commits that are not reverts."""
        commits = [
            {'message': 'Add feature'},
            {'message': 'Fix bug'},
            {'message': 'Update docs'}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 0.0

    def test_all_reverts(self):
        """Test with all commits being reverts."""
        commits = [
            {'message': 'Revert "Add feature"'},
            {'message': 'Revert: Fix bug'},
            {'message': 'revert update'}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 1.0

    def test_mixed_commits(self):
        """Test with mixed revert and non-revert commits."""
        commits = [
            {'message': 'Add feature'},
            {'message': 'Revert "Add feature"'},
            {'message': 'Fix bug'},
            {'message': 'Revert: Fix bug'}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 0.5

    def test_case_insensitive(self):
        """Test that revert detection is case insensitive."""
        commits = [
            {'message': 'REVERT "Add feature"'},
            {'message': 'Revert "Fix bug"'},
            {'message': 'revert docs'}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 1.0


class TestDiffComplexityScore:
    """Tests for calculate_diff_complexity_score function."""

    def test_no_deletions(self):
        """Test with no deletions."""
        result = calculate_diff_complexity_score(10, 0, 100)
        assert result == 0.0

    def test_valid_score(self):
        """Test with valid additions and deletions."""
        result = calculate_diff_complexity_score(10, 10, 100)
        assert result == 0.2

    def test_high_score(self):
        """Test with high complexity score."""
        result = calculate_diff_complexity_score(50, 50, 100)
        assert result == 1.0

    def test_zero_total_lines(self):
        """Test with zero total lines."""
        result = calculate_diff_complexity_score(10, 10, 0)
        assert result == 0.0


class TestAINoiseFlag:
    """Tests for is_ai_noise_flag function."""

    def test_low_complexity(self):
        """Test with low complexity score."""
        result = is_ai_noise_flag(0.2, 'fix bug')
        assert result is False

    def test_high_complexity_no_keyword(self):
        """Test with high complexity but no noise keyword."""
        result = is_ai_noise_flag(0.4, 'add feature')
        assert result is False

    def test_high_complexity_fix_keyword(self):
        """Test with high complexity and fix keyword."""
        result = is_ai_noise_flag(0.4, 'fix bug')
        assert result is True

    def test_high_complexity_hotfix_keyword(self):
        """Test with high complexity and hotfix keyword."""
        result = is_ai_noise_flag(0.4, 'hotfix critical issue')
        assert result is True

    def test_high_complexity_patch_keyword(self):
        """Test with high complexity and patch keyword."""
        result = is_ai_noise_flag(0.4, 'patch vulnerability')
        assert result is True

    def test_boundary_complexity(self):
        """Test at boundary complexity score."""
        result = is_ai_noise_flag(0.3, 'fix bug')
        assert result is False  # Must be > 0.3, not >=

    def test_boundary_complexity_plus(self):
        """Test just above boundary complexity score."""
        result = is_ai_noise_flag(0.31, 'fix bug')
        assert result is True
