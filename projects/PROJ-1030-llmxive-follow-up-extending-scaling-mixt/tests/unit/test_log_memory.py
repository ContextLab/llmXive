import pytest
import json
import os
import tempfile
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.log_memory import (
    get_memory_usage_mb,
    get_peak_memory_mb,
    generate_memory_log_entry,
    save_memory_log,
    log_memory_usage
)

def test_get_memory_usage_mb():
    """Test that memory usage is returned as a positive float."""
    mem = get_memory_usage_mb()
    assert isinstance(mem, float)
    assert mem > 0

def test_get_peak_memory_mb():
    """Test that peak memory usage is returned as a positive float."""
    peak = get_peak_memory_mb()
    assert isinstance(peak, float)
    assert peak > 0

def test_generate_memory_log_entry():
    """Test that the log entry dictionary has the correct structure."""
    entry = generate_memory_log_entry(
        clip_id="test_clip",
        stage="test_stage",
        memory_mb=100.5,
        peak_mb=150.0
    )
    
    assert entry["clip_id"] == "test_clip"
    assert entry["stage"] == "test_stage"
    assert entry["memory_mb"] == 100.5
    assert entry["peak_mb"] == 150.0
    assert "timestamp" in entry

def test_save_memory_log(tmp_path):
    """Test that save_memory_log writes a valid JSON file."""
    log_entries = [
        {"clip_id": "c1", "stage": "start", "memory_mb": 100, "timestamp": "t1", "peak_mb": 120},
        {"clip_id": "c1", "stage": "end", "memory_mb": 110, "timestamp": "t2", "peak_mb": 130}
    ]
    output_path = str(tmp_path / "memory_log.json")
    
    save_memory_log(log_entries, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["clip_id"] == "c1"

def test_log_memory_usage_integration(tmp_path, caplog):
    """Test the full log_memory_usage function integration."""
    import logging
    
    # Create a temporary logger
    logger = logging.getLogger("test_log_memory")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    log_entries = []
    output_path = str(tmp_path / "test_memory_log.json")
    
    log_memory_usage(
        clip_id="test_clip_1",
        stage="test_stage_1",
        log_entries=log_entries,
        output_path=output_path,
        logger=logger
    )
    
    assert len(log_entries) == 1
    assert log_entries[0]["clip_id"] == "test_clip_1"
    assert log_entries[0]["stage"] == "test_stage_1"
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == 1