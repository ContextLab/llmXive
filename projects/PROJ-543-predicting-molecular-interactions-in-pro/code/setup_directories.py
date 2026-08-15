import os
import sys
from pathlib import Path
from utils.io import setup_logging, log_exception

def create_directories():
    """
    Create the required directory structure for the project:
    data/raw/, data/processed/, data/results/, tests/, specs/
    
    Returns:
        list: List of created directory paths as strings
    """
    base_dir = Path(__file__).resolve().parent.parent
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "specs"
    ]
    
    created_paths = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            logging = setup_logging()
            if logging:
                logging.info(f"Created directory: {full_path}")
            else:
                # Fallback if logging not fully initialized yet
                print(f"Created directory: {full_path}")
        except OSError as e:
            error_msg = f"Failed to create directory {full_path}: {e}"
            log_exception(e)
            print(error_msg, file=sys.stderr)
            raise
    
    return created_paths

def main():
    """Main entry point for directory creation."""
    try:
        logging = setup_logging()
        if logging:
            logging.info("Starting directory creation task T009")
        else:
            print("Starting directory creation task T009")
        
        created = create_directories()
        
        if logging:
            logging.info(f"Successfully created {len(created)} directories")
        else:
            print(f"Successfully created {len(created)} directories")
        
        for path in created:
            if logging:
                logging.info(f"  - {path}")
            else:
                print(f"  - {path}")
                
    except Exception as e:
        log_exception(e)
        print(f"Task T009 failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()