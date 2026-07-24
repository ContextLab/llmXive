import os
import pytest
from pathlib import Path

def test_skeleton_files_exist():
    base_dir = Path(__file__).parent.parent.parent
    code_dir = base_dir / "code"
    docs_dir = base_dir / "docs"
    
    required_files = [
        code_dir / "config.yaml",
        code_dir / "download.py",
        code_dir / "preprocess.py",
        code_dir / "features.py",
        code_dir / "analysis.py",
        code_dir / "report.py",
        code_dir / "models" / "__init__.py",
        docs_dir / "README.md"
    ]
    
    missing = [f for f in required_files if not f.exists()]
    assert len(missing) == 0, f"Missing skeleton files: {missing}"