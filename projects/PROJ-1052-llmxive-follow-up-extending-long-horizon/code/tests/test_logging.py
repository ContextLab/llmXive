"""
Tests for the logging infrastructure (T009).
Verifies that config.yaml exists and that the logger captures
reward_fidelity_level and recovery_segment_id correctly.
"""
import os
import yaml
import logging
import tempfile
import shutil
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_handler import setup_logger, log_metric

def test_config_yaml_exists():
    """Verify config.yaml exists in the expected location."""
    config_path = Path("code/config.yaml")
    assert config_path.exists(), f"config.yaml not found at {config_path}"
    
    # Verify structure
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert 'logging' in config, "config.yaml missing 'logging' section"
    assert 'custom_fields' in config['logging'], "config.yaml missing 'custom_fields'"
    
    required_fields = ['reward_fidelity_level', 'recovery_segment_id']
    for field in required_fields:
        assert field in config['logging']['custom_fields'], f"Missing custom field: {field}"

def test_logger_captures_metrics():
    """Verify the logger captures reward_fidelity_level and recovery_segment_id."""
    # Create a temporary directory for test logs
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test_run.log")
    
    try:
        logger = setup_logger(
            name="test_logger",
            log_file=log_file,
            level=logging.INFO
        )
        
        # Log a message with specific metrics
        test_fid = "dense"
        test_seg = "seg_001"
        test_task = "task_99"
        
        log_metric(
            logger,
            f"Testing metric capture for {test_task}",
            reward_fidelity_level=test_fid,
            recovery_segment_id=test_seg,
            task_id=test_task,
            level=logging.INFO
        )
        
        # Read the log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Verify the structured log contains the fields
        assert f"reward_fidelity_level={test_fid}" in content, \
            f"Log missing reward_fidelity_level={test_fid}"
        assert f"recovery_segment_id={test_seg}" in content, \
            f"Log missing recovery_segment_id={test_seg}"
        assert f"task_id={test_task}" in content, \
            f"Log missing task_id={test_task}"
        
        # Verify JSON line exists
        import json
        lines = content.strip().split('\n')
        json_line = None
        for line in lines:
            if line.startswith('{'):
                json_line = line
                break
        
        assert json_line is not None, "No JSON structured line found in log"
        data = json.loads(json_line)
        assert data['metrics']['reward_fidelity_level'] == test_fid
        assert data['metrics']['recovery_segment_id'] == test_seg
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_default_fidelity_in_config():
    """Verify default_fidelity is set to 'dense' in config."""
    config_path = Path("code/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config['execution']['default_fidelity'] == "dense", \
        "Default fidelity in config.yaml is not 'dense'"
