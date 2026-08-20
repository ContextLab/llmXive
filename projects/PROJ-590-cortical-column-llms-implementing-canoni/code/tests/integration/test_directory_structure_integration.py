import os
import pytest
from pathlib import Path
import tempfile
import sys

# Add project root to path if running as module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.setup_directories import ensure_directory_structure, create_state_template

def test_full_directory_creation_flow():
    """
    Integration test for T001c: Verify the full flow of directory creation.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "project"
        root.mkdir()
        
        # Execute the setup logic
        created = ensure_directory_structure(root)
        template = create_state_template(root)
        
        # Verify directories
        expected_dirs = [
            "tests/unit",
            "tests/integration",
            "scripts",
            "data/results",
            "data/logs",
            "data/configs",
            "state",
        ]
        
        for rel_path in expected_dirs:
            full_path = root / rel_path
            assert full_path.exists(), f"Directory {rel_path} was not created"
            assert full_path.is_dir(), f"{rel_path} is not a directory"
            # Check for __init__.py
            init_file = full_path / "__init__.py"
            assert init_file.exists(), f"__init__.py missing in {rel_path}"
        
        # Verify state template
        assert template.exists(), "state/template.yaml was not created"
        content = template.read_text()
        assert "project_id" in content, "Template missing project_id"
        assert "version" in content, "Template missing version"
        
        print("Integration test passed: All directories and templates created correctly.")