"""
Verification script for T009.
Runs the logging infrastructure to ensure it captures the required fields
and writes them to logs/run.log.
"""
import os
import sys
from pathlib import Path
import yaml

# Add code to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_handler import setup_logger, log_metric

def main():
    # Ensure project root is recognized
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Verify config exists
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        print("ERROR: code/config.yaml not found.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    log_file = config['logging']['file']
    log_path = Path(log_file)
    
    # Initialize logger
    logger = setup_logger(
        name="llmxive",
        log_file=log_file,
        level=logging.INFO
    )
    
    print(f"Logging initialized. Output will be written to: {log_path.absolute()}")
    
    # Log the verification message with required fields
    log_metric(
        logger,
        "Verification run: Environment configuration and logging infrastructure initialized.",
        reward_fidelity_level="dense",
        recovery_segment_id="init_001",
        task_id="T009",
        model_name="Verification"
    )
    
    # Verify the file was created and contains the line
    if not log_path.exists():
        print(f"ERROR: Log file {log_file} was not created.")
        sys.exit(1)
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    if "reward_fidelity_level=dense" in content:
        print("SUCCESS: logs/run.log contains 'reward_fidelity_level=dense'")
    else:
        print("ERROR: logs/run.log does not contain 'reward_fidelity_level=dense'")
        print("Content preview:")
        print(content[:500])
        sys.exit(1)
        
    print("T009 Verification Complete.")

if __name__ == "__main__":
    main()