import pytest
from code.utils.metrics import (
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag
)

class TestAvgCommentLength:
    def test_empty_comments(self):
        """Test with empty comments list"""
        result = calculate_avg_comment_length([])
        assert result == 0.0

    def test_single_comment(self):
        """Test with a single comment"""
        comments = [{'body': 'Hello world'}]
        result = calculate_avg_comment_length(comments)
        assert result == 11.0

    def test_multiple_comments(self):
        """Test with multiple comments"""
        comments = [
            {'body': 'Short'},
            {'body': 'This is a longer comment'},
            {'body': 'Medium'}
        ]
        result = calculate_avg_comment_length(comments)
        # (5 + 24 + 6) / 3 = 35 / 3 = 11.666...
        assert abs(result - 11.666) < 0.01

    def test_missing_body_field(self):
        """Test with comments missing body field"""
        comments = [
            {'content': 'Has content'},
            {'other_field': 'No body'}
        ]
        result = calculate_avg_comment_length(comments)
        # Only first comment has valid content
        assert result == 13.0

class TestReviewThreadDepth:
    def test_empty_comments(self):
        """Test with empty review comments list"""
        result = calculate_review_thread_depth([])
        assert result == 0

    def test_single_comment(self):
        """Test with a single review comment"""
        comments = [{'in_reply_to_id': 'thread1'}]
        result = calculate_review_thread_depth(comments)
        assert result == 1

    def test_multiple_threads(self):
        """Test with multiple threads of different depths"""
        comments = [
            {'in_reply_to_id': 'thread1'},
            {'in_reply_to_id': 'thread1'},
            {'in_reply_to_id': 'thread1'},
            {'in_reply_to_id': 'thread2'},
            {'in_reply_to_id': 'thread2'}
        ]
        result = calculate_review_thread_depth(comments)
        # thread1 has 3 comments, thread2 has 2
        assert result == 3

    def test_no_thread_id(self):
        """Test with comments that have no thread ID"""
        comments = [
            {'path': 'file1.py'},
            {'path': 'file1.py'},
            {'path': 'file2.py'}
        ]
        result = calculate_review_thread_depth(comments)
        # Both file1.py comments are in same thread
        assert result == 2

class TestRevertFrequency:
    def test_empty_commits(self):
        """Test with empty commits list"""
        result = calculate_revert_frequency([])
        assert result == 0.0

    def test_no_reverts(self):
        """Test with commits that have no reverts"""
        commits = [
            {'commit': {'message': 'Add feature'}},
            {'commit': {'message': 'Fix bug'}}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 0.0

    def test_all_reverts(self):
        """Test with all commits being reverts"""
        commits = [
            {'commit': {'message': 'Revert "Add feature"'}},
            {'commit': {'message': 'Revert "Fix bug"'}}
        ]
        result = calculate_revert_frequency(commits)
        assert result == 1.0

    def test_mixed_commits(self):
        """Test with mixed revert and non-revert commits"""
        commits = [
            {'commit': {'message': 'Add feature'}},
            {'commit': {'message': 'Revert "Add feature"'}},
            {'commit': {'message': 'Another commit'}},
            {'commit': {'message': 'revert some change'}}
        ]
        result = calculate_revert_frequency(commits)
        # 2 reverts out of 4 commits
        assert result == 0.5

class TestDiffComplexityScore:
    def test_no_deletions(self):
        """Test when lines_deleted is 0"""
        result = calculate_diff_complexity_score(10, 0, 10)
        assert result == 0.0

    def test_zero_total_lines(self):
        """Test when total_lines is 0"""
        result = calculate_diff_complexity_score(0, 0, 0)
        assert result == 0.0

    def test_simple_case(self):
        """Test a simple case"""
        result = calculate_diff_complexity_score(10, 10, 20)
        assert result == 1.0

    def test_partial_complexity(self):
        """Test partial complexity"""
        result = calculate_diff_complexity_score(5, 10, 15)
        assert result == 1.0  # (5+10)/15 = 1.0

    def test_low_complexity(self):
        """Test low complexity case"""
        result = calculate_diff_complexity_score(2, 10, 12)
        assert result == 1.0  # (2+10)/12 = 1.0

class TestIsAiNoiseFlag:
    def test_low_complexity(self):
        """Test with low complexity score"""
        result = is_ai_noise_flag(0.2, 'fix something')
        assert result == False

    def test_high_complexity_no_keyword(self):
        """Test with high complexity but no noise keyword"""
        result = is_ai_noise_flag(0.5, 'add new feature')
        assert result == False

    def test_high_complexity_with_fix(self):
        """Test with high complexity and 'fix' keyword"""
        result = is_ai_noise_flag(0.5, 'fix bug in module')
        assert result == True

    def test_high_complexity_with_hotfix(self):
        """Test with high complexity and 'hotfix' keyword"""
        result = is_ai_noise_flag(0.5, 'hotfix for critical issue')
        assert result == True

    def test_high_complexity_with_patch(self):
        """Test with high complexity and 'patch' keyword"""
        result = is_ai_noise_flag(0.5, 'patch security vulnerability')
        assert result == True

    def test_boundary_case(self):
        """Test at the boundary of complexity threshold"""
        result = is_ai_noise_flag(0.3, 'fix something')
        assert result == False  # Must be > 0.3, not >= 0.3

    def test_case_insensitive(self):
        """Test that keyword matching is case insensitive"""
        result = is_ai_noise_flag(0.5, 'FIX critical issue')
        assert result == True

    def test_keyword_in_middle(self):
        """Test keyword appearing in middle of message"""
        result = is_ai_noise_flag(0.5, 'some fix in the middle')
        assert result == True
