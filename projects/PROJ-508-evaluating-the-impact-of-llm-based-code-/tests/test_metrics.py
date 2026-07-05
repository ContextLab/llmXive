import pytest
from code.utils.metrics import (
    calculate_iteration_count,
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity,
    process_review_metrics
)

class TestIterationCount:
    def test_count_commits(self):
        pr_data = {'commits': [{'sha': 'abc'}, {'sha': 'def'}, {'sha': 'ghi'}]}
        assert calculate_iteration_count(pr_data) == 3

    def test_count_push_events(self):
        pr_data = {'push_events': [{'id': 1}, {'id': 2}]}
        assert calculate_iteration_count(pr_data) == 2

    def test_empty_data(self):
        pr_data = {}
        assert calculate_iteration_count(pr_data) == 0

class TestAvgCommentLength:
    def test_basic_calculation(self):
        threads = [
            {'comments': [{'body': 'Hello'}, {'body': 'World'}]},
            {'comments': [{'body': 'Test'}]}
        ]
        # Total chars: 5 + 5 + 4 = 14, Count: 3 -> 4.666...
        result = calculate_avg_comment_length(threads)
        assert abs(result - 4.666) < 0.01

    def test_empty_threads(self):
        assert calculate_avg_comment_length([]) == 0.0

class TestReviewThreadDepth:
    def test_basic_calculation(self):
        threads = [
            {'comments': [{'body': 'a'}, {'body': 'b'}]},
            {'comments': [{'body': 'c'}]}
        ]
        # Total comments: 3, Threads: 2 -> 1.5
        assert calculate_review_thread_depth(threads) == 1.5

    def test_empty_threads(self):
        assert calculate_review_thread_depth([]) == 0.0

class TestRevertFrequency:
    def test_revert_detection(self):
        commits = [
            {'message': 'Fix bug'},
            {'message': 'Revert "Fix bug"'},
            {'message': 'New feature'}
        ]
        # 1 revert out of 3
        assert calculate_revert_frequency(commits) == pytest.approx(0.333, rel=0.01)

    def test_no_reverts(self):
        commits = [{'message': 'Fix bug'}, {'message': 'Update'}]
        assert calculate_revert_frequency(commits) == 0.0

class TestDiffComplexityScore:
    def test_normal_case(self):
        # (10 + 5) / 100 = 0.15
        assert calculate_diff_complexity_score(10, 5, 100) == 0.15

    def test_no_deletion(self):
        # lines_deleted = 0 -> returns 0
        assert calculate_diff_complexity_score(10, 0, 100) == 0.0

    def test_zero_total(self):
        assert calculate_diff_complexity_score(10, 5, 0) == 0.0

class TestIsAiNoiseFlag:
    def test_flag_true(self):
        # Score > 0.3 and message contains 'fix'
        assert is_ai_noise_flag(0.4, "fix critical bug") is True

    def test_flag_false_score_low(self):
        assert is_ai_noise_flag(0.2, "fix critical bug") is False

    def test_flag_false_no_keyword(self):
        assert is_ai_noise_flag(0.4, "add new feature") is False

    def test_flag_case_insensitive(self):
        assert is_ai_noise_flag(0.4, "HOTFIX release") is True

class TestDomainComplexity:
    def test_basic_calculation(self):
        languages = ['Python', 'JavaScript', 'Python'] # 2 unique
        manifests = [
            {'dependencies': {'react': '1.0', 'lodash': '4.0'}}, # 2 deps
            {'requires': ['pandas', 'numpy']} # 2 deps
        ]
        # 2 (langs) + 2 + 2 (deps) = 6
        assert calculate_domain_complexity(languages, manifests) == 6

    def test_empty_inputs(self):
        assert calculate_domain_complexity([], []) == 0

class TestProcessReviewMetrics:
    def test_full_pipeline(self):
        pr_data = {
            'commits': [{'message': 'fix'}, {'message': 'Revert "fix"'}],
            'review_threads': [
                {'comments': [{'body': 'Good'}]}
            ]
        }
        result = process_review_metrics(pr_data)
        assert 'avg_comment_length' in result
        assert 'review_thread_depth' in result
        assert 'revert_frequency' in result
        assert 'iteration_count' in result
        assert result['iteration_count'] == 2