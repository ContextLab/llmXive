"""
Script to create the required directory structure for the llmXive project.

This task (T002a) ensures the existence of:
- src/
- tests/
- data/raw/
- data/processed/
- models/
- templates/

It also generates a verification artifact `data/processed/directory_structure.txt`
to prove the structure was created successfully.
"""
import os
import sys
from pathlib import Path

# Import logger utilities from existing project code
try:
    from src.utils.logger import get_logger, log_info, log_error, log_debug
except ImportError:
    # Fallback for direct execution if src is not in path yet
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_info(msg): logging.info(msg)
    def log_error(msg): logging.error(msg)
    def log_debug(msg): logging.debug(msg)

def main():
    logger = get_logger("setup_dirs")
    log_info("Starting directory structure creation for T002a.")

    # Define project root (assuming code/ is the root for this agent's context, 
    # but we need to create dirs relative to the project root which is usually parent of 'code' or 'code' itself depending on layout.
    # Based on tasks.md: "Paths shown below assume single project - adjust based on plan.md structure"
    # And existing API: code/src/utils/config.py exists.
    # We will assume the script is run from the project root, or we calculate it relative to this file.
    # Let's assume the current working directory is the project root.
    project_root = Path.cwd()
    
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "models",
        "templates"
    ]

    created_count = 0
    skipped_count = 0
    error_count = 0

    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                log_info(f"Created directory: {dir_path}")
                created_count += 1
            else:
                log_debug(f"Directory already exists: {dir_path}")
                skipped_count += 1
        except PermissionError:
            log_error(f"Permission denied creating directory: {dir_path}")
            error_count += 1
        except Exception as e:
            log_error(f"Failed to create directory {dir_path}: {e}")
            error_count += 1

    # Generate verification artifact
    verification_file = project_root / "data" / "processed" / "directory_structure.txt"
    try:
        # Ensure data/processed exists first
        (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
        
        with open(verification_file, "w", encoding="utf-8") as f:
            f.write(f"# Directory Structure Verification for T002a\n")
            f.write(f"# Generated at: {Path.cwd()}\n\n")
            f.write(f"Directories created/verified:\n")
            for dir_path_str in required_dirs:
                full_path = project_root / dir_path_str
                exists = "YES" if full_path.exists() else "NO"
                f.write(f"- {dir_path_str}: {exists}\n")
            f.write(f"\nSummary:\n")
            f.write(f"  Created: {created_count}\n")
            f.write(f"  Skipped (existing): {skipped_count}\n")
            f.write(f"  Errors: {error_count}\n")
        
        log_info(f"Verification file written to: {verification_file}")
    except Exception as e:
        log_error(f"Failed to write verification file: {e}")
        error_count += 1

    if error_count > 0:
        log_error(f"Directory creation completed with {error_count} errors.")
        return 1
    
    log_info("Directory structure setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
