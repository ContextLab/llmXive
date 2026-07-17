"""
Unit tests for validate_citations.py
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_citations import (
    extract_urls_from_markdown,
    verify_citations,
    load_manifest,
    CITATION_REGEX
)

class TestCitationRegex(unittest.TestCase):
    def test_valid_citation_format(self):
        """Test that standard citation format is captured."""
        text = "[^1]: https://example.com/path\nSome text"
        match = CITATION_REGEX.findall(text)
        self.assertEqual(match, ["https://example.com/path"])

    def test_citation_with_multiple_spaces(self):
        """Test handling of extra whitespace after colon."""
        text = "[^2]:    https://example.org/resource"
        match = CITATION_REGEX.findall(text)
        self.assertEqual(match, ["https://example.org/resource"])

    def test_citation_ignores_non_citation_links(self):
        """Test that standard markdown links [text](url) are not captured."""
        text = "[^3]: https://valid.com\n[Link](https://invalid.com)"
        match = CITATION_REGEX.findall(text)
        self.assertEqual(match, ["https://valid.com"])

class TestExtractUrls(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.specs_dir = Path(self.temp_dir) / "specs"
        self.specs_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_extract_from_single_file(self):
        md_file = self.specs_dir / "test.md"
        content = """
        # Test
        [^1]: https://example.com/one
        [^2]: https://example.com/two
        """
        md_file.write_text(content)

        result = extract_urls_from_markdown(str(self.specs_dir))
        self.assertIn(str(md_file), result)
        self.assertEqual(len(result[str(md_file)]), 2)

    def test_extract_from_nested_files(self):
        nested_dir = self.specs_dir / "subdir"
        nested_dir.mkdir()
        
        file1 = self.specs_dir / "root.md"
        file1.write_text("[^1]: https://root.com")
        
        file2 = nested_dir / "nested.md"
        file2.write_text("[^2]: https://nested.com")

        result = extract_urls_from_markdown(str(self.specs_dir))
        self.assertIn(str(file1), result)
        self.assertIn(str(file2), result)

    def test_empty_directory(self):
        result = extract_urls_from_markdown(str(self.specs_dir))
        self.assertEqual(result, {})

class TestVerifyCitations(unittest.TestCase):
    def test_all_verified(self):
        extracted = {"file.md": ["https://a.com", "https://b.com"]}
        verified = {"https://a.com", "https://b.com"}
        report = verify_citations(extracted, verified)
        
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verified_count"], 2)
        self.assertEqual(report["unverified_count"], 0)

    def test_some_missing(self):
        extracted = {"file.md": ["https://a.com", "https://b.com"]}
        verified = {"https://a.com"}
        report = verify_citations(extracted, verified)
        
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["verified_count"], 1)
        self.assertEqual(report["unverified_count"], 1)
        self.assertIn("file.md", report["details"]["missing_citations"])

    def test_empty_extraction(self):
        extracted = {}
        verified = {"https://a.com"}
        report = verify_citations(extracted, verified)
        
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["total_unique_citations"], 0)

class TestLoadManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = Path(self.temp_dir) / "manifest.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_valid_manifest(self):
        data = {"verified_urls": ["https://test.com"]}
        self.manifest_path.write_text(json.dumps(data))
        
        result = load_manifest(str(self.manifest_path))
        self.assertEqual(result, {"https://test.com"})

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_manifest("/nonexistent/path.json")

    def test_missing_key(self):
        self.manifest_path.write_text(json.dumps({"other_key": []}))
        with self.assertRaises(ValueError):
            load_manifest(str(self.manifest_path))

if __name__ == "__main__":
    unittest.main()