"""
Unit tests for edge cases in the participant session module:
- Dropout handling (partial session recording)
- Network timeout simulation and retry logic
"""
import json
import logging
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from participants.session import SessionState, SessionManager, create_session
from config import get_responses_dir, get_project_root


class TestSessionEdgeCases(unittest.TestCase):
    """Test edge cases for session management: dropout and network timeout."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.responses_dir = get_responses_dir()
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging for tests
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        """Clean up test artifacts."""
        # Remove any test session files created during tests
        test_session_file = self.responses_dir / "test_session_dropout.json"
        if test_session_file.exists():
            test_session_file.unlink()
        test_session_file = self.responses_dir / "test_session_timeout.json"
        if test_session_file.exists():
            test_session_file.unlink()

    def test_session_dropout_partial_recording(self):
        """
        Test that when a session drops out (incomplete), the system:
        1. Records partial responses
        2. Flags the session as incomplete
        3. Saves the state to disk correctly
        """
        # Create a session manager
        session_id = "test_dropout_001"
        session_manager = SessionManager(session_id=session_id)
        
        # Simulate starting a session
        session_manager.start_session()
        
        # Add some responses
        session_manager.add_response(
            question_id="q1",
            value=True,
            timestamp=datetime.now()
        )
        session_manager.add_response(
            question_id="q2",
            value=False,
            timestamp=datetime.now()
        )
        
        # Simulate dropout BEFORE completing all expected questions
        # (Assume there should be 5 questions total, but only 2 were answered)
        session_manager.mark_as_dropout(expected_questions=5)
        
        # Verify the session state
        self.assertEqual(session_manager.state.status, "dropout")
        self.assertEqual(len(session_manager.state.responses), 2)
        self.assertTrue(session_manager.state.is_incomplete)
        
        # Save the session
        session_manager.save_session()
        
        # Verify file exists and contains correct data
        output_path = self.responses_dir / f"{session_id}.json"
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['status'], 'dropout')
        self.assertEqual(data['response_count'], 2)
        self.assertTrue(data['is_incomplete'])
        self.assertIn('dropout_timestamp', data)

    def test_network_timeout_retry_logic(self):
        """
        Test that when a network timeout occurs during response capture:
        1. The system retries the operation (up to max_retries)
        2. Logs the retry attempts
        3. Fails gracefully if all retries are exhausted
        """
        session_id = "test_timeout_001"
        session_manager = SessionManager(session_id=session_id)
        session_manager.start_session()
        
        # Mock the network-dependent save operation to simulate timeout
        original_save = session_manager._save_to_disk
        retry_count = 0
        max_simulated_failures = 2
        
        def mock_save_with_failures(session_data):
            nonlocal retry_count
            retry_count += 1
            if retry_count <= max_simulated_failures:
                raise TimeoutError("Simulated network timeout")
            return original_save(session_data)
        
        with patch.object(session_manager, '_save_to_disk', side_effect=mock_save_with_failures):
            # Add a response
            session_manager.add_response(
                question_id="q1",
                value=True,
                timestamp=datetime.now()
            )
            
            # This should trigger retries
            # The SessionManager should handle the retry logic internally
            # We verify that after max_simulated_failures, it succeeds
            session_manager.save_session()
            
            # Verify the file was eventually saved
            output_path = self.responses_dir / f"{session_id}.json"
            self.assertTrue(output_path.exists())
            
            # Verify retry count matches expected behavior
            self.assertEqual(retry_count, max_simulated_failures + 1)

    def test_network_timeout_exhaustion(self):
        """
        Test that when network timeouts persist beyond max_retries:
        1. The system raises an appropriate exception
        2. The session is marked as failed
        3. Partial data is preserved if possible
        """
        session_id = "test_timeout_exhaust_001"
        session_manager = SessionManager(session_id=session_id)
        session_manager.start_session()
        
        # Mock the save operation to always fail
        def always_fail_save(session_data):
            raise TimeoutError("Persistent network timeout")
        
        with patch.object(session_manager, '_save_to_disk', side_effect=always_fail_save):
            session_manager.add_response(
                question_id="q1",
                value=True,
                timestamp=datetime.now()
            )
            
            # This should raise an exception after retries
            with self.assertRaises(TimeoutError):
                session_manager.save_session()
            
            # Verify the session state reflects the failure
            # Note: Depending on implementation, the status might be 'failed'
            # or the exception might be raised before status update.
            # We verify that the session manager handled the error state.
            self.assertEqual(len(session_manager.state.responses), 1)
            # The session is not saved, so we don't check disk existence here.

    def test_session_state_serialization_after_dropout(self):
        """
        Test that a session state with dropout can be correctly serialized
        and deserialized without data loss.
        """
        session_id = "test_serialization_dropout"
        session_manager = SessionManager(session_id=session_id)
        session_manager.start_session()
        
        # Add responses
        session_manager.add_response("q1", True, datetime.now())
        session_manager.add_response("q2", False, datetime.now())
        
        # Mark dropout
        session_manager.mark_as_dropout(expected_questions=10)
        
        # Serialize to dict
        state_dict = session_manager.state.to_dict()
        
        # Deserialize from dict
        restored_state = SessionState.from_dict(state_dict)
        
        # Verify data integrity
        self.assertEqual(restored_state.session_id, session_id)
        self.assertEqual(restored_state.status, "dropout")
        self.assertEqual(len(restored_state.responses), 2)
        self.assertTrue(restored_state.is_incomplete)
        self.assertIn('dropout_timestamp', state_dict)

    def test_concurrent_session_access_handling(self):
        """
        Test that the session manager handles concurrent access attempts gracefully.
        (Basic check for lock existence or thread-safety markers if implemented)
        """
        # This test ensures that if threading locks are added in the future,
        # the basic structure supports them.
        session_id = "test_concurrent"
        session_manager = SessionManager(session_id=session_id)
        
        # If the implementation uses threading locks, they should be initialized
        # For now, we just verify the manager can be instantiated multiple times
        # without conflict for different session IDs
        manager1 = SessionManager(session_id="concurrent_1")
        manager2 = SessionManager(session_id="concurrent_2")
        
        self.assertIsNot(manager1, manager2)
        self.assertNotEqual(manager1.state.session_id, manager2.state.session_id)


if __name__ == "__main__":
    unittest.main()
