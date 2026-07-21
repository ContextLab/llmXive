"""
Runner script for code cleanup and refactoring analysis.
Orchestrates the cleanup process and generates a comprehensive report.
"""
import os
import sys
import json
from pathlib import Path
import logging
from cleanup_utils import generate_cleanup_report, main as cleanup_main

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_report(report: dict, output_path: Path) -> None:
    """Save the cleanup report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def run_cleanup_analysis(root_dir: Path, output_path: Path) -> dict:
    """
    Run the full cleanup analysis on the given directory.
    
    Args:
        root_dir: Root directory containing the code to analyze
        output_path: Path where the report will be saved
        
    Returns:
        The cleanup report dictionary
    """
    logger.info(f"Starting cleanup analysis for {root_dir}")
    
    # Generate the cleanup report
    report = generate_cleanup_report(root_dir)
    
    # Save the report
    save_report(report, output_path)
    
    # Print summary
    print("\n" + "="*60)
    print("CODE CLEANUP ANALYSIS COMPLETE")
    print("="*60)
    print(report['summary'])
    print("="*60)
    
    if report['files_with_issues']:
        print(f"\nFiles requiring attention ({len(report['files_with_issues'])}):")
        for file_info in report['files_with_issues'][:10]:  # Show first 10
            print(f"  - {file_info['file']}: {len(file_info['issues'])} issues")
        if len(report['files_with_issues']) > 10:
            print(f"  ... and {len(report['files_with_issues']) - 10} more")
    
    return report

def main():
    """Main entry point for the cleanup runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run code cleanup analysis')
    parser.add_argument('--root', '-r', type=Path, default=Path('code'),
                      help='Root directory to analyze (default: code/)')
    parser.add_argument('--output', '-o', type=Path, default=Path('data/processed/cleanup_report.json'),
                      help='Output file for the report (default: data/processed/cleanup_report.json)')
    
    args = parser.parse_args()
    
    if not args.root.exists():
        logger.error(f"Root directory does not exist: {args.root}")
        return 1
    
    try:
        report = run_cleanup_analysis(args.root, args.output)
        return 0 if report['total_issues'] == 0 else 1
    except Exception as e:
        logger.error(f"Cleanup analysis failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())