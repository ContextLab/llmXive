import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys
import importlib

# We need to mock the path resolution to test in a temp directory
# because setup_data_dirs.py calculates paths relative to __file__

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create the expected structure: code/scripts/ inside tmp_path
    scripts_dir = tmp_path / "code" / "scripts"
    scripts_dir.mkdir(parents=True)
    
    # Create the actual script file in the temp location
    script_content = """
import os
import sys
from pathlib import Path

def setup_directories():
    base_path = Path(__file__).resolve().parent.parent
    project_root = base_path / "data"
    
    directories = [
  "raw",
  "derived",
  "gold_standard",
  "../artifacts"
    ]
    
    created_count = 0
    for dir_name in directories:
  target_path = project_root / dir_name if dir_name != "../artifacts" else base_path.parent / "artifacts"
  target_path = target_path.resolve()
  
  try:
      target_path.mkdir(parents=True, exist_ok=True)
      created_count += 1
  except Exception:
      return False
      
    return True

def main():
    success = setup_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
    script_file = scripts_dir / "setup_data_dirs.py"
    script_file.write_text(script_content)
    
    # Add a marker file to indicate test root
    (tmp_path / "code").touch()
    
    return tmp_path

def test_setup_directories_creates_structure(temp_project_root):
    """Test that setup_directories creates all required directories."""
    # Add the temp root to sys.path so we can import
    sys.path.insert(0, str(temp_project_root / "code" / "scripts"))
    
    try:
        # Import the module dynamically
        spec = importlib.util.spec_from_file_location("setup_data_dirs", temp_project_root / "code" / "scripts" / "setup_data_dirs.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the setup
        result = module.setup_directories()
        
        assert result is True, "setup_directories should return True"
        
        # Verify directories exist
        data_dir = temp_project_root / "data"
        assert (data_dir / "raw").exists(), "data/raw should exist"
        assert (data_dir / "derived").exists(), "data/derived should exist"
        assert (data_dir / "gold_standard").exists(), "data/gold_standard should exist"
        assert (temp_project_root / "artifacts").exists(), "artifacts should exist"
        
    finally:
        sys.path.remove(str(temp_project_root / "code" / "scripts"))

def test_setup_directories_idempotent(temp_project_root):
    """Test that running setup_directories multiple times doesn't fail."""
    sys.path.insert(0, str(temp_project_root / "code" / "scripts"))
    
    try:
        spec = importlib.util.spec_from_file_location("setup_data_dirs", temp_project_root / "code" / "scripts" / "setup_data_dirs.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run twice
        result1 = module.setup_directories()
        result2 = module.setup_directories()
        
        assert result1 is True
        assert result2 is True
        
    finally:
        sys.path.remove(str(temp_project_root / "code" / "scripts"))