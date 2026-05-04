"""
Verify and fix data directory structure for T154.

This script checks for nested data/raw/raw/ directories and ensures
a flat data/raw/ structure as required by T007.

Usage:
    python verify_data_structure.py [--fix]
    
The --fix flag will remove any nested raw/raw/ directories found.
Without --fix, the script only reports issues.

Exit codes:
    0 - Structure is correct (no nested raw/raw/ directories)
    1 - Issues found (without --fix) or fix failed (with --fix)
"""
import os
import sys
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume script is in code/scripts/
    return Path(__file__).parent.parent.parent

def check_nested_raw_directories(data_dir: Path) -> list:
    """
    Check for nested data/raw/raw/ directories.
    
    Returns a list of paths that should not exist.
    """
    issues = []
    raw_dir = data_dir / "raw"
    
    if not raw_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist")
        return issues
    
    # Check for nested raw directories inside raw/
    for item in raw_dir.iterdir():
        if item.is_dir() and item.name == "raw":
            issues.append(item)
            logger.error(f"Found nested raw directory: {item}")
        
        # Also check subdirectories for nested raw
        for subitem in item.rglob("raw"):
            if subitem.is_dir():
                # Check if parent is also named raw
                if subitem.parent.name == "raw":
                    issues.append(subitem)
                    logger.error(f"Found deeply nested raw directory: {subitem}")
    
    return issues

def validate_data_structure(data_dir: Path) -> bool:
    """
    Validate that data directory has correct structure.
    
    Expected structure:
        data/
            raw/          (flat, no nested raw/)
            processed/
            results/ (optional, should be under processed/)
    
    Returns True if structure is valid.
    """
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    valid = True
    
    # Check raw directory exists
    if not raw_dir.exists():
        logger.warning(f"Raw directory does not exist: {raw_dir}")
        valid = False
    else:
        # Check for nested raw directories
        nested_raw = list(raw_dir.glob("raw"))
        if nested_raw:
            logger.error(f"Found nested raw directories: {nested_raw}")
            valid = False
    
    # Check processed directory exists
    if not processed_dir.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        valid = False
    
    # Check for results/ at wrong level (should be under processed/)
    results_dir = data_dir / "results"
    if results_dir.exists():
        logger.warning(f"Found results/ at data/ level (should be under processed/): {results_dir}")
        logger.warning("This may indicate legacy directory structure")
        valid = False
    
    return valid

def fix_nested_raw_directories(issues: list, dry_run: bool = False) -> bool:
    """
    Remove nested raw directories.
    
    Args:
        issues: List of paths to nested raw directories
        dry_run: If True, only report what would be done
    
    Returns:
        True if all issues were fixed (or no issues), False otherwise
    """
    if not issues:
        logger.info("No nested raw directories to fix")
        return True
    
    if dry_run:
        logger.warning("DRY RUN - No files will be modified")
        for issue in issues:
            logger.info(f"Would remove: {issue}")
        return False
    
    success = True
    for issue in issues:
        try:
            logger.info(f"Removing nested raw directory: {issue}")
            shutil.rmtree(issue)
            logger.info(f"Successfully removed: {issue}")
        except Exception as e:
            logger.error(f"Failed to remove {issue}: {e}")
            success = False
    
    return success

def main(fix: bool = False, dry_run: bool = False) -> int:
    """
    Main entry point for data structure verification.
    
    Args:
        fix: If True, attempt to fix issues found
        dry_run: If True, only report what would be done (implies fix=False)
    
    Returns:
        Exit code (0 for success, 1 for issues)
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    
    # Check for nested raw directories
    issues = check_nested_raw_directories(data_dir)
    
    if issues:
        logger.error(f"Found {len(issues)} nested raw directory issue(s)")
        
        if fix or dry_run:
            success = fix_nested_raw_directories(issues, dry_run=dry_run)
            if not success and not dry_run:
                logger.error("Some issues could not be fixed")
                return 1
            
            # Re-check after fix
            issues = check_nested_raw_directories(data_dir)
            if issues:
                logger.error("Nested raw directories still exist after fix attempt")
                return 1
            else:
                logger.info("Successfully fixed all nested raw directory issues")
        else:
            logger.error("Issues found. Run with --fix to correct them.")
            return 1
    else:
        logger.info("No nested raw directories found")
    
    # Validate overall structure
    if validate_data_structure(data_dir):
        logger.info("Data directory structure is valid")
        return 0
    else:
        logger.warning("Data directory structure has some issues")
        return 0  # Return 0 as long as nested raw is fixed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify and fix data directory structure"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues found"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    exit_code = main(fix=args.fix, dry_run=args.dry_run)
    sys.exit(exit_code)
