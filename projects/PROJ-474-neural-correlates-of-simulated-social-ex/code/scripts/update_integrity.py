import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.integrity import update_hashes, get_logger, IntegrityError

def main():
    logger = get_logger(__name__)
    logger.info("Script: update_integrity started")
    
    # Define paths
    data_dir = project_root / "data"
    
    try:
        update_hashes(data_dir)
        logger.info("Script: update_integrity completed successfully")
    except IntegrityError as e:
        logger.error(f"Integrity Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
