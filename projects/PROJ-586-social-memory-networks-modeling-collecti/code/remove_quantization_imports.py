"""
T032: Remove all 8-bit/4-bit quantization imports and verify no CUDA imports.

This script scans all Python files in the project to ensure:
1. No imports from bitsandbytes, transformers.utils.quantization, or similar quantization libraries.
2. No explicit CUDA device initialization (torch.cuda, CUDA_VISIBLE_DEVICES).

It produces a report at:
projects/PROJ-586-social-memory-networks-modeling-collecti/results/quantization_audit.md

The script exits with code 0 if the project is clean, or 1 if violations are found.
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional

# Patterns to detect prohibited imports
QUANTIZATION_PATTERNS = [
    r"import\s+bitsandbytes",
    r"from\s+bitsandbytes",
    r"import\s+transformers.*quantization",
    r"from\s+transformers.*quantization",
    r"import\s+optimum",
    r"from\s+optimum",
    r"import\s+accelerate.*quantization",
    r"from\s+accelerate.*quantization",
    r"load_in_8bit",
    r"load_in_4bit",
    r"bnb_4bit",
    r"bnb_8bit",
    r"bitsandbytes\.Autograd4Bit",
]

# Patterns to detect CUDA usage (excluding comments)
CUDA_PATTERNS = [
    r"torch\.cuda",
    r"CUDA_VISIBLE_DEVICES",
    r"\.cuda\(\)",
    r"device\s*=\s*['\"]cuda",
    r"is_available\(\)", # Often used with cuda check, but context matters. We flag if paired with torch.
]

# Specific lines to ignore (e.g., if they are in comments or docstrings, though regex is line-based)
# We will rely on the regex matching the line content.

def is_prohibited_line(line: str) -> Tuple[bool, Optional[str]]:
    """Check if a line contains prohibited quantization or CUDA patterns."""
    # Skip comments
    stripped = line.strip()
    if stripped.startswith("#"):
        return False, None

    for pattern in QUANTIZATION_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True, "QUANTIZATION"

    for pattern in CUDA_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Exclude common false positives like 'cuda' in a string literal for a path
            if "cuda" in line.lower() and "device" not in line.lower():
                # If it's just the word cuda in a string not related to device, maybe skip?
                # But strictness is better for T032.
                pass
            return True, "CUDA"

    return False, None

def process_file(file_path: pathlib.Path) -> List[Tuple[int, str, str]]:
    """Scan a single file for prohibited patterns."""
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            is_bad, category = is_prohibited_line(line)
            if is_bad:
                violations.append((i, category, line.strip()))
    except Exception as e:
        # Skip files that can't be read (e.g., binary)
        pass
    return violations

def scan_project(root_path: pathlib.Path) -> Dict[pathlib.Path, List[Tuple[int, str, str]]]:
    """Scan all Python files in the project root."""
    results = {}
    py_files = list(root_path.rglob("*.py"))
    
    for py_file in py_files:
        # Skip __pycache__, .git, virtualenvs
        if any(part.startswith("__") or part.startswith(".") for part in py_file.parts):
            continue
        if "venv" in py_file.parts or "node_modules" in py_file.parts:
            continue

        violations = process_file(py_file)
        if violations:
            results[py_file] = violations

    return results

def generate_markdown_report(
    violations: Dict[pathlib.Path, List[Tuple[int, str, str]]],
    timestamp: datetime
) -> str:
    """Generate a Markdown report of the audit."""
    lines = [
        "# Quantization and CUDA Import Audit Report",
        f"**Generated**: {timestamp.isoformat()}",
        f"**Status**: {'FAILED' if violations else 'PASSED'}",
        "",
    ]

    if not violations:
        lines.append("## Summary")
        lines.append("No prohibited quantization or CUDA imports detected in the project.")
        return "\n".join(lines)

    lines.append("## Violations Found")
    lines.append(f"Total files with violations: {len(violations)}")
    lines.append("")

    for file_path, file_violations in sorted(violations.items()):
        lines.append(f"### `{file_path}`")
        for line_no, category, line_content in file_violations:
            lines.append(f"- **Line {line_no}** ({category}): `{line_content}`")
        lines.append("")

    lines.append("## Action Required")
    lines.append("Remove or replace the identified imports with CPU-compatible alternatives.")
    
    return "\n".join(lines)

def main() -> int:
    """Main entry point."""
    # Determine project root based on script location
    script_path = pathlib.Path(__file__).resolve()
    # Assuming the script is in code/, project root is parent of code/
    project_root = script_path.parent.parent

    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow()
    violations = scan_project(project_root)

    report_content = generate_markdown_report(violations, timestamp)
    report_path = results_dir / "quantization_audit.md"
    report_path.write_text(report_content, encoding="utf-8")

    print(f"Audit complete. Report saved to: {report_path}")

    if violations:
        print("❌ VIOLATIONS FOUND. Please review the report.")
        return 1
    else:
        print("✅ No violations found. Project is compliant.")
        return 0

if __name__ == "__main__":
    sys.exit(main())