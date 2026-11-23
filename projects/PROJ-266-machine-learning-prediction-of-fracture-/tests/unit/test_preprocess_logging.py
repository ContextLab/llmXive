import os
import tempfile
import logging
from pathlib import Path
import pytest
import shutil

from code.data.preprocess import setup_logging, run_preprocessing
from code.utils.logger import get_logger

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    input_dir = Path(temp_base) / 'input'
    output_dir = Path(temp_base) / 'output'
    log_dir = Path(temp_base) / 'logs'
    
    input_dir.mkdir()
    output_dir.mkdir()
    log_dir.mkdir()
    
    yield {
        'base': temp_base,
        'input': input_dir,
        'output': output_dir,
        'log_dir': log_dir,
        'log_file': str(log_dir / 'test_preprocess.log')
    }
    
    # Cleanup
    shutil.rmtree(temp_base)

def create_test_image(path: Path, size=(128, 128)):
    """Create a simple test image."""
    from PIL import Image
    import numpy as np
    
    # Create a simple gradient image
    arr = np.random.randint(0, 255, size=size, dtype=np.uint8)
    img = Image.fromarray(arr)
    img.save(path)

def test_setup_logging_creates_file(temp_dirs):
    """Test that setup_logging creates the log file with correct format."""
    log_file = temp_dirs['log_file']
    
    # Setup logging
    setup_logging(log_file)
    
    # Get the logger and log a test message
    logger = get_logger('PREPROCESS')
    logger.info("Test preprocessing step")
    
    # Check log file exists
    assert Path(log_file).exists(), "Log file should be created"
    
    # Check log content has correct format
    with open(log_file, 'r') as f:
        content = f.read()
    
    assert 'PREPROCESS' in content, "Log should contain PREPROCESS prefix"
    assert 'Test preprocessing step' in content, "Log should contain the message"
    
    # Check format: timestamp - PREPROCESS - message
    lines = content.strip().split('\n')
    assert len(lines) >= 1, "Log should have at least one line"
    
    # Verify format pattern
    import re
    pattern = r'\d{4}-\d{2}-\d{2}.* - PREPROCESS - Test preprocessing step'
    assert any(re.search(pattern, line) for line in lines), \
        f"Log format incorrect. Expected pattern: {pattern}, Got: {lines[0]}"

def test_run_preprocessing_logs_steps(temp_dirs):
    """Test that run_preprocessing logs each step."""
    # Create test images
    for i in range(3):
        create_test_image(temp_dirs['input'] / f'test_{i}.png')
    
    # Run preprocessing
    run_preprocessing(
        temp_dirs['input'],
        temp_dirs['output'],
        log_file=temp_dirs['log_file']
    )
    
    # Check log file
    with open(temp_dirs['log_file'], 'r') as f:
        content = f.read()
    
    # Verify expected log entries
    assert 'PREPROCESS' in content, "Should log with PREPROCESS prefix"
    assert 'Starting preprocessing pipeline' in content
    assert 'Found 3 image files' in content
    assert 'Processing image' in content
    assert 'Saved processed image' in content
    assert 'Preprocessing pipeline completed' in content

def test_logging_format_matches_spec(temp_dirs):
    """Verify log format matches specification: %(asctime)s - PREPROCESS - %(message)s"""
    log_file = temp_dirs['log_file']
    
    setup_logging(log_file)
    logger = get_logger('PREPROCESS')
    logger.info("Sample message")
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "Log file should have content"
    
    # Check format
    import re
    for line in lines:
        line = line.strip()
        if line:
            # Should match: YYYY-MM-DD HH:MM:SS,mmm - PREPROCESS - message
            pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - PREPROCESS - .+$'
            assert re.match(pattern, line), f"Line format mismatch: {line}"