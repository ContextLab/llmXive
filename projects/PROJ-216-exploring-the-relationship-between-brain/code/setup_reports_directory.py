import os
import sys
from pathlib import Path

def create_reports_directory(base_dir: str = ".") -> Path:
    """
    Creates the 'reports' directory under the specified base directory.
    
    Args:
        base_dir: The root directory where 'reports' will be created. Defaults to current directory.
        
    Returns:
        The Path object for the created 'reports' directory.
        
    Raises:
        OSError: If the directory cannot be created due to permissions or other OS-level errors.
    """
    reports_path = Path(base_dir) / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path

def verify_reports_directory(base_dir: str = ".") -> bool:
    """
    Verifies that the 'reports' directory exists and is a directory.
    
    Args:
        base_dir: The root directory where 'reports' is expected. Defaults to current directory.
        
    Returns:
        True if the directory exists, False otherwise.
    """
    reports_path = Path(base_dir) / "reports"
    return reports_path.is_dir()

def main():
    """
    Main entry point to create and verify the 'reports' directory.
    Prints status to stdout/stderr.
    """
    base_dir = "."
    try:
        reports_path = create_reports_directory(base_dir)
        print(f"Successfully created/ensured reports directory at: {reports_path}")
        
        if verify_reports_directory(base_dir):
            print("Verification passed: reports directory exists.")
            return 0
        else:
            print("Verification failed: reports directory does not exist after creation.", file=sys.stderr)
            return 1
    except OSError as e:
        print(f"Error creating reports directory: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
