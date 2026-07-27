"""
Unit tests for the provenance management utilities.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from utils.provenance import (
    compute_sha256,
    load_provenance,
    save_provenance,
    register_source,
    update_source_checksum,
    add_processing_step
)
from config import get_data_path


def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(temp_path)
        # SHA-256 of "test data"
        expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
        assert checksum == expected
    finally:
        os.unlink(temp_path)


def test_load_provenance_missing_file():
    """Test loading provenance when file does not exist."""
    # This test assumes the real file might exist, so we mock the path
    with patch('utils.provenance.get_data_path') as mock_path:
        mock_path.return_value = Path(tempfile.gettempdir())
        # Ensure the file doesn't exist in temp
        fake_path = mock_path.return_value / "provenance.json"
        if fake_path.exists():
            fake_path.unlink()
        
        result = load_provenance()
        assert "sources" in result
        assert "created_at" in result
        assert "version" in result


def test_register_source_new():
    """Test registering a new source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('utils.provenance.get_data_path') as mock_path:
            mock_path.return_value = Path(tmpdir)
            
            register_source(
                source_id="test_zenodo",
                source_type="dataset",
                url="https://doi.org/10.5281/zenodo.12345",
                description="Test Zenodo dataset"
            )
            
            data = load_provenance()
            assert len(data["sources"]) == 1
            assert data["sources"][0]["id"] == "test_zenodo"
            assert data["sources"][0]["status"] == "pending_download"


def test_register_source_update():
    """Test updating an existing source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('utils.provenance.get_data_path') as mock_path:
            mock_path.return_value = Path(tmpdir)
            
            # Register initial
            register_source("test_id", "dataset", "url1", "desc1")
            
            # Update
            register_source("test_id", "dataset", "url2", "desc2")
            
            data = load_provenance()
            assert len(data["sources"]) == 1
            assert data["sources"][0]["url"] == "url2"
            assert data["sources"][0]["description"] == "desc2"


def test_update_source_checksum():
    """Test updating a source with a checksum."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy file
        test_file = Path(tmpdir) / "data.csv"
        test_file.write_text("col1,col2\n1,2")
        
        with patch('utils.provenance.get_data_path') as mock_path:
            mock_path.return_value = Path(tmpdir)
            
            # Register first
            register_source("check_id", "dataset", "http://test", "test")
            
            # Update checksum
            update_source_checksum("check_id", str(test_file))
            
            data = load_provenance()
            source = next(s for s in data["sources"] if s["id"] == "check_id")
            assert source["checksum"] is not None
            assert source["checksum_algorithm"] == "sha256"
            assert source["status"] == "downloaded"
            assert source["size_bytes"] == test_file.stat().st_size


def test_add_processing_step():
    """Test adding a processing step."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('utils.provenance.get_data_path') as mock_path:
            mock_path.return_value = Path(tmpdir)
            
            add_processing_step(
                step_id="step_1",
                action="deduplication",
                parameters={"method": "normalized_formula"}
            )
            
            data = load_provenance()
            assert len(data["processing_history"]) == 1
            assert data["processing_history"][0]["step_id"] == "step_1"
            assert data["processing_history"][0]["action"] == "deduplication"