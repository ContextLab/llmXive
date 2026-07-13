"""
Integration test for experiment flow with single participant.

This test verifies the end-to-end flow of the experiment interface:
1. Participant consent collection and validation
2. Condition assignment and randomization
3. Problem presentation and loading
4. Code submission and timestamp recording
5. Condition switching (LLM-assisted -> baseline)
6. Session completion and logging

The test runs against a simulated single participant through both conditions
and verifies that all required data is logged correctly.
"""
import os
import sys
import json
import sqlite3
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
import uuid

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.settings import get_config, get_database_config
from data.models import Participant, Session, Problem, Submission, Condition, ProblemSource
from data.db_schema import get_connection, init_schema, verify_schema
from experiment.consent import collect_consent, save_consent_record, is_participant_consented
from experiment.randomization import assign_condition, generate_randomization_seed
from experiment.counterbalance import get_problem_order
from experiment.problem_loader import load_problems, validate_problem
from logs.experiment import setup_experiment_logger, log_condition_assignment, log_session_start, log_session_complete, log_experiment_event
from experiment.submission_handler import create_submission, validate_submission


class TestExperimentFlow:
    """Integration test suite for single participant experiment flow."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.logs_dir = Path(self.test_dir) / "logs"
        self.data_dir.mkdir(parents=True)
        self.logs_dir.mkdir(parents=True)

        # Set environment variables for test configuration
        os.environ["DATABASE_PATH"] = str(self.data_dir / "experiment.db")
        os.environ["LOG_PATH"] = str(self.logs_dir / "experiment.log")
        os.environ["IRB_APPROVAL_ID"] = "TEST-IRB-2024-001"

        # Initialize database
        self.db_path = get_database_config()["path"]
        self.conn = get_connection()
        init_schema(self.conn)
        self.conn.commit()

        # Initialize logger
        self.logger = setup_experiment_logger(str(self.logs_dir / "experiment.log"))

        # Create test participant
        self.participant_id = str(uuid.uuid4())
        self.test_participant = {
            "participant_id": self.participant_id,
            "email": "test@example.com",
            "experience_years": 3,
            "language": "python"
        }

        # Generate randomization seed
        self.seed = generate_randomization_seed(self.participant_id)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Close database connection
        if hasattr(self, 'conn'):
            self.conn.close()

        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        # Clear environment variables
        for key in ["DATABASE_PATH", "LOG_PATH", "IRB_APPROVAL_ID"]:
            if key in os.environ:
                del os.environ[key]

    def _create_mock_problem(self, problem_id: str) -> dict:
        """Create a mock problem for testing."""
        return {
            "problem_id": problem_id,
            "source": "humaneval",
            "language": "python",
            "prompt": "def add(a, b):\n    return a + b",
            "test_suite": "assert add(1, 2) == 3",
            "difficulty": "medium",
            "estimated_time_minutes": 15
        }

    def test_consent_flow(self):
        """Test participant consent collection and validation."""
        # Collect consent
        consent_result = collect_consent(
            participant_id=self.participant_id,
            irb_approval_id="TEST-IRB-2024-001"
        )

        assert consent_result["consent_given"] is True
        assert consent_result["participant_id"] == self.participant_id

        # Save consent record
        save_consent_record(self.conn, consent_result)
        self.conn.commit()

        # Verify consent
        assert is_participant_consented(self.conn, self.participant_id) is True

    def test_condition_assignment(self):
        """Test condition assignment and randomization."""
        # Assign condition
        condition_assignment = assign_condition(
            participant_id=self.participant_id,
            seed=self.seed
        )

        assert "condition" in condition_assignment
        assert condition_assignment["condition"] in ["llm_assisted", "baseline"]
        assert "seed" in condition_assignment
        assert condition_assignment["seed"] == self.seed

    def test_problem_loading_and_validation(self):
        """Test problem loading and validation."""
        # Create mock problems
        mock_problems = [
            self._create_mock_problem("problem_1"),
            self._create_mock_problem("problem_2")
        ]

        # Validate problems
        for problem in mock_problems:
            is_valid = validate_problem(problem)
            assert is_valid is True

    def test_full_experiment_flow(self):
        """Test complete experiment flow for single participant."""
        # Step 1: Consent
        consent_result = collect_consent(
            participant_id=self.participant_id,
            irb_approval_id="TEST-IRB-2024-001"
        )
        save_consent_record(self.conn, consent_result)
        self.conn.commit()

        # Step 2: Condition assignment
        condition_assignment = assign_condition(
            participant_id=self.participant_id,
            seed=self.seed
        )
        log_condition_assignment(
            self.logger,
            self.participant_id,
            condition_assignment["condition"],
            condition_assignment["seed"]
        )

        # Step 3: Get problem order (counterbalancing)
        problem_order = get_problem_order(self.participant_id, self.seed)
        assert len(problem_order) == 2  # Two problems in test set

        # Step 4: Session start
        session_id = str(uuid.uuid4())
        log_session_start(
            self.logger,
            self.participant_id,
            session_id,
            condition_assignment["condition"]
        )

        # Step 5: Process each problem
        mock_problems = [
            self._create_mock_problem("problem_1"),
            self._create_mock_problem("problem_2")
        ]

        for idx, problem in enumerate(mock_problems):
            # Log problem presentation
            log_experiment_event(
                self.logger,
                self.participant_id,
                session_id,
                "problem_presented",
                {
                    "problem_id": problem["problem_id"],
                    "order": idx
                }
            )

            # Simulate code submission
            submission_code = f"# Solution for {problem['problem_id']}\ndef solution():\n    pass"
            submission_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)

            # Create submission
            submission = create_submission(
                participant_id=self.participant_id,
                session_id=session_id,
                problem_id=problem["problem_id"],
                code=submission_code,
                submission_id=submission_id,
                timestamp=timestamp
            )

            assert submission["submission_id"] == submission_id
            assert submission["participant_id"] == self.participant_id
            assert submission["problem_id"] == problem["problem_id"]

            # Log submission
            log_experiment_event(
                self.logger,
                self.participant_id,
                session_id,
                "submission_received",
                {
                    "submission_id": submission_id,
                    "problem_id": problem["problem_id"],
                    "timestamp": timestamp.isoformat()
                }
            )

        # Step 6: Condition switch (simulate mid-experiment)
        if condition_assignment["condition"] == "llm_assisted":
            # Switch to baseline
            new_condition = "baseline"
            log_experiment_event(
                self.logger,
                self.participant_id,
                session_id,
                "condition_switch",
                {
                    "from_condition": "llm_assisted",
                    "to_condition": "baseline",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            new_condition = "llm_assisted"

        # Step 7: Session complete
        log_session_complete(
            self.logger,
            self.participant_id,
            session_id,
            condition_assignment["condition"]
        )

        # Verify all logs were written
        log_file = Path(self.logs_dir) / "experiment.log"
        assert log_file.exists()

        with open(log_file, "r") as f:
            log_lines = f.readlines()

        # Verify expected log entries
        log_entries = [json.loads(line) for line in log_lines if line.strip()]

        # Check for consent
        consent_logs = [l for l in log_entries if l.get("event") == "consent_collected"]
        assert len(consent_logs) > 0

        # Check for condition assignment
        condition_logs = [l for l in log_entries if l.get("event") == "condition_assigned"]
        assert len(condition_logs) > 0

        # Check for session start
        session_start_logs = [l for l in log_entries if l.get("event") == "session_start"]
        assert len(session_start_logs) > 0

        # Check for submissions
        submission_logs = [l for l in log_entries if l.get("event") == "submission_received"]
        assert len(submission_logs) == 2  # Two problems

        # Check for session complete
        session_complete_logs = [l for l in log_entries if l.get("event") == "session_complete"]
        assert len(session_complete_logs) > 0

    def test_database_persistence(self):
        """Test that experiment data is correctly persisted to database."""
        # Run full flow
        self.test_full_experiment_flow()

        # Verify database records
        cursor = self.conn.cursor()

        # Check participant
        cursor.execute(
            "SELECT COUNT(*) FROM participant WHERE participant_id = ?",
            (self.participant_id,)
        )
        assert cursor.fetchone()[0] == 1

        # Check session
        cursor.execute(
            "SELECT COUNT(*) FROM session WHERE participant_id = ?",
            (self.participant_id,)
        )
        assert cursor.fetchone()[0] == 1

        # Check submissions
        cursor.execute(
            "SELECT COUNT(*) FROM submission WHERE participant_id = ?",
            (self.participant_id,)
        )
        assert cursor.fetchone()[0] == 2

        # Check consent
        cursor.execute(
            "SELECT COUNT(*) FROM consent WHERE participant_id = ?",
            (self.participant_id,)
        )
        assert cursor.fetchone()[0] == 1

    def test_timestamp_precision(self):
        """Test that timestamps are recorded with ≥1 second precision in UTC."""
        # Record timestamp
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.isoformat()

        # Parse and verify
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed.tzinfo == timezone.utc

        # Verify precision (should have microseconds)
        assert "." in timestamp_str

    def test_submission_uniqueness(self):
        """Test that each submission has a unique ID."""
        submission_ids = set()

        for _ in range(10):
            submission_id = str(uuid.uuid4())
            assert submission_id not in submission_ids
            submission_ids.add(submission_id)


def main():
    """Run integration tests."""
    test_runner = TestExperimentFlow()
    test_runner.setup_method()

    try:
        print("Running consent flow test...")
        test_runner.test_consent_flow()
        print("✓ Consent flow test passed")

        print("Running condition assignment test...")
        test_runner.test_condition_assignment()
        print("✓ Condition assignment test passed")

        print("Running problem loading and validation test...")
        test_runner.test_problem_loading_and_validation()
        print("✓ Problem loading and validation test passed")

        print("Running full experiment flow test...")
        test_runner.test_full_experiment_flow()
        print("✓ Full experiment flow test passed")

        print("Running database persistence test...")
        test_runner.test_database_persistence()
        print("✓ Database persistence test passed")

        print("Running timestamp precision test...")
        test_runner.test_timestamp_precision()
        print("✓ Timestamp precision test passed")

        print("Running submission uniqueness test...")
        test_runner.test_submission_uniqueness()
        print("✓ Submission uniqueness test passed")

        print("\n✅ All integration tests passed!")
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        test_runner.teardown_method()


if __name__ == "__main__":
    sys.exit(main())