"""
Unit tests for generate_preprocessing_stats.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions we want to test
# We need to import from the module file directly or via path manipulation
# Since the script is standalone, we can import the logic functions if we refactor,
# but for now, we will test the behavior by mocking the file system and running main.

# To make functions testable, we assume the logic is defined in the module.
# We will import the specific functions if they are exposed, otherwise we test the side effects.
# For this task, we will implement a test that creates fake logs and verifies the JSON output.

import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generate_preprocessing_stats import calculate_stats, load_subject_logs

class TestCalculateStats:
    def test_empty_logs(self):
        logs = []
        stats = calculate_stats(logs)
        assert stats['total_subjects'] == 0
        assert stats['successful_subjects'] == 0
        assert stats['success_rate_percentage'] == 0.0

    def test_all_success(self):
        logs = [
            {'status': 'success', 'subject_id': 'sub-01'},
            {'status': 'success', 'subject_id': 'sub-02'}
        ]
        stats = calculate_stats(logs)
        assert stats['total_subjects'] == 2
        assert stats['successful_subjects'] == 2
        assert stats['success_rate_percentage'] == 100.0

    def test_partial_success(self):
        logs = [
            {'status': 'success', 'subject_id': 'sub-01'},
            {'status': 'failure', 'subject_id': 'sub-02'},
            {'status': 'success', 'subject_id': 'sub-03'}
        ]
        stats = calculate_stats(logs)
        assert stats['total_subjects'] == 3
        assert stats['successful_subjects'] == 2
        assert stats['success_rate_percentage'] == pytest.approx(66.67, rel=0.1)

    def test_all_failure(self):
        logs = [
            {'status': 'failure', 'subject_id': 'sub-01'},
            {'status': 'failure', 'subject_id': 'sub-02'}
        ]
        stats = calculate_stats(logs)
        assert stats['total_subjects'] == 2
        assert stats['successful_subjects'] == 0
        assert stats['success_rate_percentage'] == 0.0

class TestLoadSubjectLogs:
    def test_load_logs_from_directory(self, tmp_path):
        # Create fake log files
        log1 = tmp_path / "sub-01_preprocess_log.json"
        log1.write_text(json.dumps({'status': 'success', 'subject_id': 'sub-01'}))
        
        log2 = tmp_path / "sub-02_preprocess_log.json"
        log2.write_text(json.dumps({'status': 'failure', 'subject_id': 'sub-02'}))
        
        # Non-matching file
        (tmp_path / "random.txt").write_text("hello")

        logs = load_subject_logs(tmp_path)
        
        assert len(logs) == 2
        statuses = [l['status'] for l in logs]
        assert 'success' in statuses
        assert 'failure' in statuses

    def test_empty_directory(self, tmp_path):
        logs = load_subject_logs(tmp_path)
        assert len(logs) == 0

    def test_nonexistent_directory(self, tmp_path):
        logs = load_subject_logs(tmp_path / "nonexistent")
        assert len(logs) == 0