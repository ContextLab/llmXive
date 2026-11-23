"""
Unit tests for the clarification question logging utilities.
"""
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from experiment.logging_utils import (
    detect_clarification_source,
    log_clarification_event,
    process_raw_input_for_clarifications,
    get_clarification_count,
    update_logs_with_clarification_counts
)

class TestClarificationDetection(unittest.TestCase):
    
    def test_keyword_detection_how(self):
        self.assertEqual(detect_clarification_source("How do I do this?"), 'keyword')
    
    def test_keyword_detection_why(self):
        self.assertEqual(detect_clarification_source("Why is this failing?"), 'keyword')
    
    def test_keyword_detection_what(self):
        self.assertEqual(detect_clarification_source("What is the API?"), 'keyword')
    
    def test_keyword_detection_explain(self):
        self.assertEqual(detect_clarification_source("Explain the setup."), 'keyword')
    
    def test_no_keyword_detection(self):
        self.assertIsNone(detect_clarification_source("This is just a statement."))
    
    def test_moderator_tag_override(self):
        # Even if text doesn't match keywords, moderator tag should return 'moderator'
        self.assertEqual(detect_clarification_source("This is a tag.", is_moderator_tag=True), 'moderator')
    
    def test_moderator_tag_with_keyword(self):
        # Moderator tag takes precedence
        self.assertEqual(detect_clarification_source("How do I do this?", is_moderator_tag=True), 'moderator')

class TestLogging(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logs_path = os.path.join(self.temp_dir, 'participant_logs.json')
    
    def test_log_clarification_event_creates_file(self):
        event = log_clarification_event(
            text="How do I start?",
            source='keyword',
            participant_id="P001",
            session_id="S001",
            output_path=self.logs_path
        )
        
        self.assertTrue(os.path.exists(self.logs_path))
        self.assertEqual(event['event_type'], 'clarification')
        self.assertEqual(event['source'], 'keyword')
        self.assertEqual(event['text'], "How do I start?")
        self.assertEqual(event['participant_id'], "P001")
        self.assertEqual(event['session_id'], "S001")
    
    def test_log_clarification_event_appends(self):
        # Log first event
        log_clarification_event(
            text="How do I start?",
            source='keyword',
            participant_id="P001",
            session_id="S001",
            output_path=self.logs_path
        )
        
        # Log second event
        log_clarification_event(
            text="Why is this broken?",
            source='keyword',
            participant_id="P001",
            session_id="S001",
            output_path=self.logs_path
        )
        
        with open(self.logs_path, 'r') as f:
            logs = json.load(f)
        
        self.assertEqual(len(logs), 2)
    
    def test_process_raw_input_for_clarifications(self):
        event = process_raw_input_for_clarifications(
            raw_input="What is the architecture?",
            participant_id="P001",
            session_id="S001",
            output_path=self.logs_path
        )
        
        self.assertIsNotNone(event)
        self.assertEqual(event['source'], 'keyword')
    
    def test_process_raw_input_no_clarification(self):
        event = process_raw_input_for_clarifications(
            raw_input="I am just writing code.",
            participant_id="P001",
            session_id="S001",
            output_path=self.logs_path
        )
        
        self.assertIsNone(event)
    
    def test_get_clarification_count(self):
        # Initially 0
        self.assertEqual(get_clarification_count(self.logs_path), 0)
        
        # Add some events
        log_clarification_event("How?", 'keyword', "P001", "S001", self.logs_path)
        log_clarification_event("Why?", 'keyword', "P001", "S001", self.logs_path)
        
        self.assertEqual(get_clarification_count(self.logs_path), 2)
    
    def test_update_logs_with_clarification_counts(self):
        # Add events
        log_clarification_event("How?", 'keyword', "P001", "S001", self.logs_path)
        log_clarification_event("Why?", 'keyword', "P001", "S001", self.logs_path)
        log_clarification_event("What?", 'keyword', "P002", "S002", self.logs_path)
        
        # Re-read and update
        with open(self.logs_path, 'r') as f:
            logs = json.load(f)
        
        updated_logs = update_logs_with_clarification_counts(logs, self.logs_path)
        
        # Check that summary records were added
        summaries = [l for l in updated_logs if l.get('event_type') == 'session_summary']
        self.assertEqual(len(summaries), 2)
        
        # Verify counts
        p001_summaries = [s for s in summaries if s['participant_id'] == 'P001']
        p002_summaries = [s for s in summaries if s['participant_id'] == 'P002']
        
        self.assertEqual(len(p001_summaries), 1)
        self.assertEqual(p001_summaries[0]['clarification_question_count'], 2)
        
        self.assertEqual(len(p002_summaries), 1)
        self.assertEqual(p002_summaries[0]['clarification_question_count'], 1)

if __name__ == '__main__':
    unittest.main()