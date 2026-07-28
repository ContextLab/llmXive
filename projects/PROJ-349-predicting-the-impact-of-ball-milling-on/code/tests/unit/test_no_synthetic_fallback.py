import ast
import os
import re
from pathlib import Path
from typing import List, Set
import pytest

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Patterns to detect synthetic fallbacks
SYNTHETIC_PATTERNS = [
    r"generate_synthetic_",
    r"mock_",
    r"fake_",
    r"np\.random\.",
    r"numpy\.random\.",
    r"pd\.DataFrame\(\[\]",
    r"return\s+\[\]",
    r"return\s+None",
]

def get_python_files(directory: str = "code/src/ingest") -> List[Path]:
    """Get all Python files in the specified directory."""
    path = Path(directory)
    if not path.exists():
        return []
    return list(path.glob("*.py"))

def extract_try_except_blocks(file_path: Path) -> List[Dict[str, any]]:
    """Extract try-except blocks from a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.warning(f"Syntax error in {file_path}")
        return []
    
    blocks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            blocks.append({
                "try_start": node.lineno,
                "handlers": [
                    {
                        "type": ast.unparse(h.type) if hasattr(ast, 'unparse') else str(h.type),
                        "body": [ast.unparse(b) if hasattr(ast, 'unparse') else str(b) for b in h.body]
                    }
                    for h in node.handlers
                ]
            })
    return blocks

def has_synthetic_fallback_in_handler(handler_body: List[str]) -> bool:
    """Check if a handler body contains synthetic fallback patterns."""
    for line in handler_body:
        for pattern in SYNTHETIC_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
    return False

def has_only_allowed_fallbacks(file_path: Path) -> bool:
    """Check if a file only uses allowed fallbacks (logging, skipping)."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.warning(f"Syntax error in {file_path}")
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                handler_body = [ast.unparse(b) if hasattr(ast, 'unparse') else str(b) for b in handler.body]
                if has_synthetic_fallback_in_handler(handler_body):
                    # Check if it's a logging or skip action
                    is_allowed = any(
                        "logger.warning" in line or "logger.info" in line or "return []" in line
                        for line in handler_body
                    )
                    if not is_allowed:
                        logger.error(f"Synthetic fallback detected in {file_path}: {handler_body}")
                        return False
    return True

class TestNoSyntheticFallback:
    """Test that no ingestion scripts use synthetic fallbacks."""

    def test_no_synthetic_fallback_in_ingestion_scripts(self):
        """Verify that all ingestion scripts avoid synthetic data generation."""
        ingest_dir = "code/src/ingest"
        files = get_python_files(ingest_dir)
        
        assert len(files) > 0, "No ingestion scripts found in code/src/ingest"
        
        for file_path in files:
            assert has_only_allowed_fallbacks(file_path), \
                f"File {file_path} contains synthetic fallback patterns"

    def test_specific_files_no_synthetic(self):
        """Test specific ingestion files for synthetic fallbacks."""
        files_to_check = [
            "code/src/ingest/materials_project.py",
            "code/src/ingest/nist_repo.py",
            "code/src/ingest/arxiv_extractor.py"
        ]
        
        for file_path_str in files_to_check:
            file_path = Path(file_path_str)
            if file_path.exists():
                assert has_only_allowed_fallbacks(file_path), \
                    f"File {file_path} contains synthetic fallback patterns"