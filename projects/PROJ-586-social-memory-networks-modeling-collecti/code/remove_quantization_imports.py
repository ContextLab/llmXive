"""Utility script to remove 8‑bit/4‑bit quantization and CUDA imports
from all Python source files in the project.

The script scans every ``.py`` file under the ``code/`` directory,
removes lines that import modules commonly used for quantization
(e.g., ``bitsandbytes``) or CUDA (e.g., ``torch.cuda``) and rewrites
the files in‑place.  A short report is written to
``data/quantization_removal_report.txt`` listing all modified files.

Usage
-----
Run the script directly::

    python code/remove_quantization_imports.py

The script exits with status ``0`` on success.  If no prohibited
imports are found, the report will state that no changes were made.
"""

import pathlib
import re
import sys
from typing import List

# ----------------------------------------------------------------------
# Configuration – patterns that identify prohibited imports
# ----------------------------------------------------------------------
PROHIBITED_PATTERNS: List[re.Pattern] = [
    # bitsandbytes (commonly used for 8‑bit/4‑bit quantization)
    re.compile(r"""^\s*import\s+bitsandbytes\b"""),
    re.compile(r"""^\s*from\s+bitsandbytes\b.*import"""),
    # torch CUDA imports
    re.compile(r"""^\s*import\s+torch\.cuda\b"""),
    re.compile(r"""^\s*from\s+torch\s+import\s+cuda\b"""),
    re.compile(r"""^\s*import\s+torch\.nn\.quantized\b"""),
    re.compile(r"""^\s*from\s+torch\.nn\s+import\s+quantized\b"""),
    # generic quantization modules
    re.compile(r"""^\s*import\s+torch\.quantization\b"""),
    re.compile(r"""^\s*from\s+torch\.quantization\b.*import"""),
]

# ----------------------------------------------------------------------
def line_is_prohibited(line: str) -> bool:
    """Return ``True`` if the line matches any prohibited import pattern."""
    return any(pat.match(line) for pat in PROHIBITED_PATTERNS)

# ----------------------------------------------------------------------
def process_file(file_path: pathlib.Path) -> bool:
    """
    Remove prohibited import lines from *file_path*.

    Returns
    -------
    bool
        ``True`` if the file was modified, ``False`` otherwise.
    """
    original_text = file_path.read_text(encoding="utf-8")
    lines = original_text.splitlines(keepends=True)

    # Filter out prohibited lines while preserving line endings
    filtered_lines = [
        line for line in lines if not line_is_prohibited(line)
    ]

    if filtered_lines == lines:
        return False  # no change

    # Write back the cleaned content
    file_path.write_text("".join(filtered_lines), encoding="utf-8")
    return True

# ----------------------------------------------------------------------
def main() -> None:
    """
    Walk through the ``code/`` directory, clean each ``.py`` file,
    and write a short report.
    """
    project_root = pathlib.Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.is_dir():
        sys.stderr.write(f"Error: expected code directory at {code_dir}\\n")
        sys.exit(1)

    modified_files: List[pathlib.Path] = []

    for py_file in code_dir.rglob("*.py"):
        try:
            if process_file(py_file):
                modified_files.append(py_file.relative_to(project_root))
        except Exception as exc:
            sys.stderr.write(
                f"Failed to process {py_file}: {exc}\\n"
            )
            # Continue with other files – we do not abort the whole run
            continue

    # Write report
    report_path = project_root / "data" / "quantization_removal_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as report_file:
        if not modified_files:
            report_file.write("No prohibited imports were found. No files modified.\\n")
        else:
            report_file.write(
                f"Removed prohibited imports from {len(modified_files)} file(s):\\n"
            )
            for rel_path in sorted(modified_files):
                report_file.write(f"- {rel_path}\\n")

    print(f"Quantization/CUDA import cleanup complete. Report written to {report_path}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
