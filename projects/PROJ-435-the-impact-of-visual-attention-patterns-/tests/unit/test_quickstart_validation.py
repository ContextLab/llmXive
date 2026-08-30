import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging_init import get_project_root
# We will mock the main execution logic for unit testing specific helpers
# Since 049_run_quickstart_validation is the script, we import its functions
# Note: In a real scenario, we might need to adjust imports if the module structure changes
# For now, we assume the functions are accessible or we test the logic via a mock file

def test_compute_file_hash():
    """Test that file hashing works correctly."""
    from code.utils.logging_init import get_project_root
    
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        # Import the function dynamically to avoid circular imports if any
        import importlib.util
        spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        hash_val = module.compute_file_hash(temp_path)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64 # SHA-256 hex length
        
        # Verify it's deterministic
        hash_val2 = module.compute_file_hash(temp_path)
        assert hash_val == hash_val2
    finally:
        os.unlink(temp_path)

def test_validate_artifact_missing():
    """Test validation of a non-existent file."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    fake_path = Path("/non/existent/file.txt")
    result = module.validate_artifact(fake_path)
    
    assert result["exists"] is False
    assert result["valid"] is False
    assert "does not exist" in result["message"]

def test_validate_artifact_exists():
    """Test validation of an existing file."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Use a known existing file in the project
    project_root = get_project_root()
    test_file = project_root / "code" / "049_run_quickstart_validation.py"
    
    if test_file.exists():
        result = module.validate_artifact(test_file)
        assert result["exists"] is True
        assert result["valid"] is True
        assert result["hash"] is not None
    else:
        pytest.skip("Test file not found in project structure")

def test_parse_quickstart_commands():
    """Test parsing of quickstart.md content."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create a mock quickstart content
    mock_content = """
    # Quickstart Guide
    
    ```bash
    python code/01_extract_empirical_outcome.py
    ```
    
    Verify that `data/derived/empirical_outcomes.csv` exists.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(mock_content)
        temp_path = Path(f.name)
    
    try:
        commands = module.parse_quickstart_commands(temp_path)
        assert len(commands) > 0
        
        # Check for run command
        run_commands = [c for c in commands if c["type"] == "run"]
        assert len(run_commands) > 0
        assert "01_extract_empirical_outcome.py" in run_commands[0]["command"]
        
        # Check for artifact check
        check_commands = [c for c in commands if c["type"] == "check"]
        assert len(check_commands) > 0
        assert "data/derived/empirical_outcomes.csv" in check_commands[0]["path"]
    finally:
        os.unlink(temp_path)

def test_run_script_success():
    """Test running a simple script that succeeds."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create a simple test script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        f.write("import sys; print('Success'); sys.exit(0)")
        temp_script = Path(f.name)
    
    try:
        success, stdout, stderr = module.run_script(temp_script)
        assert success is True
        assert "Success" in stdout
        assert stderr == ""
    finally:
        os.unlink(temp_script)

def test_run_script_failure():
    """Test running a script that fails."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_validator", code_path / "049_run_quickstart_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create a failing script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        f.write("import sys; print('Error'); sys.exit(1)")
        temp_script = Path(f.name)
    
    try:
        success, stdout, stderr = module.run_script(temp_script)
        assert success is False
        assert "Error" in stdout
    finally:
        os.unlink(temp_script)
