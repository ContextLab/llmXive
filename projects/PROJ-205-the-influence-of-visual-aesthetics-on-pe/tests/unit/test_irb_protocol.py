"""
Unit tests for IRB Protocol ID compliance (Task T011c).
Verifies that the system enforces Constitution Principle VI.
"""
import os
import unittest
from unittest.mock import patch
import sys

# Ensure the code directory is in the path
sys.path.insert(0, 'code')

from utils.helpers import _get_irb_protocol_id, prepare_submission_row

class TestIRBProtocolCompliance(unittest.TestCase):

    def test_irb_protocol_id_missing_raises_error(self):
        """Test that missing IRB_PROTOCOL_ID raises RuntimeError."""
        # Ensure the variable is not set
        if "IRB_PROTOCOL_ID" in os.environ:
            del os.environ["IRB_PROTOCOL_ID"]
        
        with self.assertRaises(RuntimeError) as context:
            _get_irb_protocol_id()
        
        self.assertIn("IRB_PROTOCOL_ID", str(context.exception))
        self.assertIn("Constitution Principle VI", str(context.exception))

    def test_irb_protocol_id_present_returns_value(self):
        """Test that existing IRB_PROTOCOL_ID is returned correctly."""
        test_id = "PROJ-205-IRB-001"
        with patch.dict(os.environ, {"IRB_PROTOCOL_ID": test_id}):
            result = _get_irb_protocol_id()
            self.assertEqual(result, test_id)

    def test_prepare_submission_row_includes_irb_id(self):
        """Test that submission rows always include the IRB Protocol ID."""
        test_id = "PROJ-205-IRB-001"
        
        with patch.dict(os.environ, {"IRB_PROTOCOL_ID": test_id}):
            row = prepare_submission_row(
                user_id="u123",
                condition="Professional",
                ratings={"credibility": 5.0, "professionalism": 4.0},
                demographics={"age": 25, "education": 3},
                hashed_ip="abc123"
            )
            
            self.assertIn("irb_protocol_id", row)
            self.assertEqual(row["irb_protocol_id"], test_id)

    def test_consent_log_entry_structure(self):
        """Verify the structure of a consent log entry includes IRB ID."""
        # This test simulates the logic used in T014 for consent logging
        test_id = "PROJ-205-IRB-001"
        
        with patch.dict(os.environ, {"IRB_PROTOCOL_ID": test_id}):
            # Simulate a consent log entry structure
            log_entry = {
                "timestamp": "2023-10-27T10:00:00",
                "user_id": "u456",
                "decision": "agreed",
                "irb_protocol_id": _get_irb_protocol_id()
            }
            
            self.assertEqual(log_entry["irb_protocol_id"], test_id)
            self.assertEqual(log_entry["decision"], "agreed")

if __name__ == "__main__":
    unittest.main()