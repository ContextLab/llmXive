"""
Unit tests for replication module: concordance calculation and missing data exclusion logic.
Tests T037 requirements.
"""
import csv
import os
import tempfile
import unittest
import math

# Import the specific functions to test from the replication module
# Using the API surface provided in the prompt
import sys
import importlib.util

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from replication import calculate_concordance, get_common_lines, ReplicationError


class TestConcordanceCalculation(unittest.TestCase):
    """Tests for the calculate_concordance function."""

    def test_concordance_both_positive(self):
        """Test when both original and replication effects are positive."""
        orig_effect = 0.5
        rep_effect = 0.6
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertTrue(concordance)

    def test_concordance_both_negative(self):
        """Test when both original and replication effects are negative."""
        orig_effect = -0.5
        rep_effect = -0.4
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertTrue(concordance)

    def test_concordance_opposite_signs(self):
        """Test when effects have opposite signs (discordant)."""
        orig_effect = 0.5
        rep_effect = -0.3
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertFalse(concordance)

    def test_concordance_zero_original(self):
        """Test behavior when original effect is exactly zero."""
        # If original is 0, direction is undefined; typically treated as non-concordant
        # unless replication is also 0. We assume strict sign matching.
        orig_effect = 0.0
        rep_effect = 0.5
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertFalse(concordance)

    def test_concordance_both_zero(self):
        """Test when both effects are zero."""
        orig_effect = 0.0
        rep_effect = 0.0
        # 0 and 0: sign(0) is usually 0. 0==0 implies concordance in magnitude,
        # but directionally ambiguous. Based on standard biological interpretation,
        # if no effect in either, it's often considered consistent (concordant).
        # However, strict sign check: 0 is not >0 and not <0.
        # Let's assume the implementation handles 0 as a special case or checks signum.
        # If signum(0) == 0, then 0 == 0 -> True.
        concordance = calculate_concordance(orig_effect, rep_effect)
        # Depending on implementation, this might be True or False.
        # We assume the implementation treats 0 as matching 0.
        # If the implementation uses `math.copysign` or similar, 0.0 matches 0.0.
        self.assertTrue(concordance)

    def test_concordance_small_values(self):
        """Test with very small effect sizes."""
        orig_effect = 1e-9
        rep_effect = 2e-9
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertTrue(concordance)

    def test_concordance_mixed_small_values(self):
        """Test with mixed small values of opposite sign."""
        orig_effect = -1e-9
        rep_effect = 2e-9
        concordance = calculate_concordance(orig_effect, rep_effect)
        self.assertFalse(concordance)


class TestMissingDataExclusion(unittest.TestCase):
    """Tests for missing data exclusion logic (get_common_lines)."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.orig_file = os.path.join(self.temp_dir, 'orig.csv')
        self.rep_file = os.path.join(self.temp_dir, 'rep.csv')

    def tearDown(self):
        """Clean up temporary files."""
        os.remove(self.orig_file)
        os.remove(self.rep_file)
        os.rmdir(self.temp_dir)

    def _write_csv(self, filepath, header, rows):
        """Helper to write CSV files."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    def test_common_lines_basic(self):
        """Test basic common line identification."""
        header = ['line_id', 'value']
        orig_rows = [['L1', 10], ['L2', 20], ['L3', 30]]
        rep_rows = [['L1', 100], ['L3', 300], ['L4', 400]]

        self._write_csv(self.orig_file, header, orig_rows)
        self._write_csv(self.rep_file, header, rep_rows)

        common_ids = get_common_lines(self.orig_file, self.rep_file, 'line_id')
        self.assertEqual(sorted(common_ids), ['L1', 'L3'])

    def test_missing_data_exclusion(self):
        """Test that lines with missing data in either file are excluded."""
        # Simulate missing data by leaving a cell empty or using 'NA'
        header = ['line_id', 'value']
        # L2 has value in orig, but 'NA' in rep
        # L4 has value in rep, but missing in orig
        orig_rows = [['L1', 10], ['L2', 20], ['L4', 40]]
        rep_rows = [['L1', 100], ['L2', 'NA'], ['L3', 300]]

        self._write_csv(self.orig_file, header, orig_rows)
        self._write_csv(self.rep_file, header, rep_rows)

        # The function should ideally handle 'NA' or empty strings as missing
        # and exclude them.
        common_ids = get_common_lines(self.orig_file, self.rep_file, 'line_id')
        # Only L1 should be common and valid (no missing data)
        # L2 is excluded because rep has 'NA'
        # L3 is missing in orig
        # L4 is missing in rep
        self.assertEqual(sorted(common_ids), ['L1'])

    def test_all_missing(self):
        """Test case where no common valid lines exist."""
        header = ['line_id', 'value']
        orig_rows = [['L1', 10]]
        rep_rows = [['L1', 'NA']]

        self._write_csv(self.orig_file, header, orig_rows)
        self._write_csv(self.rep_file, header, rep_rows)

        common_ids = get_common_lines(self.orig_file, self.rep_file, 'line_id')
        self.assertEqual(common_ids, [])

    def test_no_overlap(self):
        """Test case where there is no overlap in line IDs."""
        header = ['line_id', 'value']
        orig_rows = [['L1', 10], ['L2', 20]]
        rep_rows = [['L3', 30], ['L4', 40]]

        self._write_csv(self.orig_file, header, orig_rows)
        self._write_csv(self.rep_file, header, rep_rows)

        common_ids = get_common_lines(self.orig_file, self.rep_file, 'line_id')
        self.assertEqual(common_ids, [])


if __name__ == '__main__':
    unittest.main()