import json
import tempfile
from pathlib import Path
from unittest import TestCase
from reference_validator import ReferenceValidator

class TestReferenceValidator(TestCase):
    def setUp(self):
        self.test_data = {
            "citations": [
                {
                    "title": "Test Title",
                    "authors": ["Author A", "Author B"],
                    "year": 2021,
                    "journal": "Test Journal",
                    "doi": "10.1234/test"
                }
            ]
        }
        self.temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_data, self.temp_input)
        self.temp_input.close()
        
        self.temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_output.close()

    def tearDown(self):
        Path(self.temp_input.name).unlink()
        Path(self.temp_output.name).unlink()

    def test_load_citations(self):
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        citations = validator.load_citations()
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['title'], "Test Title")

    def test_validate_citation_format_valid(self):
        citation = {
            "title": "Test",
            "authors": ["A"],
            "year": 2021,
            "journal": "J"
        }
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        is_valid, msg = validator.validate_citation_format(citation)
        self.assertTrue(is_valid)

    def test_validate_citation_format_missing_fields(self):
        citation = {
            "title": "Test",
            "authors": ["A"]
        }
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        is_valid, msg = validator.validate_citation_format(citation)
        self.assertFalse(is_valid)
        self.assertIn("year", msg)

    def test_verify_title_token_overlap(self):
        citation = {"title": "Thermal Conductivity Study"}
        reference_text = "This study examines thermal conductivity in materials"
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        is_valid, score = validator.verify_title_token_overlap(citation, reference_text)
        self.assertTrue(is_valid)
        self.assertGreater(score, 0.5)

    def test_run_validation(self):
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        summary = validator.run_validation()
        self.assertIn('total_citations', summary)
        self.assertEqual(summary['total_citations'], 1)
        self.assertTrue(summary['format_valid_count'] >= 0)

    def test_save_results(self):
        validator = ReferenceValidator(self.temp_input.name, self.temp_output.name)
        summary = validator.run_validation()
        validator.save_results(summary)
        self.assertTrue(Path(self.temp_output.name).exists())
        with open(self.temp_output.name, 'r') as f:
            saved = json.load(f)
        self.assertEqual(saved['total_citations'], 1)