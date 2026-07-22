"""
Documentation Generator for llmXive Research Pipeline.

This module orchestrates the generation of documentation files,
specifically `docs/results.md`, from the statistical analysis reports.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any
from analysis.report_generator import load_stats_report, generate_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Ensure the docs directory exists."""
    docs_path = Path("docs")
    docs_path.mkdir(exist_ok=True)
    logger.info(f"Ensured output directory exists: {docs_path}")
    return docs_path

def main():
    """
    Main entry point for generating documentation.
    
    1. Loads the statistical report from `data/processed/stats_report.json`.
    2. Ensures the `docs/` directory exists.
    3. Generates the `docs/results.md` report using the report generator.
    4. Logs success or failure.
    """
    try:
        # Ensure output directory
        ensure_output_dirs()
        
        # Load the stats report
        stats_path = Path("data/processed/stats_report.json")
        if not stats_path.exists():
            logger.error(f"Stats report not found at {stats_path}. "
                         "Please run the analysis tasks (T024a, T027) first.")
            return 1
        
        logger.info(f"Loading stats report from {stats_path}")
        report_data = load_stats_report(stats_path)
        
        if not report_data:
            logger.error("Failed to load or parse stats report.")
            return 1
        
        # Generate the Markdown report
        output_path = Path("docs/results.md")
        logger.info(f"Generating documentation at {output_path}")
        generate_report(report_data, output_path)
        
        logger.info("Documentation generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Error during documentation generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())