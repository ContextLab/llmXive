"""
Verification script for T009: Logging infrastructure setup.
Verifies that config.yaml exists and the logging handler captures
reward_fidelity_level and recovery_segment_id.
"""
import os
import sys
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_handler import setup_logger, log_metric, load_config

def main():
    """Run verification checks for T009."""
    print("Starting T009 verification...")
    
    # 1. Verify config.yaml exists
    config_path = project_root / "code" / "config.yaml"
    if not config_path.exists():
        print("FAIL: config.yaml does not exist")
        return False
    
    print("PASS: config.yaml exists")
    
    # 2. Verify config content
    try:
        config = load_config(str(config_path))
        assert 'logging' in config, "Missing 'logging' section in config"
        assert 'metrics' in config['logging'], "Missing 'metrics' in logging section"
        
        required_metrics = ['reward_fidelity_level', 'recovery_segment_id']
        for metric in required_metrics:
            assert metric in config['logging']['metrics'], f"Missing {metric} in metrics"
        
        print("PASS: config.yaml contains required logging configuration")
    except Exception as e:
        print(f"FAIL: config.yaml validation error: {e}")
        return False
    
    # 3. Setup logger and log test metrics
    log_file = project_root / "logs" / "run.log"
    # Ensure logs directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logger(
        name="llmXive",
        log_file=str(log_file),
        level=20,  # INFO
        console_output=True
    )
    
    # Log the specific metrics required by T009
    log_metric(
        logger,
        "Initialization complete",
        reward_fidelity_level="dense",
        recovery_segment_id="test_segment_001",
        task_id="T009"
    )
    
    print("PASS: Logged reward_fidelity_level=dense and recovery_segment_id")
    
    # 4. Verify log file content
    if not log_file.exists():
        print("FAIL: logs/run.log was not created")
        return False
    
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # Check for required values
    if "reward_fidelity_level=dense" not in log_content and '"reward_fidelity_level": "dense"' not in log_content:
        print("FAIL: Log file does not contain reward_fidelity_level=dense")
        return False
    
    if "recovery_segment_id" not in log_content:
        print("FAIL: Log file does not contain recovery_segment_id")
        return False
    
    print("PASS: logs/run.log contains required metrics")
    print("\nT009 Verification: SUCCESS")
    print(f"Log file location: {log_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)