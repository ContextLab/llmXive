"""
Unit tests for course filtering logic (assessment + forum presence).

Tests the logic in `code/preprocess.py` that filters courses based on the
presence of both "assessment" and "forum" events.
"""
import os
import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add the project code directory to the path for imports
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from preprocess import filter_courses_by_events


class TestCourseFilteringLogic(unittest.TestCase):
    """Tests for the course filtering logic (assessment + forum presence)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'code_module': [
                'AAA', 'AAA', 'AAA',  # Course AAA: Assessment + Forum (Valid)
                'BBB', 'BBB',         # Course BBB: Assessment only (Invalid)
                'CCC', 'CCC',         # Course CCC: Forum only (Invalid)
                'DDD', 'DDD', 'DDD',  # Course DDD: Assessment + Forum (Valid)
                'EEE',                # Course EEE: No relevant events (Invalid)
                'FFF'                 # Course FFF: Empty event type (Invalid)
            ],
            'event_type': [
                'assessment', 'forum', 'other',
                'assessment', 'other',
                'forum', 'other',
                'assessment', 'forum', 'other',
                'other',
                ''
            ],
            'value': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        })

    def test_filter_returns_only_valid_courses(self):
        """Test that only courses with BOTH assessment and forum are kept."""
        result = filter_courses_by_events(self.test_data)
        
        unique_courses = result['code_module'].unique()
        
        # Expected: AAA and DDD
        expected_courses = {'AAA', 'DDD'}
        
        self.assertEqual(set(unique_courses), expected_courses)
        self.assertEqual(len(result), 6) # 3 rows for AAA + 3 rows for DDD

    def test_filter_excludes_assessment_only(self):
        """Test that courses with only assessment events are excluded."""
        result = filter_courses_by_events(self.test_data)
        
        self.assertNotIn('BBB', result['code_module'].values)

    def test_filter_excludes_forum_only(self):
        """Test that courses with only forum events are excluded."""
        result = filter_courses_by_events(self.test_data)
        
        self.assertNotIn('CCC', result['code_module'].values)

    def test_filter_excludes_courses_without_either(self):
        """Test that courses with neither event type are excluded."""
        result = filter_courses_by_events(self.test_data)
        
        self.assertNotIn('EEE', result['code_module'].values)
        self.assertNotIn('FFF', result['code_module'].values)

    def test_filter_empty_dataframe(self):
        """Test that an empty dataframe returns an empty dataframe."""
        empty_df = pd.DataFrame(columns=['code_module', 'event_type', 'value'])
        result = filter_courses_by_events(empty_df)
        
        self.assertTrue(result.empty)

    def test_filter_no_matching_courses(self):
        """Test that if no courses have both events, result is empty."""
        data = pd.DataFrame({
            'code_module': ['GGG', 'HHH'],
            'event_type': ['assessment', 'forum'],
            'value': [1, 1]
        })
        result = filter_courses_by_events(data)
        
        self.assertTrue(result.empty)

    def test_filter_case_sensitivity(self):
        """Test that event type matching is case-sensitive (as per typical data)."""
        # If the logic expects 'assessment', 'Assessment' should not match unless normalized.
        # Assuming strict matching based on the prompt's specific "assessment" and "forum" strings.
        data = pd.DataFrame({
            'code_module': ['III', 'III'],
            'event_type': ['Assessment', 'Forum'], # Capitalized
            'value': [1, 1]
        })
        result = filter_courses_by_events(data)
        
        # Should be empty if strictly looking for lowercase 'assessment'
        self.assertTrue(result.empty)


if __name__ == '__main__':
    unittest.main()