"""
Unit test to ensure the project does not import any CUDA‑specific modules.
Scans all Python files under the ``code`` directory for the presence of
``torch.cuda`` or ``device="cuda"`` patterns. The test fails if any such
occurrence is found, satisfying FR‑004.
"""
import pathlib
import re

def test_no_cuda_imports():
    """
    Fail if any source file under ``code/`` contains CUDA‑related strings.
    """
    project_root = pathlib.Path(__file__).resolve().parents[2]  # go up to project root
    code_dir = project_root / "code"

    # Patterns that indicate CUDA usage
    cuda_patterns = re.compile(r"torch\.cuda|device\s*=\s*['\"]cuda['\"]")

    for py_file in code_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if cuda_patterns.search(content):
            raise AssertionError(
                f"CUDA usage detected in {py_file.relative_to(project_root)}"
            )
