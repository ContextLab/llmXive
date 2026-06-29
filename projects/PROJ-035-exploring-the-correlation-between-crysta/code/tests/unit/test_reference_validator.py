"""
Unit tests for the Reference Validator Agent.
"""

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from reference_validator import ReferenceValidator


class TestReferenceValidator(TestCase):
    """Tests for ReferenceValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.validator = ReferenceValidator(self.project_root)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_reference_patterns_slack_1979(self):
        """Test that Slack 1979 reference is detected."""
        test_cases = [
            "As described in Slack (1979), thermal conductivity...",
            "Following Slack, 1979 methodology...",
            "Slack et al. 1979 proposed...",
            "Reference: Slack, G. A. 1979",
        ]
        
        for content in test_cases:
            self.assertTrue(
                self.validator._find_reference(content, "Slack 1979"),
                f"Failed to detect Slack 1979 in: {content}"
            )
    
    def test_reference_patterns_smith_2021(self):
        """Test that Smith et al. 2021 reference is detected."""
        test_cases = [
            "Smith et al. 2021 established...",
            "Smith et al., 2021 reported...",
            "Smith et al (2021) found...",
            "Smith, J. et al. 2021",
        ]
        
        for content in test_cases:
            self.assertTrue(
                self.validator._find_reference(content, "Smith et al. 2021"),
                f"Failed to detect Smith et al. 2021 in: {content}"
            )
    
    def test_missing_reference_detection(self):
        """Test that missing references are properly detected."""
        content = "This document has no citations at all."
        
        self.assertFalse(
            self.validator._find_reference(content, "Slack 1979")
        )
        self.assertFalse(
            self.validator._find_reference(content, "Smith et al. 2021")
        )
    
    def test_validate_references_single_document(self):
        """Test validation of a single document with all references."""
        docs_dir = self.project_root / "data" / "results"
        docs_dir.mkdir(parents=True)
        
        test_doc = docs_dir / "test_report.md"
        test_doc.write_text(
            "## Report\n\n"
            "Based on Slack (1979) and Smith et al. 2021, we find...\n"
        )
        
        results = self.validator.validate_references(test_doc)
        
        self.assertTrue(results["Slack 1979"])
        self.assertTrue(results["Smith et al. 2021"])
    
    def test_validate_references_missing_citations(self):
        """Test validation of a document missing required references."""
        docs_dir = self.project_root / "data" / "results"
        docs_dir.mkdir(parents=True)
        
        test_doc = docs_dir / "incomplete_report.md"
        test_doc.write_text(
            "## Report\n\n"
            "This report lacks proper citations.\n"
        )
        
        results = self.validator.validate_references(test_doc)
        
        self.assertFalse(results["Slack 1979"])
        self.assertFalse(results["Smith et al. 2021"])
    
    def test_validate_all_documents(self):
        """Test validation across multiple documents."""
        docs_dir = self.project_root / "data" / "results"
        docs_dir.mkdir(parents=True)
        
        doc1 = docs_dir / "complete.md"
        doc1.write_text(
            "Slack (1979) and Smith et al. 2021 support our findings.\n"
        )
        
        doc2 = docs_dir / "incomplete.md"
        doc2.write_text(
            "No citations here.\n"
        )
        
        results = self.validator.validate_all_documents()
        
        self.assertIn("data/results/complete.md", results)
        self.assertIn("data/results/incomplete.md", results)
        self.assertTrue(results["data/results/complete.md"]["Slack 1979"])
        self.assertFalse(results["data/results/incomplete.md"]["Slack 1979"])
    
    def test_generate_report(self):
        """Test JSON report generation."""
        docs_dir = self.project_root / "data" / "results"
        docs_dir.mkdir(parents=True)
        
        test_doc = docs_dir / "report.md"
        test_doc.write_text(
            "Slack (1979) and Smith et al. 2021 are cited.\n"
        )
        
        validation_results = self.validator.validate_all_documents()
        report_path = self.validator.generate_report(validation_results)
        
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn("validation_timestamp", report)
        self.assertIn("required_references", report)
        self.assertIn("overall_status", report)
        self.assertIn("constitution_compliance", report)
        self.assertEqual(report["overall_status"], "passed")
    
    def test_run_empty_directory(self):
        """Test running validation when no documents exist."""
        results_dir = self.project_root / "data" / "results"
        results_dir.mkdir(parents=True)
        
        success, report_path = self.validator.run()
        
        self.assertFalse(success)
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report["overall_status"], "failed")
        self.assertEqual(report["error"], "No documents found to validate")
    
    def test_constitution_compliance_field(self):
        """Test that Constitution II compliance is properly tracked."""
        docs_dir = self.project_root / "data" / "results"
        docs_dir.mkdir(parents=True)
        
        test_doc = docs_dir / "report.md"
        test_doc.write_text(
            "Slack (1979) and Smith et al. 2021 are cited.\n"
        )
        
        validation_results = self.validator.validate_all_documents()
        report_path = self.validator.generate_report(validation_results)
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn("constitution_compliance", report)
        self.assertEqual(report["constitution_compliance"]["constitution_id"], "II")
        self.assertTrue(report["constitution_compliance"]["compliant"])
