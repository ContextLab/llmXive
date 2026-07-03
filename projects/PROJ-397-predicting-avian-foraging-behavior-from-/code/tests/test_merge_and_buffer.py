import os
import sys
import unittest
import pandas as pd
import json
from pathlib import Path

# Add code directory to path to allow imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.merge_and_buffer import validate_schema, REQUIRED_COLUMNS

class TestMergeAndBuffer(unittest.TestCase):

    def test_validate_schema_pass(self):
        """Test that validate_schema passes when all required columns are present."""
        data = {
            'species_id': ['sp1', 'sp2'],
            'foraging_guild': ['g1', 'g2'],
            'land_cover_proportions': ['{"10": 0.5}', '{"20": 0.3}']
        }
        df = pd.DataFrame(data)
        # Should not raise
        try:
            validate_schema(df)
        except ValueError:
            self.fail("validate_schema raised ValueError unexpectedly")

    def test_validate_schema_missing_columns(self):
        """Test that validate_schema raises ValueError when columns are missing."""
        # Missing 'foraging_guild'
        data = {
            'species_id': ['sp1'],
            'land_cover_proportions': ['{}']
        }
        df = pd.DataFrame(data)
        
        with self.assertRaises(ValueError) as context:
            validate_schema(df)
        
        self.assertIn('foraging_guild', str(context.exception))
        self.assertIn('Missing required columns', str(context.exception))

    def test_validate_schema_missing_multiple_columns(self):
        """Test error message when multiple columns are missing."""
        data = {
            'species_id': ['sp1']
        }
        df = pd.DataFrame(data)
        
        with self.assertRaises(ValueError) as context:
            validate_schema(df)
        
        error_msg = str(context.exception)
        self.assertIn('foraging_guild', error_msg)
        self.assertIn('land_cover_proportions', error_msg)

if __name__ == '__main__':
    unittest.main()