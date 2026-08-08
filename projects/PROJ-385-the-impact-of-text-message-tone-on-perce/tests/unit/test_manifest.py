"""
Unit tests for T093: Manifest Generation and Validation.
"""
import json
import hashlib
import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the config or set up the environment
# Since config.py relies on relative paths, we might need to run this in the project context
# or mock get_project_root.
# For this test, we assume the test runs in the project root.

# Import the functions we want to test if possible, or just test the script behavior
# Since 99_manifest.py is a script, we can import main() or the helper functions.
# We'll import the helper logic by importing the module (if it's in sys.path)
# or by executing the script.

# Let's assume the test runs from the project root, so code/ is in path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_project_root, get_data_dir
from logging_config import setup_logging

# Import the manifest logic
# We need to import the specific functions from 99_manifest.py
# Since it's not a package, we might need to exec or import as module
# Let's assume we can import it as a module if we add code/ to path
# But 99_manifest.py is a script. Let's import the logic.
# Actually, let's just test the validation logic directly and the script execution.

def test_manifest_generation_creates_file():
    """Test that running the manifest script creates data/manifest.json"""
    setup_logging()
    project_root = get_project_root()
    manifest_path = project_root / "data" / "manifest.json"
    
    # Ensure data dir exists
    get_data_dir().mkdir(parents=True, exist_ok=True)
    
    # Create a dummy file to be included
    dummy_file = get_data_dir() / "test_dummy.txt"
    dummy_file.write_text("test content")
    
    try:
        # Import and run main
        # We need to import the module. Since it's a script, we might need to reload
        # or import it directly.
        import importlib.util
        spec = importlib.util.spec_from_file_location("manifest_gen", project_root / "code" / "99_manifest.py")
        manifest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manifest_module)
        
        # Run main
        # We might need to capture exit code or just run the logic
        # The main function returns 0 or 1
        result = manifest_module.main()
        
        assert result == 0, "Manifest generation failed"
        assert manifest_path.exists(), "Manifest file was not created"
        
        # Check content
        with open(manifest_path) as f:
            data = json.load(f)
        
        assert "artifacts" in data
        assert str(dummy_file.relative_to(project_root)) in data["artifacts"]
        
    finally:
        # Cleanup
        if dummy_file.exists():
            dummy_file.unlink()
        if manifest_path.exists():
            manifest_path.unlink()

def test_manifest_validation():
    """Test the validation script"""
    setup_logging()
    project_root = get_project_root()
    manifest_path = project_root / "data" / "manifest.json"
    
    # Create a fake manifest with a valid hash
    dummy_file = project_root / "data" / "test_val.txt"
    dummy_file.write_text("valid content")
    content_hash = hashlib.sha256(b"valid content").hexdigest()
    
    manifest_data = {
        "version": "1.0",
        "artifacts": {
            "data/test_val.txt": {
                "hash": content_hash,
                "size_bytes": 13
            }
        }
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)
        
    try:
        # Import validator
        import importlib.util
        spec = importlib.util.spec_from_file_location("val_manifest", project_root / "utils" / "validate_manifest.py")
        val_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(val_module)
        
        # Run validation
        result = val_module.validate(manifest_path)
        assert result is True, "Validation should pass for correct hash"
        
        # Test with wrong hash
        manifest_data["artifacts"]["data/test_val.txt"]["hash"] = "wronghash"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
            
        result = val_module.validate(manifest_path)
        assert result is False, "Validation should fail for wrong hash"
        
    finally:
        if dummy_file.exists():
            dummy_file.unlink()
        if manifest_path.exists():
            manifest_path.unlink()
