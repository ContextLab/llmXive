"""
Code Block Extraction with Rename Tracking
-------------------------------------------------
This script walks all cloned repositories under ``data/raw/clones``,
extracts top‑level function and class definitions from Python files
(using ``ast``) and JavaScript files (placeholder implementation),
records the introduction commit via ``git log --follow``, computes a
SHA‑256 hash of the block content, and writes the results to
``data/raw/code_blocks.csv``.

It also detects rename events that change the directory depth or the
immediate parent directory name and excludes such blocks, logging the
exclusions to ``data/logs/refactor_exclusions.log`` and a summary JSON
to ``data/logs/refactor_validation_report.json``.
"""

import csv
import hashlib
import json
import os
import subprocess
import uuid
import ast
from pathlib import Path
from typing import List, Dict, Tuple

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _sha256(text: str) -> str:
    """Return the SHA‑256 hex digest of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_code_blocks_py(file_path: Path) -> List[Dict]:
    """
    Extract top‑level function and class definitions from a Python file.

    Returns a list of dicts with keys:
        - start_line: 1‑based start line number
        - end_line:   1‑based end line number
        - content:    source code of the block
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Failed to read {file_path}: {e}")
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        log.warning(f"Skipping unparsable Python file {file_path}: {e}")
        return []

    blocks = []
    lines = source.splitlines()

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # ast nodes have lineno (1‑based) and, from Python 3.8+, end_lineno
            start = node.lineno
            end = getattr(node, "end_lineno", None)
            if end is None:
                # Fallback: approximate by scanning forward until next top‑level node
                # or end of file.
                end = start
                for subsequent in ast.iter_child_nodes(tree):
                    if getattr(subsequent, "lineno", 0) > start:
                        end = subsequent.lineno - 1
                        break
                else:
                    end = len(lines)
            block_source = "\n".join(lines[start - 1 : end])
            blocks.append(
                {
                    "start_line": start,
                    "end_line": end,
                    "content": block_source,
                }
            )
    return blocks


def extract_code_blocks_js(file_path: Path) -> List[Dict]:
    """
    Placeholder JavaScript block extractor.

    For the purposes of T003 we treat the entire file as a single block.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Failed to read {file_path}: {e}")
        return []

    lines = source.splitlines()
    if not lines:
        return []
    return [
        {
            "start_line": 1,
            "end_line": len(lines),
            "content": source,
        }
    ]


def _git_introduction_commit(repo_path: Path, rel_file: Path) -> Tuple[str, str]:
    """
    Return the earliest commit hash and its ISO‑8601 timestamp that introduced *rel_file*.

    Uses ``git log --follow --diff-filter=A`` to find the addition commit.
    If no such commit is found, returns empty strings.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--diff-filter=A",
                "--format=%H %cI",
                "--",
                str(rel_file),
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log.error(f"Git log failed for {rel_file} in {repo_path}: {e}")
        return "", ""

    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    if not lines:
        return "", ""

    # The earliest commit is the last line of the output
    commit_hash, commit_ts = lines[-1].split(maxsplit=1)
    return commit_hash, commit_ts


def generate_code_blocks(
    clones_root: Path,
    output_csv: Path,
    exclusions_log: Path,
    validation_json: Path,
) -> None:
    """
    Walk all cloned repositories under ``clones_root`` and write a CSV with one
    row per extracted block. Blocks whose files have been renamed in a way that
    changes directory depth or the immediate parent directory are excluded.

    The CSV columns are:
        block_id, file_path, start_line, end_line, language,
        content_hash, introduction_commit, introduction_timestamp
    """
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    exclusions_log.parent.mkdir(parents=True, exist_ok=True)

    total_blocks = 0
    excluded_blocks = 0
    exclusion_records = []

    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "block_id",
                "file_path",
                "start_line",
                "end_line",
                "language",
                "content_hash",
                "introduction_commit",
                "introduction_timestamp",
            ]
        )

        # Iterate over each repository directory
        for repo_dir in clones_root.iterdir():
            if not repo_dir.is_dir():
                continue

            # Walk the repository file tree
            for file_path in repo_dir.rglob("*"):
                if file_path.is_dir():
                    continue
                if file_path.suffix not in {".py", ".js"}:
                    continue

                rel_path = file_path.relative_to(repo_dir)
                language = "python" if file_path.suffix == ".py" else "javascript"

                # Extract blocks
                if language == "python":
                    blocks = extract_code_blocks_py(file_path)
                else:
                    blocks = extract_code_blocks_js(file_path)

                if not blocks:
                    continue

                # Determine rename history for the file
                from utils.git_mv_detector import get_git_rename_history, should_exclude_due_to_rename

                rename_history = get_git_rename_history(repo_dir, rel_path)
                exclude_file = False
                exclude_reason = ""
                for old_path, new_path in rename_history:
                    if should_exclude_due_to_rename(old_path, new_path):
                        exclude_file = True
                        exclude_reason = (
                            f"Path depth or parent changed: {old_path} -> {new_path}"
                        )
                        break

                # Process each block
                for blk in blocks:
                    total_blocks += 1
                    block_id = str(uuid.uuid4())
                    content = blk["content"]
                    content_hash = _sha256(content)

                    # Find introduction commit for the *file* (not per block)
                    intro_commit, intro_ts = _git_introduction_commit(repo_dir, rel_path)

                    if exclude_file:
                        excluded_blocks += 1
                        exclusion_records.append(
                            {
                                "block_id": block_id,
                                "old_path": old_path,
                                "new_path": new_path,
                                "reason": exclude_reason,
                            }
                        )
                        continue

                    writer.writerow(
                        [
                            block_id,
                            str(rel_path).replace(os.sep, "/"),
                            blk["start_line"],
                            blk["end_line"],
                            language,
                            content_hash,
                            intro_commit,
                            intro_ts,
                        ]
                    )

    # Write exclusions log
    with exclusions_log.open("w", newline="", encoding="utf-8") as excl_file:
        excl_writer = csv.writer(excl_file)
        excl_writer.writerow(["block_id", "old_path", "new_path", "reason"])
        for rec in exclusion_records:
            excl_writer.writerow(
                [rec["block_id"], rec["old_path"], rec["new_path"], rec["reason"]]
            )

    # Write validation JSON summary
    validation = {
        "total_blocks_processed": total_blocks,
        "blocks_excluded": excluded_blocks,
        "blocks_written": total_blocks - excluded_blocks,
    }
    with validation_json.open("w", encoding="utf-8") as json_file:
        json.dump(validation, json_file, indent=2)


def main() -> None:
    """
    Entry point used by the quick‑start pipeline.
    """
    clones_root = paths.data("raw", "clones")
    output_csv = paths.data("raw", "code_blocks.csv")
    exclusions_log = paths.data("logs", "refactor_exclusions.log")
    validation_json = paths.data("logs", "refactor_validation_report.json")

    log.info(f"Starting code block extraction over clones in {clones_root}")
    generate_code_blocks(clones_root, output_csv, exclusions_log, validation_json)
    log.info(f"Extraction completed. CSV written to {output_csv}")


if __name__ == "__main__":
    main()
