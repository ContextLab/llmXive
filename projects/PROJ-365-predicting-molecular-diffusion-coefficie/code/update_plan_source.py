"""
Update `plan.md` with the dataset source information.

This script reads the `data/data_source_flag.json` artifact produced by the
ingestion pipeline to determine whether the dataset is real or synthetic.
It then writes a line to the repository's ``plan.md`` file indicating the
source status. If the source is real, the script attempts to locate a
``data/source_url.txt`` file (created by the download step) to record the
actual URL; otherwise it records that the dataset is a simulation study.

The script is idempotent – running it multiple times will update the same
line rather than appending duplicates.
"""

import json
from pathlib import Path
from typing import Optional

from utils.config import get_project_root


def _load_data_source_flag(project_root: Path) -> Optional[str]:
    """
    Load the ``data_source_flag.json`` file and return the ``source`` field.

    Parameters
    ----------
    project_root: Path
        The root directory of the repository.

    Returns
    -------
    Optional[str]
        ``'real'`` or ``'synthetic'`` if the file exists and contains the
        field, otherwise ``None``.
    """
    flag_path = project_root / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        return None
    try:
        with flag_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("source")
    except Exception:
        return None


def _load_source_url(project_root: Path) -> Optional[str]:
    """
    Attempt to read a plain‑text file containing the dataset URL.

    The ingestion step that downloads a real dataset can optionally write
    the URL to ``data/source_url.txt``.  If the file is missing, ``None`` is
    returned.

    Parameters
    ----------
    project_root: Path

    Returns
    -------
    Optional[str]
    """
    url_path = project_root / "data" / "source_url.txt"
    if not url_path.is_file():
        return None
    try:
        with url_path.open("r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def _update_plan_md(project_root: Path, line: str) -> None:
    """
    Insert or replace a line that starts with ``Dataset source:`` in ``plan.md``.

    If the line already exists, it is replaced with the new content.
    Otherwise the line is appended to the end of the file.

    Parameters
    ----------
    project_root: Path
        Repository root.
    line: str
        The full line to write (including the trailing newline).
    """
    plan_path = project_root / "plan.md"
    if not plan_path.is_file():
        # Create a minimal plan file if it does not exist.
        plan_path.write_text(line + "\n", encoding="utf-8")
        return

    with plan_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    prefix = "Dataset source:"
    updated = False
    new_lines = []
    for existing in lines:
        if existing.lstrip().startswith(prefix):
            new_lines.append(line + "\n")
            updated = True
        else:
            new_lines.append(existing.rstrip("\n"))
    if not updated:
        # Ensure there is a blank line before appending for readability.
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(line)

    plan_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> None:
    """
    Entry point for the script.

    Detects the dataset source and writes a descriptive line to ``plan.md``.
    """
    project_root = get_project_root()
    source = _load_data_source_flag(project_root)

    if source == "real":
        url = _load_source_url(project_root)
        if url:
            status_line = f"Dataset source: real – {url}"
        else:
            status_line = "Dataset source: real – URL not recorded"
    elif source == "synthetic":
        status_line = "Dataset source: Simulation Study"
    else:
        # Fallback when the flag is missing or malformed.
        status_line = "Dataset source: unknown (ingestion not yet executed)"

    _update_plan_md(project_root, status_line)


if __name__ == "__main__":
    main()
