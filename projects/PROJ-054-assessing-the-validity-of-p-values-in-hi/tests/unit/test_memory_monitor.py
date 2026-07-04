import pytest
import numpy as np
import logging
import io
import sys
import resource
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.simulation import check_memory_limit, get_current_rss_mb, MEMORY_WARNING_THRESHOLD_BYTES
from utils.simulation import SimulationOrchestrator, SimulationConfig

@pytest.fixture
def logger_stream():
    """Capture log output."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('utils.simulation')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    yield stream
    logger.removeHandler(handler)

def test_check_memory_limit_below_threshold(logger_stream):
    """Test that no warning is logged when memory is below threshold."""
    # Mock resource to return a low value (e.g., 1 GB)
    mock_usage = MagicMock()
    mock_usage.ru_maxrss = 1024 * 1024  # 1 GB in KB (Linux assumption)
    
    with patch('utils.simulation.resource.getrusage', return_value=mock_usage):
        check_memory_limit(threshold_bytes=MEMORY_WARNING_THRESHOLD_BYTES)
    
    log_output = logger_stream.getvalue()
    assert "Memory usage threshold exceeded" not in log_output

def test_check_memory_limit_above_threshold(logger_stream):
    """Test that a warning is logged when memory exceeds 6GB."""
    # Mock resource to return a high value (e.g., 7 GB)
    # 7 GB = 7 * 1024 MB = 7168 MB = 7340032 KB
    mock_usage = MagicMock()
    mock_usage.ru_maxrss = 7 * 1024 * 1024  # 7 GB in KB
    
    with patch('utils.simulation.resource.getrusage', return_value=mock_usage):
        check_memory_limit(threshold_bytes=MEMORY_WARNING_THRESHOLD_BYTES)
    
    log_output = logger_stream.getvalue()
    assert "Memory usage threshold exceeded" in log_output
    assert "7.00 GB" in log_output or "7.0" in log_output

def test_orchestrator_memory_monitoring_integration():
    """
    Integration test: Run an orchestrator with a mock that forces high memory usage
    and verify the warning is logged during execution.
    """
    config = SimulationConfig(
        n_values=[10],
        p_values=[10],
        rho_values=[0.0],
        distribution_types=["normal"],
        n_iterations=1,
        seed_base=1,
        memory_warning_threshold_bytes=6 * 1024 * 1024 * 1024  # 6 GB
    )
    
    orchestrator = SimulationOrchestrator(config)
    
    # Mock _generate_data to simulate high memory usage
    def mock_generate_data(seed, n, p, rho, dist_type):
        # Simulate high memory usage by creating a large array
        # 100 million floats * 8 bytes = 800 MB. Not enough for 6GB.
        # We need to mock the check_memory_limit call inside to force a warning
        # or mock resource.getrusage globally during the run.
        
        # Instead, we patch resource.getrusage during the run to return high value
        pass 
    
    # We will patch the check_memory_limit function to verify it gets called
    # and that the underlying logic triggers a warning when mocked high.
    
    with patch('utils.simulation.resource.getrusage') as mock_rusage:
        # Set up the mock to return 7GB
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 7 * 1024 * 1024 # 7GB in KB
        mock_rusage.return_value = mock_usage
        
        # Capture logs
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger('utils.simulation')
        logger.addHandler(handler)
        
        try:
            orchestrator.run_simulation()
        finally:
            logger.removeHandler(handler)
        
        log_output = stream.getvalue()
        # Verify that the warning was triggered at least once (likely twice: during gen and after)
        assert "Memory usage threshold exceeded" in log_output
