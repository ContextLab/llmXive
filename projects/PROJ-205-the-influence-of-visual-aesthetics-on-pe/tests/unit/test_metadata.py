"""
Unit Tests for Metadata Extraction (T069b).
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class TestMetadataExtraction(unittest.TestCase):

    def setUp(self):
        """
        Mock Streamlit environment for testing.
        """
        # Mock the streamlit module and its context
        self.mock_st = MagicMock()
        self.mock_st.context.headers = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.mock_st.session_state = {
            "session_start_time": "2024-01-15T10:00:00+00:00",
            "current_stimulus_id": "professional",
            "hashed_ip": "abc123hash"
        }

        # Patch streamlit in the survey module
        self.patcher = patch.dict(sys.modules, {"streamlit": self.mock_st})
        self.patcher.start()

        # Import after patching
        from survey.metadata import extract_metadata
        self.extract_metadata = extract_metadata

    def tearDown(self):
        self.patcher.stop()

    def test_extract_metadata_chrome(self):
        """Test extraction with a Chrome User-Agent."""
        result = self.extract_metadata(participant_id="test-uuid-123")
        
        self.assertEqual(result["participant_id"], "test-uuid-123")
        self.assertIn("Chrome", result["browser_version"])
        self.assertEqual(result["session_start_time"], "2024-01-15T10:00:00+00:00")
        self.assertEqual(result["stimulus_id"], "professional")
        self.assertEqual(result["hashed_ip"], "abc123hash")
        self.assertIn("timestamp", result)
        self.assertRegex(result["timestamp"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_extract_metadata_firefox(self):
        """Test extraction with a Firefox User-Agent."""
        self.mock_st.context.headers["user_agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"
        
        result = self.extract_metadata(participant_id="test-uuid-456")
        
        self.assertIn("Firefox", result["browser_version"])
        self.assertEqual(result["participant_id"], "test-uuid-456")

    def test_extract_metadata_missing_headers(self):
        """Test that missing User-Agent raises an error."""
        self.mock_st.context.headers = {}
        
        with self.assertRaises(RuntimeError) as context:
            self.extract_metadata(participant_id="test-uuid-789")
        
        self.assertIn("Unable to extract User-Agent", str(context.exception))

    def test_extract_metadata_missing_stimulus(self):
        """Test that missing stimulus_id raises an error."""
        del self.mock_st.session_state["current_stimulus_id"]
        del self.mock_st.session_state["last_stimulus_id"]
        
        with self.assertRaises(RuntimeError) as context:
            self.extract_metadata(participant_id="test-uuid-789")
        
        self.assertIn("No stimulus_id found", str(context.exception))

    def test_schema_compliance(self):
        """Test that extracted metadata matches METADATA_SCHEMA types."""
        from survey.constants import METADATA_SCHEMA
        result = self.extract_metadata(participant_id="test-uuid-123")
        
        # Check required system fields
        system_fields = ["participant_id", "timestamp", "browser_version", "session_start_time", "stimulus_id", "hashed_ip"]
        for field in system_fields:
            self.assertIn(field, result, f"Field {field} missing from metadata")
            # Type checks based on schema
            if field == "participant_id":
                self.assertIsInstance(result[field], str)
            elif field == "timestamp":
                self.assertIsInstance(result[field], str)
            elif field == "browser_version":
                self.assertIsInstance(result[field], str)
            elif field == "session_start_time":
                self.assertIsInstance(result[field], str)
            elif field == "stimulus_id":
                self.assertIsInstance(result[field], str)
            elif field == "hashed_ip":
                self.assertIsInstance(result[field], str)

if __name__ == "__main__":
    unittest.main()