"""
Unit tests for inference logging utilities.
"""
import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from inference.logging_utils import (
    InferencePerformanceLog,
    log_inference_start,
    log_inference_batch,
    log_inference_summary,
    log_constraint_check,
    save_performance_log,
    create_performance_log_entry,
    get_logger_for_inference
)
from config import get_resource_limits

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock()

@pytest.fixture
def sample_log_entry():
    """Create a sample InferencePerformanceLog for testing."""
    return InferencePerformanceLog(
        model_id="test_model",
        start_time=time.time(),
        batch_count=0,
        samples_processed=0
    )

def test_log_inference_start(mock_logger):
    """Test initialization of inference logging."""
    log_entry = log_inference_start("test_model_v1", mock_logger)
    
    assert log_entry.model_id == "test_model_v1"
    assert log_entry.start_time is not None
    assert log_entry.batch_count == 0
    assert log_entry.samples_processed == 0
    assert log_entry.end_time is None
    
    # Verify logger was called
    mock_logger.info.assert_called_once()

def test_log_inference_batch(mock_logger, sample_log_entry):
    """Test logging of a single batch."""
    batch_size = 32
    duration_ms = 100.5
    
    updated_entry = log_inference_batch(
        sample_log_entry,
        batch_size=batch_size,
        duration_ms=duration_ms,
        logger=mock_logger
    )
    
    assert updated_entry.batch_count == 1
    assert updated_entry.samples_processed == batch_size
    assert updated_entry.avg_latency_ms is not None
    assert updated_entry.avg_latency_ms > 0

def test_log_inference_summary(mock_logger, sample_log_entry):
    """Test finalization of inference logging."""
    # Simulate some processing
    sample_log_entry.batch_count = 5
    sample_log_entry.samples_processed = 160
    
    # Patch time and memory tracking
    with patch('time.time', return_value=sample_log_entry.start_time + 1.0):
        with patch('tracemalloc.get_traced_memory', return_value=(1000000, 2000000)):
            with patch('tracemalloc.is_tracing', return_value=True):
                with patch('tracemalloc.stop'):
                    summary = log_inference_summary(sample_log_entry, mock_logger)
                    
                    assert summary.end_time is not None
                    assert summary.total_duration_ms is not None
                    assert summary.peak_ram_mb is not None
                    assert summary.avg_ram_mb is not None

def test_log_constraint_check(mock_logger, sample_log_entry):
    """Test constraint checking logic."""
    # Set up a log entry with known metrics
    sample_log_entry.total_duration_ms = 300000  # 5 minutes
    sample_log_entry.peak_ram_mb = 5000  # ~5 GB
    
    constraint_result = log_constraint_check(sample_log_entry, mock_logger)
    
    assert constraint_result.constraint_passed is not None
    assert constraint_result.constraint_details is not None
    assert "time_hours" in constraint_result.constraint_details
    assert "ram_gb" in constraint_result.constraint_details

def test_create_performance_log_entry(mock_logger):
    """Test creation of a standardized performance log entry."""
    entry = create_performance_log_entry(
        model_id="test_model",
        auc=0.95,
        latency_ms=150.0,
        ram_gb=4.5,
        constraint_passed=True,
        constraint_details={"time_passed": True, "ram_passed": True}
    )
    
    assert entry["model_id"] == "test_model"
    assert entry["auc"] == 0.95
    assert entry["latency_ms"] == 150.0
    assert entry["ram_gb"] == 4.5
    assert entry["constraint_passed"] is True
    assert "timestamp" in entry

def test_save_performance_log(mock_logger):
    """Test saving performance log to file."""
    log_entry = InferencePerformanceLog(
        model_id="save_test",
        start_time=time.time(),
        end_time=time.time() + 1.0,
        total_duration_ms=1000.0,
        batch_count=10,
        samples_processed=320,
        avg_latency_ms=3.125,
        peak_ram_mb=4000.0,
        constraint_passed=True
    )
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir)
        saved_path = save_performance_log(log_entry, output_dir=output_path, logger=mock_logger)
        
        assert saved_path.exists()
        assert saved_path.suffix == ".json"
        
        # Verify content
        with open(saved_path, 'r') as f:
            data = json.load(f)
            assert data["model_id"] == "save_test"
            assert data["total_duration_ms"] == 1000.0

def test_get_logger_for_inference():
    """Test retrieval of inference logger."""
    logger = get_logger_for_inference()
    assert logger is not None
    assert logger.name == "inference"