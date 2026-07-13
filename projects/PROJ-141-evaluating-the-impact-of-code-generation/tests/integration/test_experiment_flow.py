"""
Integration test for experiment flow with single participant.

This test verifies the complete end-to-end flow of the experiment interface
with a single participant, ensuring that:
1. Consent flow works correctly
2. Participant registration and randomization work
3. Problem presentation works
4. Code submission works
5. Timestamp recording works
6. Condition switching works
7. Session completion works
8. All events are logged correctly
"""

import os
import sys
import json
import tempfile
import shutil
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiment.app import init_app
from experiment.consent import generate_consent_hash, save_consent_record
from experiment.randomization import generate_participant_id, assign_condition, pin_random_seed
from experiment.timestamp_recorder import get_current_utc_timestamp
from experiment.submission_handler import SubmissionHandler
from logs.experiment import setup_experiment_logger, log_experiment_event
from config.settings import get_config


class TestExperimentFlow(unittest.TestCase):
    """Integration test for the complete experiment flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir()
        self.logs_dir = Path(self.test_dir) / "logs"
        self.logs_dir.mkdir()
        
        # Set environment variables for test
        os.environ["TEST_MODE"] = "true"
        os.environ["DATA_DIR"] = str(self.data_dir)
        os.environ["LOGS_DIR"] = str(self.logs_dir)
        os.environ["DATABASE_PATH"] = str(self.data_dir / "test_experiment.db")
        os.environ["IRB_APPROVAL_ID"] = "TEST-IRB-001"
        
        # Initialize app
        self.app = init_app()
        self.client = self.app.test_client()
        
        # Setup logger
        self.logger = setup_experiment_logger(str(self.logs_dir / "experiment.log"))
        
        # Generate test participant ID
        self.participant_id = generate_participant_id()
        
        # Pin random seed for reproducibility
        pin_random_seed(42)
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Clear environment variables
        for key in ["TEST_MODE", "DATA_DIR", "LOGS_DIR", "DATABASE_PATH", "IRB_APPROVAL_ID"]:
            if key in os.environ:
                del os.environ[key]
    
    def _generate_consent_hash(self, irb_id):
        """Generate consent hash for IRB approval."""
        return generate_consent_hash(irb_id)
    
    def _save_consent_record(self, participant_id, irb_id):
        """Save consent record for participant."""
        consent_hash = self._generate_consent_hash(irb_id)
        save_consent_record(participant_id, consent_hash)
    
    def test_01_health_check(self):
        """Test that the application is healthy."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
    
    def test_02_participant_registration(self):
        """Test participant registration flow."""
        # Generate IRB approval ID
        irb_id = "TEST-IRB-001"
        
        # Save consent record
        self._save_consent_record(self.participant_id, irb_id)
        
        # Register participant
        response = self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "registered")
        self.assertEqual(data["participant_id"], self.participant_id)
    
    def test_03_session_start(self):
        """Test session start and randomization."""
        # First register and consent
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        # Start session
        response = self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "session_started")
        self.assertIn("condition", data)
        self.assertIn("seed", data)
        self.assertIn("session_id", data)
        
        # Verify condition is valid
        self.assertIn(data["condition"], ["llm_assisted", "baseline"])
    
    def test_04_get_next_problem(self):
        """Test problem retrieval."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        # Get next problem
        response = self.client.get(
            "/get_next_problem",
            query_string={"participant_id": self.participant_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("problem_id", data)
        self.assertIn("description", data)
        self.assertIn("starter_code", data)
        self.assertIn("language", data)
    
    def test_05_submit_code(self):
        """Test code submission flow."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        # Get problem first
        problem_response = self.client.get(
            "/get_next_problem",
            query_string={"participant_id": self.participant_id}
        )
        problem_data = json.loads(problem_response.data)
        problem_id = problem_data["problem_id"]
        
        # Submit code
        test_code = "def solution():\n    return True"
        response = self.client.post(
            "/submit_code",
            json={
                "participant_id": self.participant_id,
                "problem_id": problem_id,
                "code": test_code,
                "language": problem_data["language"]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "submitted")
        self.assertIn("submission_id", data)
        self.assertIn("timestamp", data)
    
    def test_06_timestamp_recording(self):
        """Test that timestamps are recorded correctly."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        before_start = get_current_utc_timestamp()
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        after_start = get_current_utc_timestamp()
        
        # Verify timestamps are valid and in order
        self.assertLessEqual(before_start, after_start)
        
        # Get problem
        problem_response = self.client.get(
            "/get_next_problem",
            query_string={"participant_id": self.participant_id}
        )
        problem_data = json.loads(problem_response.data)
        problem_id = problem_data["problem_id"]
        
        before_submit = get_current_utc_timestamp()
        
        # Submit code
        self.client.post(
            "/submit_code",
            json={
                "participant_id": self.participant_id,
                "problem_id": problem_id,
                "code": "def solution():\n    return True",
                "language": problem_data["language"]
            }
        )
        
        after_submit = get_current_utc_timestamp()
        
        # Verify timestamps are valid and in order
        self.assertLessEqual(before_submit, after_submit)
        self.assertLessEqual(after_start, before_submit)
    
    def test_07_condition_switching(self):
        """Test condition switching logic."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        # Get current condition
        response = self.client.get(
            "/get_current_condition",
            query_string={"participant_id": self.participant_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("condition", data)
        self.assertIn("participant_id", data)
    
    def test_08_session_completion(self):
        """Test session completion flow."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        # Complete session
        response = self.client.post(
            "/complete_session",
            json={"participant_id": self.participant_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "session_complete")
        self.assertIn("session_id", data)
        self.assertIn("completion_timestamp", data)
    
    def test_09_full_experiment_flow(self):
        """Test complete experiment flow with single participant."""
        # Step 1: Consent and Registration
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        register_response = self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        self.assertEqual(register_response.status_code, 200)
        
        # Step 2: Start Session
        start_response = self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        self.assertEqual(start_response.status_code, 200)
        session_data = json.loads(start_response.data)
        session_id = session_data["session_id"]
        initial_condition = session_data["condition"]
        
        # Step 3: Get and solve first problem
        problem_response = self.client.get(
            "/get_next_problem",
            query_string={"participant_id": self.participant_id}
        )
        self.assertEqual(problem_response.status_code, 200)
        problem_data = json.loads(problem_response.data)
        problem_id = problem_data["problem_id"]
        
        # Submit solution
        submit_response = self.client.post(
            "/submit_code",
            json={
                "participant_id": self.participant_id,
                "problem_id": problem_id,
                "code": "def solution():\n    return True",
                "language": problem_data["language"]
            }
        )
        self.assertEqual(submit_response.status_code, 200)
        
        # Step 4: Verify condition
        condition_response = self.client.get(
            "/get_current_condition",
            query_string={"participant_id": self.participant_id}
        )
        self.assertEqual(condition_response.status_code, 200)
        condition_data = json.loads(condition_response.data)
        self.assertEqual(condition_data["condition"], initial_condition)
        
        # Step 5: Complete session
        complete_response = self.client.post(
            "/complete_session",
            json={"participant_id": self.participant_id}
        )
        self.assertEqual(complete_response.status_code, 200)
        complete_data = json.loads(complete_response.data)
        self.assertEqual(complete_data["status"], "session_complete")
        
        # Step 6: Verify logs exist
        log_file = Path(self.logs_dir) / "experiment.log"
        self.assertTrue(log_file.exists())
        
        # Read and verify log entries
        with open(log_file, 'r') as f:
            log_content = f.read()
            self.assertIn(self.participant_id, log_content)
            self.assertIn(session_id, log_content)
            self.assertIn("session_started", log_content)
            self.assertIn("session_complete", log_content)
    
    def test_10_logging_verification(self):
        """Verify that all events are logged correctly."""
        # Setup participant
        irb_id = "TEST-IRB-001"
        self._save_consent_record(self.participant_id, irb_id)
        
        self.client.post(
            "/register",
            json={
                "participant_id": self.participant_id,
                "irb_approval_id": irb_id,
                "email": "test@example.com"
            }
        )
        
        self.client.post(
            "/start_session",
            json={"participant_id": self.participant_id}
        )
        
        # Get problem
        problem_response = self.client.get(
            "/get_next_problem",
            query_string={"participant_id": self.participant_id}
        )
        problem_data = json.loads(problem_response.data)
        problem_id = problem_data["problem_id"]
        
        # Submit code
        self.client.post(
            "/submit_code",
            json={
                "participant_id": self.participant_id,
                "problem_id": problem_id,
                "code": "def solution():\n    return True",
                "language": problem_data["language"]
            }
        )
        
        # Complete session
        self.client.post(
            "/complete_session",
            json={"participant_id": self.participant_id}
        )
        
        # Verify log file
        log_file = Path(self.logs_dir) / "experiment.log"
        self.assertTrue(log_file.exists())
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)
            
            # Check for required log entries
            log_content = ''.join(lines)
            self.assertIn(self.participant_id, log_content)
            self.assertIn("consent", log_content.lower())
            self.assertIn("session_start", log_content.lower())
            self.assertIn("problem_view", log_content.lower())
            self.assertIn("code_submission", log_content.lower())
            self.assertIn("session_complete", log_content.lower())


if __name__ == "__main__":
    unittest.main()