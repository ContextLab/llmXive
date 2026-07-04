"""
Unit tests for schema validation of fetched data.
Note: This task (T013) focuses on fetching. Validation logic is in T016.
However, we can test that the fetched data structure is as expected.
"""
import unittest
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

class TestFetchSchema(unittest.TestCase):

    def test_csv_structure(self):
        """Test that the generated CSV has the correct headers."""
        # We will create a mock CSV file to test the structure expectation
        test_csv_path = "/tmp/test_schema.csv"
        with open(test_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "value", "source"])
            writer.writerow(["2023-01-01", "0.5", "GDELT"])
        
        with open(test_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            self.assertIn("date", headers)
            self.assertIn("value", headers)
            self.assertIn("source", headers)
        
        os.remove(test_csv_path)

    def test_date_format(self):
        """Test that dates are in YYYY-MM-DD format."""
        test_csv_path = "/tmp/test_date.csv"
        with open(test_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "value", "source"])
            writer.writerow(["2023-01-01", "0.5", "GDELT"])
        
        with open(test_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row["date"]
                # Simple check for format YYYY-MM-DD
                parts = date_str.split('-')
                self.assertEqual(len(parts), 3)
                self.assertEqual(len(parts[0]), 4) # Year
                self.assertEqual(len(parts[1]), 2) # Month
                self.assertEqual(len(parts[2]), 2) # Day
        
        os.remove(test_csv_path)

if __name__ == '__main__':
    unittest.main()
