"""
Integration tests for the Flask experiment interface (T017).

Tests the full flow:
1. Participant registration and consent
2. Session start with condition assignment
3. Problem presentation
4. Code submission
5. Session completion
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import uuid

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from experiment.app import app
from data.db_schema import get_connection, init_schema, verify_schema

class TestExperimentInterface(unittest.TestCase):
    """Integration tests for the experiment Flask app."""

    @classmethod
    def setUpClass(cls):
        """Set up test database and app client."""
        # Initialize schema
        init_schema()
        
        # Configure test client
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()

    def setUp(self):
        """Reset state before each test."""
        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)

    def test_register_participant_success(self):
        """Test successful participant registration."""
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        payload = {
            'participant_id': participant_id,
            'irb_approval_id': 'IRB-2024-001'
        }
        
        response = self.client.post('/register', 
                                  json=payload,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['participant_id'], participant_id)
        self.assertTrue(data['consent_verified'])

    def test_start_session_success(self):
        """Test starting a session with condition assignment."""
        # First register
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        self.client.post('/register', 
                       json={'participant_id': participant_id, 'irb_approval_id': 'IRB-2024-001'},
                       content_type='application/json')
        
        # Then start session
        response = self.client.post('/start_session',
                                  json={},
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('session_id', data)
        self.assertIn('condition', data)
        self.assertIn('problem_count', data)
        self.assertGreater(data['problem_count'], 0)
        self.assertIn('llm_assisted', data)

    def test_get_problem_sequence(self):
        """Test getting problems in sequence."""
        # Setup
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        self.client.post('/register', 
                       json={'participant_id': participant_id, 'irb_approval_id': 'IRB-2024-001'},
                       content_type='application/json')
        
        self.client.post('/start_session', json={}, content_type='application/json')
        
        # Get first problem
        response = self.client.get('/problem')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('problem', data)
        self.assertIn('index', data)
        self.assertIn('total', data)
        
        problem_id = data['problem']['id']
        
        # Submit code
        submit_payload = {
            'code': 'def solution():\n    return 42',
            'problem_id': problem_id
        }
        submit_response = self.client.post('/submit',
                                         json=submit_payload,
                                         content_type='application/json')
        self.assertEqual(submit_response.status_code, 200)
        submit_data = submit_response.get_json()
        self.assertEqual(submit_data['status'], 'success')
        self.assertIn('submission_id', submit_data)

    def test_condition_endpoint(self):
        """Test getting current condition."""
        # Setup
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        self.client.post('/register', 
                       json={'participant_id': participant_id, 'irb_approval_id': 'IRB-2024-001'},
                       content_type='application/json')
        
        self.client.post('/start_session', json={}, content_type='application/json')
        
        response = self.client.get('/condition')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('condition', data)
        self.assertIn('llm_assisted', data)

    def test_complete_session(self):
        """Test completing a session."""
        # Setup
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        self.client.post('/register', 
                       json={'participant_id': participant_id, 'irb_approval_id': 'IRB-2024-001'},
                       content_type='application/json')
        
        self.client.post('/start_session', json={}, content_type='application/json')
        
        response = self.client.post('/complete')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('end_time', data)

    def test_no_session_error(self):
        """Test error when no session exists."""
        # Try to access problem without starting session
        response = self.client.get('/problem')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_missing_code_submission(self):
        """Test error when code is missing in submission."""
        # Setup
        participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
        self.client.post('/register', 
                       json={'participant_id': participant_id, 'irb_approval_id': 'IRB-2024-001'},
                       content_type='application/json')
        
        self.client.post('/start_session', json={}, content_type='application/json')
        
        # Submit without code
        response = self.client.post('/submit',
                                  json={'problem_id': 'test-problem'},
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()