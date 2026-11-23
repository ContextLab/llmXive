import os
import json
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import from src and scripts
code_root = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_setup_data_dirs_script_exists(temp_project_root):
    """Verify that the setup_data_dirs script exists."""
    script_path = code_root / "scripts" / "setup_data_dirs.py"
    assert script_path.exists(), f"Script not found at {script_path}"

def test_data_directories_exist_in_repo(temp_project_root):
    """
    Run the script to create directories and verify they exist.
    """
    # We need to mock the project root detection in the script or run it in the temp dir
    # For this test, we will run the script logic directly by patching the path or
    # simply checking that the script creates the dirs when run in a temp context.
    # However, the script assumes it is in code/scripts/ and finds root via parent.parent.
    # To test this reliably, we'll copy the script to a temp location that mimics the structure
    # or we can just import and call the function directly if we refactor, but for now
    # let's verify the structure by running the script in a controlled way.
    
    # Simpler approach: Create the structure manually using the function if we import it,
    # but the task asks for the script to be runnable.
    # Let's execute the script in a temporary directory structure that mimics the project.
    
    # Create a temp structure: temp_root/code/scripts/setup_data_dirs.py
    temp_scripts = temp_project_root / "code" / "scripts"
    temp_scripts.mkdir(parents=True)
    
    # Copy the actual script content to the temp location
    actual_script = code_root / "scripts" / "setup_data_dirs.py"
    if actual_script.exists():
        shutil.copy(actual_script, temp_scripts / "setup_data_dirs.py")
    
    # Create src and state dirs to satisfy imports if needed, though the script only uses relative imports for state_manager
    # We need to ensure the temp project has the 'code' structure so imports work
    (temp_project_root / "code" / "src").mkdir(parents=True)
    (temp_project_root / "code" / "state").mkdir(parents=True)
    
    # Copy necessary source files for imports to work
    # We need src/utils/state_manager.py
    src_utils = code_root / "src" / "utils"
    temp_src_utils = temp_project_root / "code" / "src" / "utils"
    temp_src_utils.mkdir(parents=True)
    if (src_utils / "state_manager.py").exists():
        shutil.copy(src_utils / "state_manager.py", temp_src_utils / "state_manager.py")
    if (src_utils / "__init__.py").exists():
        shutil.copy(src_utils / "__init__.py", temp_src_utils / "__init__.py")
    else:
        (temp_src_utils / "__init__.py").touch()
        
    # Also need src/__init__.py
    (temp_project_root / "code" / "src" / "__init__.py").touch()

    # Run the script
    result = subprocess.run(
        [sys.executable, str(temp_scripts / "setup_data_dirs.py")],
        cwd=str(temp_project_root),
        capture_output=True,
        text=True
    )
    
    # Check if script ran successfully
    assert result.returncode == 0, f"Script failed with: {result.stderr}"
    
    # Verify directories exist
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/references",
        "state"
    ]
    
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_checksums_file_exists_and_valid(temp_project_root):
    """
    Verify that the state file is created and contains valid checksums.
    """
    # Setup similar to above
    temp_scripts = temp_project_root / "code" / "scripts"
    temp_scripts.mkdir(parents=True)
    actual_script = code_root / "scripts" / "setup_data_dirs.py"
    if actual_script.exists():
        shutil.copy(actual_script, temp_scripts / "setup_data_dirs.py")
    
    (temp_project_root / "code" / "src").mkdir(parents=True)
    (temp_project_root / "code" / "state").mkdir(parents=True)
    
    src_utils = code_root / "src" / "utils"
    temp_src_utils = temp_project_root / "code" / "src" / "utils"
    temp_src_utils.mkdir(parents=True)
    if (src_utils / "state_manager.py").exists():
        shutil.copy(src_utils / "state_manager.py", temp_src_utils / "state_manager.py")
    if (src_utils / "__init__.py").exists():
        shutil.copy(src_utils / "__init__.py", temp_src_utils / "__init__.py")
    else:
        (temp_src_utils / "__init__.py").touch()
    (temp_project_root / "code" / "src" / "__init__.py").touch()

    # Run the script
    result = subprocess.run(
        [sys.executable, str(temp_scripts / "setup_data_dirs.py")],
        cwd=str(temp_project_root),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check state file
    state_file = temp_project_root / "state" / "state.json"
    assert state_file.exists(), "State file was not created"
    
    with open(state_file, 'r') as f:
        state_data = json.load(f)
    
    assert "task_id" in state_data, "State file missing task_id"
    assert state_data["task_id"] == "T019", f"Wrong task_id: {state_data['task_id']}"
    assert "checksums" in state_data, "State file missing checksums"
    assert isinstance(state_data["checksums"], dict), "Checksums should be a dict"
    
    # Verify expected directories are in checksums
    expected_dirs = ["data/raw", "data/processed", "data/artifacts", "data/references"]
    for d in expected_dirs:
        assert d in state_data["checksums"], f"Missing checksum for {d}"