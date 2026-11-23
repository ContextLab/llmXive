"""
Unit test to ensure the project does not import any CUDA-specific modules.
Satisfies FR-004.
"""
import pathlib
import re

def test_no_cuda_imports():
    project_root = pathlib.Path(__file__).resolve().parents[2]
    code_dir = project_root / "code"
    cuda_patterns = re.compile(r"torch\.cuda|device\s*=\s*['\"]cuda['\"]")

    for py_file in code_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if cuda_patterns.search(content):
            raise AssertionError(f"CUDA usage detected in {py_file.relative_to(project_root)}")
