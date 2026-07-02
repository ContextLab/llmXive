import unittest
import os
import csv
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.helpers import ensure_data_dirs, prepare_submission_row, append_to_submissions_csv

class TestDemographicsSubmission(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.data_raw_path = os.path.join(self.test_dir, "data", "raw")
        self.csv_path = os.path.join(self.data_raw_path, "submissions.csv")
        
        # Mock the ensure_data_dirs to use our temp path
        self.original_ensure = ensure_data_dirs
        ensure_data_dirs = lambda: os.makedirs(self.data_raw_path, exist_ok=True)
        
        # Ensure CSV exists with headers
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "user_id", "timestamp", "sequence", "submission_status", 
                    "session_timeout", "rating_count", "Professional_credibility",
                    "Professional_professionalism", "Minimalist_credibility",
                    "Minimalist_professionalism", "Low-Quality_credibility",
                    "Low-Quality_professionalism", "Neutral_credibility",
                    "Neutral_professionalism", "age", "education", "hashed_ip", "duplicate_flag"
                ])

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_demographics_columns_exist(self):
        """Verify that Age and Education columns are present in the CSV schema."""
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            self.assertIn("age", fieldnames, "Age column missing from CSV")
            self.assertIn("education", fieldnames, "Education column missing from CSV")

    def test_demographics_data_types(self):
        """Verify that Age is integer and Education is integer code 1-4."""
        test_row = {
            "user_id": "test_user_123",
            "timestamp": "2023-10-27T10:00:00",
            "sequence": "Professional,Minimalist,Low-Quality,Neutral",
            "submission_status": "complete",
            "session_timeout": "false",
            "rating_count": 8,
            "Professional_credibility": 5, "Professional_professionalism": 5,
            "Minimalist_credibility": 3, "Minimalist_professionalism": 3,
            "Low-Quality_credibility": 2, "Low-Quality_professionalism": 2,
            "Neutral_credibility": 4, "Neutral_professionalism": 4,
            "age": 25,
            "education": 2, # Bachelor's
            "hashed_ip": "abc123",
            "duplicate_flag": "false"
        }
        
        # Append test row
        append_to_submissions_csv(test_row, self.csv_path)
        
        # Read back and verify
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            last_row = rows[-1]
            
            self.assertEqual(int(last_row["age"]), 25, "Age should be integer 25")
            self.assertEqual(int(last_row["education"]), 2, "Education should be integer code 2")

    def test_education_codes(self):
        """Verify that education codes map correctly (1-4)."""
        test_rows = [
            {"age": 20, "education": 1}, # High School
            {"age": 22, "education": 2}, # Bachelor's
            {"age": 24, "education": 3}, # Master's
            {"age": 30, "education": 4}  # PhD
        ]
        
        for row in test_rows:
            base_row = {
                "user_id": f"user_{row['education']}",
                "timestamp": "2023-10-27T10:00:00",
                "sequence": "Professional,Minimalist,Low-Quality,Neutral",
                "submission_status": "complete",
                "session_timeout": "false",
                "rating_count": 8,
                "Professional_credibility": 5, "Professional_professionalism": 5,
                "Minimalist_credibility": 3, "Minimalist_professionalism": 3,
                "Low-Quality_credibility": 2, "Low-Quality_professionalism": 2,
                "Neutral_credibility": 4, "Neutral_professionalism": 4,
                "hashed_ip": f"hash_{row['education']}",
                "duplicate_flag": "false"
            }
            base_row.update(row)
            append_to_submissions_csv(base_row, self.csv_path)

        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Check last 4 rows
            for i, expected_code in enumerate([1, 2, 3, 4]):
                actual_code = int(rows[-(4-i)]["education"])
                self.assertEqual(actual_code, expected_code)

if __name__ == "__main__":
    unittest.main()