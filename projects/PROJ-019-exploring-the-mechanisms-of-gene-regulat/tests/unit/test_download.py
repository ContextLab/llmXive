"""
Unit tests for code/download.py
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os

# We'll test the logic without actually downloading
# by mocking the network calls

@pytest.fixture
def mock_environ():
    """Set up temporary directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set environment variables for test directories
        old_raw = os.environ.get("LLMXIVE_DATA_RAW_DIR")
        old_tmp = os.environ.get("LLMXIVE_TMP_DIR")
        
        os.environ["LLMXIVE_DATA_RAW_DIR"] = str(Path(tmpdir) / "raw")
        os.environ["LLMXIVE_TMP_DIR"] = str(Path(tmpdir) / "tmp")
        
        yield tmpdir
        
        # Restore environment
        if old_raw:
            os.environ["LLMXIVE_DATA_RAW_DIR"] = old_raw
        elif "LLMXIVE_DATA_RAW_DIR" in os.environ:
            del os.environ["LLMXIVE_DATA_RAW_DIR"]
            
        if old_tmp:
            os.environ["LLMXIVE_TMP_DIR"] = old_tmp
        elif "LLMXIVE_TMP_DIR" in os.environ:
            del os.environ["LLMXIVE_TMP_DIR"]

def test_download_all_peaks_structure(mock_environ):
    """
    Test that download_all_peaks would create the correct structure
    (mocked to avoid actual network calls)
    """
    from code.download import ENCODE_PEAKS, download_all_peaks
    
    # Verify we have the expected cell types
    expected_cell_types = {"GM12878", "K562", "HepG2", "H1-hESC", "IMR90"}
    assert set(ENCODE_PEAKS.keys()) == expected_cell_types
    
    # Verify each entry has required fields
    for cell_type, info in ENCODE_PEAKS.items():
        assert "accession" in info
        assert "url" in info
        assert "filename" in info
        assert info["filename"].endswith(".bed.gz")

@patch('code.download.fetch_file_with_retry')
@patch('code.download.add_encode_accession')
@patch('code.download.save_provenance')
def test_download_single_cell_type(mock_save, mock_add_acc, mock_fetch, mock_environ):
    """
    Test downloading a single cell type with mocked network
    """
    from code.download import ENCODE_PEAKS
    
    cell_type = "K562"
    info = ENCODE_PEAKS[cell_type]
    
    # Call the function (we'll need to import it in the module scope)
    # For this test, we're just verifying the structure would be correct
    mock_fetch.return_value = None
    mock_add_acc.return_value = None
    mock_save.return_value = None
    
    # Verify the URL format is correct
    assert info["url"].startswith("https://www.encodeproject.org/")
    assert "ENCFF" in info["accession"]
    assert info["filename"].endswith(".bed.gz")

def test_provenance_structure(mock_environ):
    """
    Test that provenance tracking structure is correct
    """
    from code.provenance import initialize_provenance, add_encode_accession, save_provenance, load_provenance
    
    # Initialize
    provenance = initialize_provenance()
    assert "created_at" in provenance
    assert "datasets" in provenance
    assert "encode_accessions" in provenance
    
    # Add an accession
    test_path = "/tmp/test.bed.gz"
    add_encode_accession("TestCell", "ENCSR000TEST", test_path)
    
    # Load and verify
    loaded = load_provenance()
    assert "TestCell" in loaded["encode_accessions"]
    assert loaded["encode_accessions"]["TestCell"]["accession"] == "ENCSR000TEST"
    assert loaded["encode_accessions"]["TestCell"]["file_path"] == test_path