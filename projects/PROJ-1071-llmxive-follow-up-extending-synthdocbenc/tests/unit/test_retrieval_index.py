"""
Unit tests for retrieval_index.py
"""

import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, "code")

from retrieval_index import chunk_text, extract_text_from_pdf_page, build_index
from utils import pin_random_seed

def test_chunk_text_basic():
    """Test basic text chunking."""
    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)
    # Check overlap
    assert chunks[0][-10:] == chunks[1][:10]

def test_chunk_text_empty():
    """Test chunking empty text."""
    chunks = chunk_text("")
    assert chunks == []

def test_chunk_text_whitespace():
    """Test chunking whitespace-only text."""
    chunks = chunk_text("   \n\t  ")
    assert chunks == []

def test_chunk_text_overlap():
    """Test that overlap is correctly applied."""
    text = "0123456789" * 100
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) >= 2
    # Verify overlap
    end_first = chunks[0][-5:]
    start_second = chunks[1][:5]
    assert end_first == start_second

@patch('retrieval_index.fitz')
@patch('retrieval_index.pytesseract')
def test_extract_text_from_pdf_page_ocr_fallback(mock_tesseract, mock_fitz):
    """Test OCR fallback when native text extraction fails."""
    # Mock page with no native text
    mock_page = MagicMock()
    mock_page.get_text.return_value = ""
    mock_doc = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz.open.return_value = mock_doc
    
    # Mock image and OCR
    mock_pixmap = MagicMock()
    mock_pixmap.tobytes.return_value = b"fake_png_data"
    mock_page.get_pixmap.return_value = mock_pixmap
    
    mock_image = MagicMock()
    mock_tesseract.image_to_string.return_value = "Test OCR result"
    
    # Mock PIL Image
    with patch('retrieval_index.Image.open') as mock_img_open:
        mock_img_open.return_value = mock_image
        
        result = extract_text_from_pdf_page("fake.pdf", 0)
        
        assert result == "Test OCR result"
        mock_tesseract.image_to_string.assert_called_once()

@patch('retrieval_index.fitz')
def test_extract_text_from_pdf_page_native_text(mock_fitz):
    """Test native text extraction when available."""
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Native text extraction"
    mock_doc = MagicMock()
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz.open.return_value = mock_doc
    
    result = extract_text_from_pdf_page("fake.pdf", 0)
    
    assert result == "Native text extraction"
    mock_page.get_pixmap.assert_not_called()

def test_build_index_empty_documents():
    """Test index building with empty document list."""
    index, metadata = build_index([])
    assert index is None
    assert metadata == []

def test_chunk_text_preserves_content():
    """Test that chunking preserves the original content."""
    text = "The quick brown fox jumps over the lazy dog."
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    reconstructed = "".join(chunks)
    # Content should be largely preserved (with overlaps)
    assert "quick brown" in reconstructed
    assert "lazy dog" in reconstructed

if __name__ == "__main__":
    test_chunk_text_basic()
    test_chunk_text_empty()
    test_chunk_text_whitespace()
    test_chunk_text_overlap()
    test_extract_text_from_pdf_page_ocr_fallback()
    test_extract_text_from_pdf_page_native_text()
    test_build_index_empty_documents()
    test_chunk_text_preserves_content()
    print("All tests passed.")
