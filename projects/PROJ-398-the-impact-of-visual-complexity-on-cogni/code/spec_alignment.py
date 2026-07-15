"""
spec_alignment.py

Implements the spec‑task alignment review required for task **T000**.
The script compares the list of task identifiers present in ``tasks.md``
with those mentioned in ``spec.md`` and produces a markdown report at
``docs/spec_alignment_report.md`` detailing any mismatches.

Public API (as declared in the project’s API surface):
  - load_file_content
  - check_path_existence
  - analyze_spec_tasks_alignment
  - generate_report
  - main
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_file_content(file_path: Path) -> str:
    """
    Load the full text content of ``file_path`` and return it as a string.

    Parameters
    ----------
    file_path: Path
        Path to the file to be read.

    Returns
    -------
    str
        File contents. If the file does not exist, an empty string is
        returned.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def check_path_existence(paths: List[Path]) -> Dict[Path, bool]:
    """
    Return a dictionary mapping each supplied ``Path`` to a boolean indicating
    whether the path exists on disk.

    Parameters
    ----------
    paths: List[Path]

    Returns
    -------
    Dict[Path, bool]
    """
    return {p: p.exists() for p in paths}

# ----------------------------------------------------------------------
# Core analysis
# ----------------------------------------------------------------------
_TASK_ID_PATTERN = re.compile(r"\[([A-Z]\d{3})\]")

def _extract_task_ids(text: str) -> List[str]:
    """
    Extract all task identifiers of the form ``[Txxx]`` from the supplied text.
    """
    return list({match.group(1) for match in _TASK_ID_PATTERN.finditer(text)})

def analyze_spec_tasks_alignment(
    spec_content: str, tasks_content: str
) -> Tuple[List[str], List[str]]:
    """
    Compare task identifiers found in ``spec_content`` with those found in
    ``tasks_content``.

    Returns
    -------
    missing_in_spec: List[str]
        Task IDs that appear in ``tasks.md`` but not in ``spec.md``.
    extra_in_spec: List[str]
        Task IDs that appear in ``spec.md`` but not in ``tasks.md``.
    """
    spec_ids = set(_extract_task_ids(spec_content))
    tasks_ids = set(_extract_task_ids(tasks_content))

    missing_in_spec = sorted(tasks_ids - spec_ids)
    extra_in_spec = sorted(spec_ids - tasks_ids)

    return missing_in_spec, extra_in_spec

# ----------------------------------------------------------------------
# Report generation
# ----------------------------------------------------------------------
def generate_report(
    missing_in_spec: List[str], extra_in_spec: List[str], spec_path: Path, tasks_path: Path
) -> str:
    """
    Produce a markdown report summarising the alignment check.

    Parameters
    ----------
    missing_in_spec: List[str]
        IDs present in ``tasks.md`` but absent from ``spec.md``.
    extra_in_spec: List[str]
        IDs present in ``spec.md`` but absent from ``tasks.md``.
    spec_path: Path
    tasks_path: Path

    Returns
    -------
    str
        Markdown formatted report.
    """
    lines = [
        "# Spec‑Task Alignment Report",
        "",
        f"**Spec file:** `{spec_path}`",
        f"**Tasks file:** `{tasks_path}`",
        "",
        "## Summary",
        "",
    ]

    if not missing_in_spec and not extra_in_spec:
        lines.append("✅ No contradictions detected – the task list in `tasks.md` aligns with the identifiers referenced in `spec.md`.")
    else:
        if missing_in_spec:
            lines.append("### Tasks missing from spec.md")
            lines.append("")
            for tid in missing_in_spec:
                lines.append(f"- `{tid}`")
            lines.append("")
        if extra_in_spec:
            lines.append("### Task identifiers present in spec.md but not in tasks.md")
            lines.append("")
            for tid in extra_in_spec:
                lines.append(f"- `{tid}`")
            lines.append("")

    lines.append("---")
    lines.append("_Report generated automatically by `code/spec_alignment.py`._")
    return "\n".join(lines)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the alignment check and write the markdown report to
    ``docs/spec_alignment_report.md``.
    """
    project_root = Path(__file__).resolve().parent.parent  # repository root
    spec_path = project_root / "spec.md"
    tasks_path = project_root / "tasks.md"
    report_path = project_root / "docs" / "spec_alignment_report.md"

    # Ensure the ``docs`` directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Load files
    spec_content = load_file_content(spec_path)
    tasks_content = load_file_content(tasks_path)

    # Analyse
    missing_in_spec, extra_in_spec = analyze_spec_tasks_alignment(
        spec_content, tasks_content
    )

    # Generate report
    report_md = generate_report(missing_in_spec, extra_in_spec, spec_path, tasks_path)

    # Write the report
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Spec‑task alignment report written to: {report_path}")

if __name__ == "__main__":
    main()
