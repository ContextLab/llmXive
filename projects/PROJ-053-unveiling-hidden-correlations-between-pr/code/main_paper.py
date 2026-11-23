"""
Main entry point for T044: Paper Generation.

This script orchestrates the generation of docs/paper.md by:
1. Loading metrics from results/metrics.json
2. Loading normalization bounds from data/processed/normalization_bounds.json
3. Checking preprocessing logs for scope reduction notes
4. Generating the paper content
5. Saving to docs/paper.md
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ensure_directories
from utils.paper_generator import main as generate_paper_main
from utils.logger import setup_logging

def main():
    """Main entry point."""
    # Setup logging
    logger = setup_logging(
        name="main_paper",
        log_dir="logs",
        filename="main_paper.log"
    )
    
    logger.info("=" * 60)
    logger.info("Starting T044: Paper Generation")
    logger.info("=" * 60)
    
    try:
        # Ensure required directories exist
        ensure_directories()
        
        # Run the paper generation
        generate_paper_main()
        
        logger.info("T044: Paper generation completed successfully.")
        print("\n✓ T044: Paper generated at docs/paper.md")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Paper generation failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()