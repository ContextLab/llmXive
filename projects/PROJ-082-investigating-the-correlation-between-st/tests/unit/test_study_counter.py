"""
Unit tests for the study counter module (T014a).
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

# We need to add the code directory to the path to import the module
# In a real test runner, this would be handled by PYTHONPATH or setup.py
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from analysis.study_counter import load_extracted_studies, count_unique_studies, save_study_count

class TestStudyCounter(TestCase):
    def setUp(self):
        """Set up temporary directory and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_csv = Path(self.temp_dir) / "extracted_studies.csv"
        self.output_json = Path(self.temp_dir) / "study_count.json"

    def tearDown(self):
        """Clean up temporary files."""
        if self.input_csv.exists():
            self.input_csv.unlink()
        if self.output_json.exists():
            self.output_json.unlink()
        os.rmdir(self.temp_dir)

    def test_count_unique_studies_normal(self):
        """Test counting unique (Author, Year) pairs with normal data."""
        studies = [
            {"Author": "Smith", "Year": "2020"},
            {"Author": "Smith", "Year": "2020"}, # Duplicate
            {"Author": "Jones", "Year": "2019"},
            {"Author": "Smith", "Year": "2021"},
        ]
        count = count_unique_studies(studies)
        self.assertEqual(count, 3) # Smith 2020, Jones 2019, Smith 2021

    def test_count_unique_studies_empty(self):
        """Test counting with empty list."""
        count = count_unique_studies([])
        self.assertEqual(count, 0)

    def test_count_unique_studies_missing_fields(self):
        """Test handling of missing Author or Year."""
        studies = [
            {"Author": "Smith", "Year": "2020"},
            {"Author": "", "Year": "2020"}, # Missing Author
            {"Author": "Jones", "Year": ""}, # Missing Year
            {"Year": "2020"}, # Missing Author key
            {"Author": "Doe", "Year": "2020"},
        ]
        count = count_unique_studies(studies)
        self.assertEqual(count, 2) # Smith 2020, Doe 2020

    def test_load_and_save_integration(self):
        """Test loading from CSV and saving to JSON."""
        # Write mock CSV
        with open(self.input_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Author", "Year", "Tract"])
            writer.writeheader()
            writer.writerow({"Author": "A", "Year": "1", "Tract": "Arcuate"})
            writer.writerow({"Author": "B", "Year": "2", "Tract": "Cingulum"})
            writer.writerow({"Author": "A", "Year": "1", "Tract": "Uncinate"}) # Duplicate study

        # Load
        studies = load_extracted_studies(self.input_csv)
        self.assertEqual(len(studies), 3)

        # Count
        n = count_unique_studies(studies)
        self.assertEqual(n, 2)

        # Save
        save_study_count(n, self.output_json)

        # Verify JSON content
        self.assertTrue(self.output_json.exists())
        with open(self.output_json, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data, {"N": 2})