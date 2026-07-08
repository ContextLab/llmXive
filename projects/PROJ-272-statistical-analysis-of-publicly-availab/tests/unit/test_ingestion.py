"""
Unit tests for ingestion module.
"""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import sys
# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import compute_sha256, download_file, validate_scope
from code.config import DataSourceConfig

class TestIngestionUtils(unittest.TestCase):

    def test_compute_sha256(self):
        """Test SHA-256 computation on a known string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Hello, World!")
            tmp_path = Path(tmp.name)
        
        try:
            # Expected hash for "Hello, World!"
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            actual_hash = compute_sha256(tmp_path)
            self.assertEqual(actual_hash, expected_hash)
        finally:
            os.remove(tmp_path)

    def test_validate_scope_adress(self):
        """Test that ADReSS primary source is valid."""
        config = DataSourceConfig(primary_source="ADReSS", secondary_source=None)
        # Mock logger
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        self.assertTrue(result)
        logger.warning.assert_not_called()

    def test_validate_scope_dementiabank_warning(self):
        """Test that DementiaBank as secondary source triggers a warning."""
        config = DataSourceConfig(primary_source="ADReSS", secondary_source="DementiaBank")
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        # The function returns True if primary is ADReSS, but logs a warning
        self.assertTrue(result)
        logger.warning.assert_called()
        self.assertIn("DementiaBank", logger.warning.call_args[0][0])

    def test_validate_scope_invalid_primary(self):
        """Test that non-ADReSS primary source fails validation."""
        config = DataSourceConfig(primary_source="DementiaBank", secondary_source=None)
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        self.assertFalse(result)
        logger.warning.assert_called()

if __name__ == '__main__':
    unittest.main()