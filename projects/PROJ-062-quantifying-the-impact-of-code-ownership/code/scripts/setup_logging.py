"""
Script to initialize logging infrastructure for the pipeline.
This script ensures the log directory exists and the logger is configured.
It is called during project setup or pipeline initialization.
"""
import sys
from pathlib import Path

# Add code directory to path if running as script
code_path = Path(__file__).resolve().parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging_utils import configure_logging, LOG_FILE

def main():
    print("Initializing logging infrastructure...")
    log_file = configure_logging()
    print(f"Logging configured. Output file: {log_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
