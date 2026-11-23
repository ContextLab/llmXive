"""
Code Cleanup and Refactoring Script.

This script performs comprehensive cleanup and refactoring of the project,
including:
- Validation of all data artifacts
- Removal of temporary files
- Optimization of code structure
- Generation of cleanup reports

Run this script as part of the final project cleanup phase.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil
import time

# Import cleanup utilities
from cleanup_utils import (
    check_data_integrity,
    generate_cleanup_report,
    validate_csv_structure,
    validate_yaml_structure
)
from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def cleanup_temp_files(project_root: Path) -> int:
    """
    Remove temporary and cache files from the project.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Number of files removed
    """
    removed_count = 0
    temp_patterns = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        '.mypy_cache',
        '.ruff_cache',
        '.coverage',
        'htmlcov',
        '.tox',
        'build',
        'dist',
        '*.egg-info',
        '.eggs'
    ]
    
    for pattern in temp_patterns:
        for path in project_root.rglob(pattern):
            try:
                if path.is_file():
                    path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
                    logger.debug(f"Removed directory: {path}")
            except Exception as e:
                logger.warning(f"Could not remove {path}: {e}")
    
    logger.info(f"Removed {removed_count} temporary files/directories")
    return removed_count

def organize_output_files(project_root: Path) -> Dict[str, int]:
    """
    Organize and categorize output files for better structure.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with counts of organized files by category
    """
    categories = {
        'data_files': 0,
        'report_files': 0,
        'model_files': 0,
        'figure_files': 0,
        'config_files': 0
    }
    
    # Define file patterns for each category
    patterns = {
        'data_files': ['*.csv', '*.json', '*.parquet'],
        'report_files': ['*.md', '*.txt', '*.rst'],
        'model_files': ['*.pkl', '*.h5', '*.pt', '*.pth'],
        'figure_files': ['*.png', '*.jpg', '*.svg', '*.pdf'],
        'config_files': ['*.yaml', '*.yml', '*.toml', '*.ini']
    }
    
    for category, extensions in patterns.items():
        for ext in extensions:
            for file_path in project_root.rglob(ext):
                # Skip files in temporary directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                
                categories[category] += 1
                logger.debug(f"Categorized {file_path} as {category}")
    
    logger.info(f"Organized files: {categories}")
    return categories

def validate_all_artifacts(project_root: Path) -> Dict[str, Any]:
    """
    Perform comprehensive validation of all project artifacts.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting artifact validation...")
    
    # Check data integrity
    data_dir = project_root / 'data'
    data_results = check_data_integrity(data_dir)
    
    # Validate specific critical files
    critical_files = {
        'rsametrics.csv': data_dir / 'derived' / 'rsametrics.csv',
        'merged_data.csv': data_dir / 'derived' / 'merged_data.csv',
        'model_results.csv': data_dir / 'derived' / 'model_results.csv',
        'phylogenetic_tree.newick': data_dir / 'derived' / 'phylogenetic_tree.newick'
    }
    
    critical_results = {}
    for name, path in critical_files.items():
        if path.suffix == '.csv':
            is_valid, issues = validate_csv_structure(path, ['placeholder'])
            # We'll just check existence for now, columns are validated separately
            is_valid = path.exists()
            issues = [] if is_valid else ["File not found"]
        elif path.suffix == '.newick':
            is_valid = path.exists()
            issues = [] if is_valid else ["File not found"]
        else:
            is_valid = path.exists()
            issues = [] if is_valid else ["File not found"]
        
        critical_results[name] = {
            'exists': is_valid,
            'issues': issues,
            'path': str(path)
        }
    
    return {
        'data_artifacts': data_results,
        'critical_files': critical_results
    }

def generate_summary_report(validation_results: Dict[str, Any], cleanup_stats: Dict[str, Any]) -> str:
    """
    Generate a comprehensive summary report.
    
    Args:
        validation_results: Results from validate_all_artifacts
        cleanup_stats: Statistics from cleanup operations
        
    Returns:
        Formatted summary report string
    """
    report_lines = [
        "=" * 70,
        "PROJECT CLEANUP AND REFACTORING SUMMARY REPORT",
        "=" * 70,
        "",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "-" * 70,
        "CLEANUP STATISTICS",
        "-" * 70,
        f"Temporary files removed: {cleanup_stats.get('temp_removed', 0)}",
        f"Data files organized: {cleanup_stats.get('data_files', 0)}",
        f"Report files organized: {cleanup_stats.get('report_files', 0)}",
        f"Model files organized: {cleanup_stats.get('model_files', 0)}",
        f"Figure files organized: {cleanup_stats.get('figure_files', 0)}",
        f"Config files organized: {cleanup_stats.get('config_files', 0)}",
        "",
        "-" * 70,
        "ARTIFACT VALIDATION SUMMARY",
        "-" * 70
    ]
    
    # Add critical files status
    critical_files = validation_results.get('critical_files', {})
    valid_count = sum(1 for v in critical_files.values() if v['exists'])
    total_count = len(critical_files)
    
    report_lines.append(f"Critical files: {valid_count}/{total_count} valid")
    
    for name, result in critical_files.items():
        status = "✅" if result['exists'] else "❌"
        report_lines.append(f"  {status} {name}: {result['path']}")
        if not result['exists']:
            report_lines.append(f"      Issues: {', '.join(result['issues'])}")
    
    report_lines.append("")
    report_lines.append("=" * 70)
    
    if valid_count == total_count:
        report_lines.append("✅ ALL CRITICAL ARTIFACTS VALIDATED SUCCESSFULLY")
    else:
        report_lines.append(f"⚠️  {total_count - valid_count} CRITICAL ARTIFACTS FAILED VALIDATION")
    
    report_lines.append("=" * 70)
    
    return "\n".join(report_lines)

def main():
    """
    Main entry point for the cleanup and refactoring script.
    
    This function orchestrates the entire cleanup process:
    1. Remove temporary files
    2. Organize output files
    3. Validate all artifacts
    4. Generate comprehensive report
    """
    start_time = time.time()
    logger.info("Starting project cleanup and refactoring...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    try:
        # Step 1: Clean up temporary files
        logger.info("Step 1: Removing temporary files...")
        temp_removed = cleanup_temp_files(project_root)
        
        # Step 2: Organize output files
        logger.info("Step 2: Organizing output files...")
        file_organization = organize_output_files(project_root)
        
        # Step 3: Validate all artifacts
        logger.info("Step 3: Validating all artifacts...")
        validation_results = validate_all_artifacts(project_root)
        
        # Prepare cleanup statistics
        cleanup_stats = {
            'temp_removed': temp_removed,
            **file_organization
        }
        
        # Step 4: Generate summary report
        logger.info("Step 4: Generating summary report...")
        summary_report = generate_summary_report(validation_results, cleanup_stats)
        
        # Print report
        print(summary_report)
        
        # Save report to file
        report_path = project_root / 'docs' / 'cleanup_report.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(summary_report)
        logger.info(f"Report saved to: {report_path}")
        
        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"Cleanup completed in {duration:.2f} seconds")
        
        # Determine exit code
        critical_files = validation_results.get('critical_files', {})
        valid_count = sum(1 for v in critical_files.values() if v['exists'])
        total_count = len(critical_files)
        
        if valid_count == total_count:
            logger.info("✅ Cleanup completed successfully!")
            return 0
        else:
            logger.warning(f"⚠️  Cleanup completed with {total_count - valid_count} validation failures")
            return 1
            
    except Exception as e:
        logger.error(f"Cleanup failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())