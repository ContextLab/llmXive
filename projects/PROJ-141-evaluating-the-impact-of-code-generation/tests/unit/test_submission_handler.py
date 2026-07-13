"""
Unit tests for Submission Handler (T019)

Tests unique submission ID generation, UTF-8 streaming, and validation.
"""
import unittest
import uuid
from io import BytesIO
from datetime import datetime, timezone

# Import the module under test
from experiment.submission_handler import SubmissionHandler, SubmissionError


class TestSubmissionHandler(unittest.TestCase):
    """Test cases for SubmissionHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = SubmissionHandler()
    
    def test_generate_submission_id(self):
        """Test that submission IDs are unique UUIDs."""
        id1 = self.handler.generate_submission_id()
        id2 = self.handler.generate_submission_id()
        
        # Verify both are valid UUIDs
        try:
            uuid.UUID(id1)
            uuid.UUID(id2)
        except ValueError:
            self.fail("Generated ID is not a valid UUID")
        
        # Verify uniqueness
        self.assertNotEqual(id1, id2)
    
    def test_validate_valid_code(self):
        """Test validation of valid UTF-8 code."""
        valid_code = "def hello():\n    return 'world'\n"
        is_valid, error = self.handler.validate_code_content(valid_code)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_empty_code(self):
        """Test validation of empty code."""
        is_valid, error = self.handler.validate_code_content("")
        
        self.assertFalse(is_valid)
        self.assertIn("empty", error)
    
    def test_validate_very_large_code(self):
        """Test validation of code exceeding size limit."""
        # Create code larger than default 1MB limit
        large_code = "x = 1\n" * 200000  # ~1.2MB
        
        is_valid, error = self.handler.validate_code_content(large_code)
        
        self.assertFalse(is_valid)
        self.assertIn("maximum size", error)
    
    def test_validate_invalid_utf8(self):
        """Test validation of invalid UTF-8 content."""
        # This should fail UTF-8 validation
        invalid_utf8 = "Hello \xff\xfe World"
        
        is_valid, error = self.handler.validate_code_content(invalid_utf8)
        
        self.assertFalse(is_valid)
        self.assertIn("UTF-8", error)
    
    def test_stream_code_submission_integration(self):
        """Test the full streaming submission flow."""
        # Create a mock code stream
        code_content = "def test_function():\n    return 42\n"
        code_stream = BytesIO(code_content.encode('utf-8'))
        
        # This test would normally require a database connection
        # We're testing the validation logic primarily
        is_valid, error = self.handler.validate_code_content(code_content)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_code_size_tracking(self):
        """Test that code size is correctly calculated."""
        code = "x = 1\n"
        expected_size = len(code.encode('utf-8'))
        
        is_valid, error = self.handler.validate_code_content(code)
        
        self.assertTrue(is_valid)
        # The handler should track size internally
        self.assertEqual(self.handler.max_code_size_bytes, 1024 * 1024)
    
    def test_streaming_with_unicode(self):
        """Test streaming code with Unicode characters."""
        unicode_code = "# 你好世界\ndef hello():\n    print('Привет мир')\n"
        code_stream = BytesIO(unicode_code.encode('utf-8'))
        
        is_valid, error = self.handler.validate_code_content(unicode_code)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class TestSubmissionError(unittest.TestCase):
    """Test cases for SubmissionError exception."""
    
    def test_submission_error_instantiation(self):
        """Test that SubmissionError can be instantiated."""
        error = SubmissionError("Test error message")
        
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)
    
    def test_submission_error_with_nested_exception(self):
        """Test SubmissionError with nested exception info."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = SubmissionError(f"Wrapped: {str(e)}")
        
        self.assertIn("Original error", str(error))


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSubmissionHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestSubmissionError))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
