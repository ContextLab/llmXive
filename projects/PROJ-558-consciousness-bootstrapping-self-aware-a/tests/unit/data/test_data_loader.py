import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We need to ensure the code path is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_loader import compute_checksum, save_dataset_and_manifest
from config import Config

def test_compute_checksum():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello World")
        temp_path = f.name

    try:
        checksum = compute_checksum(Path(temp_path))
        assert len(checksum) == 64  # SHA256 hex length
        # Verify determinism
        checksum2 = compute_checksum(Path(temp_path))
        assert checksum == checksum2
    finally:
        os.unlink(temp_path)

def test_save_dataset_and_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock paths
        data_dir = Path(tmpdir) / "data" / "raw"
        data_dir.mkdir(parents=True)
        manifest_path = Path(tmpdir) / "data" / "manifest.json"
        
        # Patch the global paths in data_loader module
        import data_loader
        original_raw_dir = data_loader.RAW_DATA_DIR
        original_manifest_path = data_loader.MANIFEST_PATH
        
        data_loader.RAW_DATA_DIR = data_dir
        data_loader.MANIFEST_PATH = manifest_path

        try:
            test_data = [{"text": "test content"}]
            filename = "test_dataset.json"
            
            save_dataset_and_manifest(test_data, filename, "test_type")
            
            # Verify file exists
            output_file = data_dir / filename
            assert output_file.exists()
            
            # Verify content
            with open(output_file) as f:
                loaded = json.load(f)
            assert loaded == test_data
            
            # Verify manifest
            assert manifest_path.exists()
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            assert filename in manifest
            assert manifest[filename]["type"] == "test_type"
            assert "checksum" in manifest[filename]
        finally:
            # Restore
            data_loader.RAW_DATA_DIR = original_raw_dir
            data_loader.MANIFEST_PATH = original_manifest_path
