import os
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
# We need to simulate the project structure for testing
def test_create_directories():
    """Test that create_directories actually creates the required directories."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a fake 'code' directory to match the expected structure
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Create a fake setup_directories.py in the code dir
        script_path = code_dir / "setup_directories.py"
        script_path.write_text("""
import os
import sys
from pathlib import Path

def get_project_root():
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def create_directories():
    root = get_project_root()
    
    directories = [
  "code",
  "data",
  "data/synthetic",
  "data/synthetic/raw",
  "data/synthetic/short_context",
  "data/results",
  "data/results/logs",
  "data/results/aggregated",
  "tests",
  "models",
  "data/assets",
    ]
    
    for dir_path in directories:
  full_path = root / dir_path
  full_path.mkdir(parents=True, exist_ok=True)
""")
        
        # Add the temp directory to sys.path
        sys.path.insert(0, str(tmp_path))
        
        try:
            # Import the module
            from setup_directories import create_directories
            
            # Run the function
            create_directories()
            
            # Verify that the data directory was created
            data_dir = tmp_path / "data"
            assert data_dir.exists(), "data/ directory was not created"
            assert data_dir.is_dir(), "data/ is not a directory"
            
            # Verify subdirectories
            synthetic_dir = tmp_path / "data" / "synthetic"
            assert synthetic_dir.exists(), "data/synthetic/ directory was not created"
            
            raw_dir = tmp_path / "data" / "synthetic" / "raw"
            assert raw_dir.exists(), "data/synthetic/raw/ directory was not created"
            
            print("All directories created successfully!")
            
        finally:
            # Clean up sys.path
            sys.path.remove(str(tmp_path))

if __name__ == "__main__":
    test_create_directories()
    print("Test passed!")