import os
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from exclusion_tracker import (
    ensure_exclusions_file_exists,
    log_exclusion,
    evaluate_subject_for_exclusion,
    get_excluded_subjects,
    MIN_TRIALS_PER_CONDITION,
    MAX_ARTIFACT_REMOVAL_RATIO
)

from logging_setup import get_logger

class TestExclusionTracker:
    @pytest.fixture
    def temp_exclusions_path(self):
        """Create a temporary file for exclusions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("subject_id,reason\n")
            path = Path(f.name)
        yield path
        # Cleanup
        if path.exists():
            os.remove(path)

    def test_ensure_exclusions_file_exists_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "new_exclusions.csv"
            assert not path.exists()
            ensure_exclusions_file_exists(path)
            assert path.exists()
            with open(path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                assert header == ['subject_id', 'reason']

    def test_log_exclusion_appends_correctly(self, temp_exclusions_path):
        logger = MagicMock()
        log_exclusion(temp_exclusions_path, "sub-002", "insufficient trials", logger)
        
        with open(temp_exclusions_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['subject_id'] == 'sub-002'
            assert rows[0]['reason'] == 'insufficient trials'

    def test_evaluate_insufficient_trials(self, temp_exclusions_path):
        logger = MagicMock()
        # Subject has 8 trials in 'switch' condition (< 10)
        trials = {"switch": 8, "stay": 15}
        result = evaluate_subject_for_exclusion(
            "sub-003", trials, 23, 20, temp_exclusions_path, logger
        )
        assert result is True
        logger.info.assert_any_call("Subject sub-003 excluded: insufficient trials")

    def test_evaluate_excessive_artifact_removal(self, temp_exclusions_path):
        logger = MagicMock()
        # Subject has enough trials per condition, but >50% removed
        # 20 before, 5 after -> 75% removed
        trials = {"switch": 10, "stay": 10}
        result = evaluate_subject_for_exclusion(
            "sub-004", trials, 20, 5, temp_exclusions_path, logger
        )
        assert result is True
        logger.info.assert_any_call("Subject sub-004 excluded: excessive artifact removal")

    def test_evaluate_passes(self, temp_exclusions_path):
        logger = MagicMock()
        # Subject has enough trials and <50% removed
        # 20 before, 15 after -> 25% removed
        trials = {"switch": 12, "stay": 12}
        result = evaluate_subject_for_exclusion(
            "sub-005", trials, 24, 15, temp_exclusions_path, logger
        )
        assert result is False
        # Should not log any exclusion
        assert not logger.info.called

    def test_get_excluded_subjects(self, temp_exclusions_path):
        # Manually write some data
        with open(temp_exclusions_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sub-006', 'insufficient trials'])
            writer.writerow(['sub-007', 'excessive artifact removal'])
        
        excluded = get_excluded_subjects(temp_exclusions_path)
        assert 'sub-006' in excluded
        assert 'sub-007' in excluded
        assert len(excluded) == 2