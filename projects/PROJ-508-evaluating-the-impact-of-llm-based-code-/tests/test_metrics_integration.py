"""
Integration tests for metrics calculation in the context of master dataset generation.
"""
import pytest
import json
import tempfile
from pathlib import Path

from code.generate_master_dataset import (
    load_ingestion_data,
    calculate_repo_metrics,
    write_master_dataset,
    validate_output
)


class TestMetricsIntegration:
    """Integration tests for metrics calculation."""

    def test_calculate_repo_metrics_with_review_data(self):
        """Test metrics calculation with review comments and threads."""
        repo_data = {
            'comments': [
                {'body': 'Short'},
                {'body': 'This is a longer comment with more text'}
            ],
            'threads': [
                {'comments': [{'id': 1}, {'id': 2}]},
                {'comments': [{'id': 3}, {'id': 4}, {'id': 5}]}
            ],
            'commits': [
                {'message': 'Add feature'},
                {'message': 'Revert "Add feature"'},
                {'message': 'Fix bug'}
            ],
            'languages': ['Python', 'JavaScript'],
            'dependencies': ['requests', 'numpy', 'pandas'],
            'prs': [
                {
                    'push_events': [{'id': 1}, {'id': 2}, {'id': 3}]
                }
            ]
        }

        metrics = calculate_repo_metrics(repo_data)

        # Check avg_comment_length
        assert metrics['avg_comment_length'] > 0
        expected_avg = (5 + 36) / 2  # 'Short' + 'This is a longer comment with more text'
        assert metrics['avg_comment_length'] == expected_avg

        # Check review_thread_depth
        assert metrics['review_thread_depth'] == 3  # Second thread has 3 comments

        # Check revert_frequency
        assert metrics['revert_frequency'] == 1/3

        # Check iteration_count
        assert metrics['iteration_count'] == 3

        # Check domain_complexity
        assert metrics['domain_complexity'] == 2 + 3  # 2 languages + 3 dependencies

    def test_calculate_repo_metrics_with_empty_data(self):
        """Test metrics calculation with empty data."""
        repo_data = {
            'comments': [],
            'threads': [],
            'commits': [],
            'languages': [],
            'dependencies': [],
            'prs': []
        }

        metrics = calculate_repo_metrics(repo_data)

        assert metrics['avg_comment_length'] == 0.0
        assert metrics['review_thread_depth'] == 0
        assert metrics['revert_frequency'] == 0.0
        assert metrics['iteration_count'] == 0
        assert metrics['domain_complexity'] == 0

    def test_master_dataset_generation(self):
        """Test end-to-end master dataset generation."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [
                {
                    'repo_name': 'test-repo-1',
                    'llm_adoption_flag': True,
                    'comments': [{'body': 'Comment 1'}, {'body': 'Comment 2'}],
                    'threads': [{'comments': [{'id': 1}, {'id': 2}]}],
                    'commits': [
                        {'message': 'Add feature', 'lines_added': 10, 'lines_deleted': 0, 'total_lines': 100},
                        {'message': 'Revert "Add feature"', 'lines_added': 0, 'lines_deleted': 10, 'total_lines': 90}
                    ],
                    'languages': ['Python'],
                    'dependencies': ['requests'],
                    'prs': [{'push_events': [{'id': 1}]}]
                }
            ]
            json.dump(test_data, f)
            input_path = Path(f.name)

        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = Path(f.name)

            try:
                # Load and process
                repos = load_ingestion_data(input_path)
                processed_repos = []
                for repo in repos:
                    metrics = calculate_repo_metrics(repo)
                    processed_repo = {**repo, **metrics}
                    processed_repos.append(processed_repo)

                # Write master dataset
                write_master_dataset(processed_repos, output_path)

                # Validate
                assert validate_output(output_path)

                # Verify file exists and has content
                assert output_path.exists()
                with open(output_path, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == 2  # Header + 1 data row

            finally:
                output_path.unlink(missing_ok=True)

        finally:
            input_path.unlink(missing_ok=True)