import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    
    This function creates:
    - data/raw/ for raw input data
    - data/processed/ for processed data and analysis results
    
    Returns:
        dict: A dictionary containing the paths to the created directories
    """
    base_path = Path(__file__).parent.parent / 'data'
    raw_path = base_path / 'raw'
    processed_path = base_path / 'processed'
    
    # Create directories if they don't exist
    raw_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Create a .gitkeep file to ensure directories are tracked by git
    (raw_path / '.gitkeep').touch()
    (processed_path / '.gitkeep').touch()
    
    return {
        'base': str(base_path),
        'raw': str(raw_path),
        'processed': str(processed_path)
    }

if __name__ == '__main__':
    result = setup_data_directories()
    print(f"Data directories created successfully:")
    print(f"  Base: {result['base']}")
    print(f"  Raw: {result['raw']}")
    print(f"  Processed: {result['processed']}")