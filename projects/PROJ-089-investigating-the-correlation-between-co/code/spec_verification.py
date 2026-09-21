import os
import sys
from pathlib import Path
from datetime import datetime
import logging

from config import ensure_directories, get_config_summary

def read_file_safe(file_path: Path) -> str:
    """Read file content safely, returning empty string if not found."""
    try:
        return file_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return ""
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return ""

def analyze_contradiction(spec_content: str, plan_content: str) -> str:
    """
    Analyze the contradiction between spec and plan.
    
    Spec mandates: Raw metrics, Semgrep.
    Plan (Summary) claims: Density metrics, SonarQube.
    
    Returns a formatted log entry string.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # The specific contradiction identified in T000a
    deviation_msg = (
        f"{timestamp} | CRITICAL_DEVIATION | "
        f"Spec mandates Raw/Semgrep, Plan mandates Density/SonarQube | "
        f"ACTION: KICKBACK_REQUIRED"
    )
    
    return deviation_msg

def main():
    """
    Execute T000b: Log the deviation to data/logs/spec_verification.log.
    """
    # Ensure directories exist
    config = get_config_summary()
    ensure_directories(config)
    
    # Setup logging
    log_dir = Path(config["log_dir"])
    log_file = log_dir / "spec_verification.log"
    
    # Configure logger for this specific file
    logger = logging.getLogger("spec_verification")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers = []
    
    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Read artifacts (T000a logic embedded for context)
    # Note: In a real run, these paths would be relative to project root
    # For this task, we assume the paths are standard based on config
    # We use dummy content here because the task is specifically to LOG the 
    # known contradiction identified in T000a, not to re-read files that might not exist yet.
    # The contradiction is a fact of the project state.
    
    # The core action of T000b is to write the specific log entry format
    log_entry = analyze_contradiction("", "")
    
    # Write the log entry
    logger.info(log_entry)
    
    # Also print to stdout for immediate visibility
    print(f"Logged deviation to {log_file}:")
    print(log_entry)
    
    # Close handler
    fh.close()

if __name__ == "__main__":
    main()
