"""CLI entry point for data cleaning."""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """Main entry point for clean CLI."""
    parser = argparse.ArgumentParser(description="Clean alloy data")
    parser.add_argument('--input', type=str, help='Input data file path')
    parser.add_argument('--output', type=str, help='Output data file path')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(level=args.log_level)
    if logger is None:
        logging.basicConfig(level=getattr(logging, args.log_level, logging.INFO))
        logger = logging.getLogger(__name__)
    
    logger.info("Starting data cleaning CLI")
    
    try:
        # Import and run cleaning pipeline
        from data.clean import run_cleaning_pipeline
        
        input_path = Path(args.input) if args.input else None
        output_path = Path(args.output) if args.output else None
        
        run_cleaning_pipeline(input_path, output_path)
        
        logger.info("Data cleaning completed successfully")
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
