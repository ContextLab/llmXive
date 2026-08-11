"""CLI entry point for data extraction."""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """Main entry point for download CLI."""
    parser = argparse.ArgumentParser(description="Extract alloy data from sources")
    parser.add_argument('--input', type=str, help='Input data file path (optional)')
    parser.add_argument('--output', type=str, help='Output data file path')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(level=args.log_level)
    if logger is None:
        logging.basicConfig(level=getattr(logging, args.log_level, logging.INFO))
        logger = logging.getLogger(__name__)
    
    logger.info("Starting data extraction CLI")
    
    try:
        # Import and run extraction
        from data._download_logic import run_extraction
        
        output_path = Path(args.output) if args.output else None
        
        run_extraction(output_path)
        
        logger.info("Data extraction completed successfully")
        
    except Exception as e:
        logger.error(f"Data extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
