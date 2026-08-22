import json
import os
import sys
import tempfile
import shutil
import unittest
from datetime import datetime

# Add project root to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_collection import (
    log_help_request, 
    log_session_start, 
    log_session_end, 
    load_existing_logs, 
    save_logs,
    ensure_data_directory,
    CLARIFICATION_KEYWORDS,
    MODERATOR_TAG
)

class TestClarificationLogging(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.logs_path = os.path.join(self.test_dir, "logs.json")
        # Create a minimal valid log structure
        self.initial_logs = {
            "sessions": [],
            "metadata": {"version": "1.0"}
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_keyword_detection(self):
        """Test that keyword-based questions are detected."""
        logs = load_existing_logs(self.logs_path)
        session_data = {"id": 1, "condition": "test"}
        logs = log_session_start(session_data, logs)
        
        # Test 'how'
        logs = log_help_request(0, "How do I install this?", "user", logs)
        self.assertEqual(logs['sessions'][0]['clarification_question_count'], 1)
        
        # Test 'why'
        logs = log_help_request(0, "Why is the server down?", "user", logs)
        self.assertEqual(logs['sessions'][0]['clarification_question_count'], 2)

    def test_moderator_tag_detection(self):
        """Test that moderator-tagged questions are detected."""
        logs = load_existing_logs(self.logs_path)
        session_data = {"id": 1, "condition": "test"}
        logs = log_session_start(session_data, logs)
        
        tag_msg = f"{MODERATOR_TAG} Can you clarify step 3?"
        logs = log_help_request(0, tag_msg, "moderator", logs)
        
        self.assertEqual(logs['sessions'][0]['clarification_question_count'], 1)
        self.assertEqual(logs['sessions'][0]['clarification_questions'][0]['type'], 'moderator-tag')

    def test_non_question_ignored(self):
        """Test that non-question statements are ignored."""
        logs = load_existing_logs(self.logs_path)
        session_data = {"id": 1, "condition": "test"}
        logs = log_session_start(session_data, logs)
        
        logs = log_help_request(0, "This is just a statement.", "user", logs)
        
        self.assertEqual(logs['sessions'][0]['clarification_question_count'], 0)
        self.assertEqual(len(logs['sessions'][0]['clarification_questions']), 0)

    def test_count_matches_array_length(self):
        """Verify that the count field always matches the array length."""
        logs = load_existing_logs(self.logs_path)
        session_data = {"id": 1, "condition": "test"}
        logs = log_session_start(session_data, logs)
        
        # Add valid questions
        logs = log_help_request(0, "How does this work?", "user", logs)
        logs = log_help_request(0, "What is X?", "user", logs)
        
        # Add invalid statement
        logs = log_help_request(0, "I see.", "user", logs)
        
        # Add moderator tag
        logs = log_help_request(0, f"{MODERATOR_TAG} Help.", "moderator", logs)
        
        expected_count = 3
        actual_count = logs['sessions'][0]['clarification_question_count']
        array_len = len(logs['sessions'][0]['clarification_questions'])
        
        self.assertEqual(actual_count, expected_count)
        self.assertEqual(array_len, expected_count)
        self.assertEqual(actual_count, array_len)

    def test_file_output_structure(self):
        """Test that the saved file has the correct structure."""
        ensure_data_directory() # Ensure dir exists for save
        logs = load_existing_logs(self.logs_path)
        session_data = {"id": 1, "condition": "test"}
        logs = log_session_start(session_data, logs)
        logs = log_help_request(0, "How?", "user", logs)
        logs = log_session_end(0, datetime.now().isoformat(), logs)
        
        save_logs(logs, self.logs_path)
        
        with open(self.logs_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn('sessions', saved_data)
        self.assertIn('clarification_questions', saved_data['sessions'][0])
        self.assertIn('clarification_question_count', saved_data['sessions'][0])
        self.assertIsInstance(saved_data['sessions'][0]['clarification_questions'], list)

if __name__ == '__main__':
    unittest.main()