"""
Main entry point for the llmXive project.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.setup_data_dirs import setup_data_directories
from utils.logging import setup_logging, get_logger, info, error

logger = get_logger(__name__)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--setup", action="store_true", help="Setup data directories")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(__import__('logging'), args.log_level.upper(), logging.INFO)
    setup_logging(log_level=log_level)
    
    info("Starting llmXive project...")
    
    if args.setup:
        try:
            setup_data_directories()
            info("Data directories setup complete.")
        except Exception as e:
            error(f"Failed to setup data directories: {e}")
            sys.exit(1)
    
    info("Project initialized successfully.")

if __name__ == "__main__":
    main()
