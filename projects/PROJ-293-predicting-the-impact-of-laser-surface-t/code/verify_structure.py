"""
Verify that the project directory structure exists as required by T001.
Writes verification results to state/directory_verification.log.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports if needed (though this script is standalone)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging to file
log_path = project_root / "state" / "directory_verification.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

# Setup basic logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Required directories relative to project root
REQUIRED_DIRS = [
    "code",
    "data",
    "tests",
    "state",
    "models",
    "data/raw",
    "data/processed",
    "reports"
]

def verify_structure():
    """Check if all required directories exist."""
    logger.info(f"Starting directory structure verification at {datetime.now()}")
    logger.info(f"Project root: {project_root}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "directories": {},
        "all_present": True
    }

    missing_dirs = []
    existing_dirs = []

    for dir_name in REQUIRED_DIRS:
        full_path = project_root / dir_name
        exists = full_path.exists() and full_path.is_dir()
        
        results["directories"][dir_name] = {
            "path": str(full_path),
            "exists": exists
        }

        if exists:
            existing_dirs.append(dir_name)
            logger.info(f"✓ Found: {dir_name}")
        else:
            missing_dirs.append(dir_name)
            results["all_present"] = False
            logger.warning(f"✗ Missing: {dir_name}")

    logger.info("-" * 50)
    logger.info(f"Verification Summary:")
    logger.info(f"  Total directories checked: {len(REQUIRED_DIRS)}")
    logger.info(f"  Found: {len(existing_dirs)}")
    logger.info(f"  Missing: {len(missing_dirs)}")
    
    if missing_dirs:
        logger.error(f"Missing directories: {', '.join(missing_dirs)}")
        logger.info("Verification FAILED.")
        return False
    else:
        logger.info("All required directories exist.")
        logger.info("Verification PASSED.")
        return True

def main():
    """Main entry point for the verification script."""
    success = verify_structure()
    
    # Write summary to log file explicitly
    with open(Path(__file__).resolve().parent.parent / "state" / "directory_verification.log", 'a') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"FINAL RESULT: {'PASSED' if success else 'FAILED'}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()