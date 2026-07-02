import pytest
import json
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.download import generate_manifest_template, fetch_viral_genomes, fetch_geo_data, main
from src.config import DATA_RAW_PATH

def test_fetch_viral_genomes_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        fetch_viral_genomes(["NC_000001"])

def test_fetch_geo_data_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        fetch_geo_data(["GSE000001"])

def test_main_logs_message(capsys):
    # Capture log output
    main()
    captured = capsys.readouterr()
    # The logging framework usually prints to stderr, but we check for the message
    assert "Download skeleton initialized" in captured.out or "Download skeleton initialized" in captured.err

def test_generate_manifest_template_creates_file(tmp_path):
    # Temporarily override DATA_RAW_PATH for testing if needed, 
    # but here we just verify the function creates a file in the expected location
    # relative to the project root.
    
    # We will call the function and then check if the file exists.
    # Since the function writes to a fixed path defined in config, 
    # we verify that path exists after the call.
    
    # Note: In a real CI environment, we might need to mock the path or ensure write permissions.
    # For this test, we assume the test runner has write access to the project data directory.
    
    result_path = generate_manifest_template()
    path_obj = Path(result_path)
    
    assert path_obj.exists(), f"Manifest file not created at {result_path}"
    
    with open(path_obj, 'r') as f:
        data = json.load(f)
    
    assert "accessions" in data
    assert "source" in data
    assert "timestamp" in data
    assert "version" in data
    assert "checksum_algorithm" in data
    assert data["checksum_algorithm"] == "sha256"
    assert isinstance(data["accessions"], list)
    assert isinstance(data["timestamp"], str)