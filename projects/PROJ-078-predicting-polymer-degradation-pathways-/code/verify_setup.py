import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add code directory to path to import utils if needed, 
# though for this simple task we can do it without complex imports
# to avoid recursion issues seen in previous runs.

def verify_directories():
    """
    Verifies the existence of the required project directory structure.
    Returns a list of missing directories and the output of 'ls -R' for the root.
    """
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    root = Path(".")
    missing = []
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
        elif not full_path.is_dir():
            missing.append(f"{full_path} (exists but not a directory)")
    
    return missing

def generate_ls_output():
    """
    Generates the recursive listing of the directory structure.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["ls", "-R"],
            cwd=Path("."),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running ls -R: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'ls' command not found."

def append_to_log(missing_dirs, ls_output):
    """
    Appends the verification results to state/setup_log.txt.
    """
    log_path = Path("state/setup_log.txt")
    
    # Ensure state directory exists before writing
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_path, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"VERIFICATION RUN: {timestamp}\n")
        f.write(f"{'='*60}\n")
        
        if missing_dirs:
            f.write("STATUS: FAILED\n")
            f.write("Missing directories:\n")
            for d in missing_dirs:
                f.write(f"  - {d}\n")
        else:
            f.write("STATUS: PASSED\n")
            f.write("All required directories exist.\n")
        
        f.write("\n--- Directory Listing (ls -R) ---\n")
        f.write(ls_output)
        f.write("\n--- End of Listing ---\n\n")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting directory verification for T001b...")
    
    missing = verify_directories()
    
    if missing:
        logger.warning(f"Missing directories found: {missing}")
    else:
        logger.info("All required directories are present.")
    
    logger.info("Generating recursive directory listing...")
    ls_output = generate_ls_output()
    
    logger.info("Appending results to state/setup_log.txt...")
    append_to_log(missing, ls_output)
    
    if missing:
        logger.error("Verification failed. See state/setup_log.txt for details.")
        sys.exit(1)
    else:
        logger.info("Verification successful. See state/setup_log.txt for details.")
        sys.exit(0)

if __name__ == "__main__":
    main()
