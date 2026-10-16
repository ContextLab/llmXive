"""Unit tests for the T007 exclusion logging infrastructure in code/utils.py."""
import logging
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

from utils import setup_exclusion_logging, log_exclusion


class TestExclusionLogging(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmpdir.name, "logs", "exclusion.log")
        # Reset the singleton logger so each test configures fresh handlers
        logger = logging.getLogger("exclusion_logger")
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()

    def tearDown(self):
        logger = logging.getLogger("exclusion_logger")
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()
        self.tmpdir.cleanup()

    def _read_log(self):
        with open(self.log_path) as f:
            return f.read()

    def test_setup_creates_log_file_with_header(self):
        logger = setup_exclusion_logging(self.log_path)
        self.assertIsInstance(logger, logging.Logger)
        self.assertTrue(os.path.exists(self.log_path))
        content = self._read_log()
        self.assertIn("Exclusion Log Started", content)
        self.assertIn("T007", content)

    def test_log_exclusion_writes_record(self):
        logger = setup_exclusion_logging(self.log_path)
        log_exclusion(logger, "sub-001", "low_signal_quality", "SNR < 5dB")
        content = self._read_log()
        self.assertIn("EXCLUSION", content)
        self.assertIn("Subject=sub-001", content)
        self.assertIn("Reason=low_signal_quality", content)
        self.assertIn("Details=SNR < 5dB", content)

    def test_log_exclusion_without_details(self):
        logger = setup_exclusion_logging(self.log_path)
        log_exclusion(logger, "sub-002", "missing_questionnaire")
        content = self._read_log()
        self.assertIn("Subject=sub-002", content)
        self.assertIn("Reason=missing_questionnaire", content)
        self.assertNotIn("Details=", content)

    def test_setup_is_idempotent_single_handler(self):
        logger1 = setup_exclusion_logging(self.log_path)
        logger2 = setup_exclusion_logging(self.log_path)
        self.assertIs(logger1, logger2)
        self.assertEqual(len(logger2.handlers), 1)


if __name__ == "__main__":
    unittest.main()