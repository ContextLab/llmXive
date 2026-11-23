"""
Unit tests for code/doc_generator.py.
Verifies synthetic document structure, middle-third metadata, and the 200-document count.
"""
import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(PROJECT_ROOT))

from doc_generator import (
    generate_text_block,
    calculate_text_density,
    generate_page,
    generate_document,
    save_document,
    generate_all_documents,
    compute_checksums,
    validate_documents
)
from models.document import Document, Page, MiddleThirdMetadata


class TestTextBlockGeneration(unittest.TestCase):
    """Tests for generate_text_block and calculate_text_density."""

    def test_generate_text_block_non_empty(self):
        """Verify that generated text blocks are not empty."""
        text = generate_text_block(min_words=50, max_words=100)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 0)
        words = text.split()
        self.assertGreaterEqual(len(words), 50)
        self.assertLessEqual(len(words), 100)

    def test_calculate_text_density_positive(self):
        """Verify text density calculation returns a positive float."""
        text = "This is a test paragraph with some words."
        width = 800
        height = 600
        density = calculate_text_density(text, width, height)
        self.assertIsInstance(density, float)
        self.assertGreater(density, 0.0)


class TestPageGeneration(unittest.TestCase):
    """Tests for generate_page."""

    def test_generate_page_structure(self):
        """Verify generated page has required fields."""
        page_data = generate_page(page_num=1, width=800, height=600)
        
        self.assertIn('page_num', page_data)
        self.assertIn('width', page_data)
        self.assertIn('height', page_data)
        self.assertIn('text', page_data)
        self.assertIn('text_density', page_data)
        self.assertIn('is_middle_third', page_data)

        self.assertEqual(page_data['page_num'], 1)
        self.assertIsInstance(page_data['text'], str)
        self.assertIsInstance(page_data['text_density'], float)
        self.assertIsInstance(page_data['is_middle_third'], bool)


class TestDocumentGeneration(unittest.TestCase):
    """Tests for generate_document."""

    def test_generate_document_structure(self):
        """Verify generated document has required fields."""
        doc = generate_document(doc_id="test-001")
        
        self.assertIn('doc_id', doc)
        self.assertIn('pages', doc)
        self.assertIn('middle_third_metadata', doc)
        self.assertIn('total_pages', doc)

        self.assertEqual(doc['doc_id'], "test-001")
        self.assertIsInstance(doc['pages'], list)
        self.assertIsInstance(doc['middle_third_metadata'], dict)
        self.assertIsInstance(doc['total_pages'], int)

    def test_generate_document_middle_third_metadata(self):
        """Verify middle-third metadata is correctly populated."""
        doc = generate_document(doc_id="test-002")
        meta = doc['middle_third_metadata']
        
        self.assertIn('start_page', meta)
        self.assertIn('end_page', meta)
        self.assertIn('page_count', meta)
        self.assertIn('total_text_density', meta)
        self.assertIn('avg_text_density', meta)

        # Verify start and end pages are within bounds
        total_pages = doc['total_pages']
        self.assertGreaterEqual(meta['start_page'], 0)
        self.assertLessEqual(meta['end_page'], total_pages - 1)
        self.assertGreater(meta['page_count'], 0)

    def test_generate_document_page_count(self):
        """Verify document has a reasonable number of pages."""
        doc = generate_document(doc_id="test-003")
        # Documents should have between 10 and 50 pages typically
        self.assertGreaterEqual(doc['total_pages'], 10)
        self.assertLessEqual(doc['total_pages'], 50)


class TestDocumentValidation(unittest.TestCase):
    """Tests for validate_documents."""

    def test_validate_documents_pass(self):
        """Verify validation passes for valid documents."""
        # Create a temporary directory for test documents
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Generate a single valid document
            doc = generate_document(doc_id="valid-doc")
            save_document(doc, tmp_dir)
            
            # Validate the document
            is_valid, errors = validate_documents(tmp_dir)
            
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)

    def test_validate_documents_middle_third_check(self):
        """Verify validation checks middle-third metadata."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            doc = generate_document(doc_id="valid-doc-2")
            save_document(doc, tmp_dir)
            
            is_valid, errors = validate_documents(tmp_dir)
            
            # Should be valid because middle-third is properly generated
            self.assertTrue(is_valid)
            
            # Verify middle-third metadata exists and is valid
            meta = doc['middle_third_metadata']
            self.assertGreater(meta['page_count'], 0)
            self.assertGreater(meta['avg_text_density'], 0.0)


class TestDocumentCount(unittest.TestCase):
    """Tests for the 200-document count requirement."""

    def test_generate_all_documents_count(self):
        """Verify that generate_all_documents creates exactly 200 documents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Generate all documents
            generate_all_documents(output_dir=tmp_dir, num_documents=200)
            
            # Count the generated documents
            doc_files = [f for f in os.listdir(tmp_dir) if f.endswith('.json')]
            
            self.assertEqual(len(doc_files), 200)
            
            # Verify each document has the required structure
            for filename in doc_files:
                filepath = os.path.join(tmp_dir, filename)
                with open(filepath, 'r') as f:
                    doc = json.load(f)
                
                self.assertIn('doc_id', doc)
                self.assertIn('pages', doc)
                self.assertIn('middle_third_metadata', doc)
                self.assertIn('total_pages', doc)


class TestChecksums(unittest.TestCase):
    """Tests for compute_checksums."""

    def test_compute_checksums(self):
        """Verify checksum computation works correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Generate a document
            doc = generate_document(doc_id="checksum-test")
            save_document(doc, tmp_dir)
            
            # Compute checksums
            checksums = compute_checksums(tmp_dir)
            
            self.assertIsInstance(checksums, dict)
            self.assertIn('documents', checksums)
            self.assertGreater(len(checksums['documents']), 0)
            
            # Verify checksum format
            for doc_id, checksum in checksums['documents'].items():
                self.assertIsInstance(checksum, str)
                self.assertEqual(len(checksum), 64)  # SHA-256 hex length


if __name__ == '__main__':
    unittest.main()