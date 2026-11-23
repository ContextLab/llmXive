import seed
import pathlib
import logging

# Set up basic logging for directory creation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_directory_structure():
    """
    Create the required directory structure for the project.
    
    This function ensures that all base directories required by the 
    research pipeline exist at the project root.
    """
    required_dirs = [
        'data/raw',
        'data/processed',
        'results',
        'logs',
        'code',
        'tests'
    ]
    for d in required_dirs:
        p = pathlib.Path(d)
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")
