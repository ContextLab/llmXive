"""
Documentation Generator for llmXive Results.

This module orchestrates the generation of the final documentation (docs/results.md)
by loading statistical reports and rendering them via the report generator.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any

from analysis.report_generator import load_stats_report, generate_report

logger = logging.getLogger(__name__)

def ensure_output_dirs(output_path: str) -> Path:
    """
    Ensures the directory for the output documentation exists.
    
    Args:
        output_path: The full path to the output file.
        
    Returns:
        The Path object for the output directory.
    """
    output_file = Path(output_path)
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")
    return output_dir

def main():
    """
    Main entry point for generating documentation.
    
    Loads the stats report from data/processed/stats_report.json
    and generates docs/results.md.
    """
    # Configuration
    stats_file = Path("data/processed/stats_report.json")
    output_file = Path("docs/results.md")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Check if stats file exists
    if not stats_file.exists():
        logger.error(f"Stats report not found at {stats_file}. Run analysis first.")
        raise FileNotFoundError(f"Stats report missing: {stats_file}")
    
    # Ensure output directory exists
    ensure_output_dirs(str(output_file))
    
    try:
        # Load the stats report
        logger.info(f"Loading stats report from {stats_file}")
        stats_data = load_stats_report(stats_file)
        
        if not stats_data:
            logger.warning("Stats report is empty. Generating empty documentation.")
            # We still generate a report, it will just note the missing data
        
        # Generate the report
        logger.info(f"Generating documentation at {output_file}")
        generate_report(stats_data, str(output_file))
        
        logger.info("Documentation generation complete.")
        
    except Exception as e:
        logger.error(f"Failed to generate documentation: {e}")
        raise

if __name__ == "__main__":
    main()
