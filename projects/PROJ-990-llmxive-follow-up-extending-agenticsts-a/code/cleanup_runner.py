import os
import sys
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from cleanup_utils import generate_cleanup_report, main as cleanup_main


def save_report(report: dict, output_path: Path) -> None:
    """
    Save the cleanup report to a JSON file.
    
    Args:
        report: The report dictionary to save.
        output_path: Path where the report will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Report saved to {output_path}")


def run_cleanup_analysis(root_dir: Path = None, output_file: Path = None) -> dict:
    """
    Run the cleanup analysis on the specified directory.
    
    Args:
        root_dir: The root directory to analyze. Defaults to 'code'.
        output_file: Path for the output report. Defaults to 'data/processed/cleanup_report.json'.
        
    Returns:
        The generated report dictionary.
    """
    if root_dir is None:
        root_dir = Path('code')
    if output_file is None:
        output_file = Path('data/processed/cleanup_report.json')
        
    logger.info(f"Running cleanup analysis on {root_dir}")
    
    try:
        report = generate_cleanup_report(root_dir, output_file)
        return report
    except Exception as e:
        logger.error(f"Error running cleanup analysis: {e}")
        raise


def main():
    """Main entry point for the cleanup runner script."""
    # Default paths
    root_dir = Path('code')
    output_file = Path('data/processed/cleanup_report.json')
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        
    try:
        report = run_cleanup_analysis(root_dir, output_file)
        print(f"Cleanup analysis complete.")
        print(f"Total issues found: {report['total_issues']}")
        print(f"  - TODOs: {report['summary']['todo_count']}")
        print(f"  - Empty functions: {report['summary']['empty_function_count']}")
        print(f"  - Import issues: {report['summary']['import_issue_count']}")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
