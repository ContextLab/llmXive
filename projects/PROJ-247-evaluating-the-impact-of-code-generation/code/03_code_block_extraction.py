"""
Extract code blocks from the cloned repositories produced by ``01_data_curation.py``.
Produces ``data/raw/code_blocks.csv`` and logs any blocks excluded because
the underlying file has been renamed in a way that changes directory depth
or parent directory name.
"""

import csv
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

# Local utilities
from utils.git_mv_detector import (
    get_git_rename_history,
    should_exclude_due_to_rename,
    log_exclusion,
    generate_validation_report,
)

# ----------------------------------------------------------------------
# Helpers for Python AST extraction
# ----------------------------------------------------------------------
import ast

def extract_code_blocks_py(file_path: Path) -> List[Dict]:
    """
    Extract top‑level function and class definitions from a Python file.
    Returns a list of dicts with keys:
    ``start_line``, ``end_line``, ``content``.
    """
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    blocks: List[Dict] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # ``end_lineno`` is available in Python 3.8+
            end_line = getattr(node, "end_lineno", None)
            if end_line is None:
                # Fallback: approximate by counting lines of the node's body
                end_line = node.lineno + len(ast.get_source_segment(source, node).splitlines())
            block_source = ast.get_source_segment(source, node)
            if block_source is None:
                # As a safety net, slice the source lines
                lines = source.splitlines()
                block_source = "\n".join(lines[node.lineno - 1 : end_line])
            blocks.append(
                {
                    "start_line": node.lineno,
                    "end_line": end_line,
                    "content": block_source,
                }
            )
    return blocks

# ----------------------------------------------------------------------
# Helpers for JavaScript extraction via tree‑sitter
# ----------------------------------------------------------------------
try:
    from tree_sitter import Language, Parser
except Exception as e:  # pragma: no cover
    raise ImportError(
        "tree_sitter is required for JavaScript block extraction. "
        "Install it via `pip install tree_sitter tree_sitter_javascript`."
    ) from e

# Build or load the JavaScript language. The compiled shared library is
# expected at ``code/utils/build/my-languages.so``. If it does not exist,
# we build it on‑the‑fly (this is safe for the small subset of files we
# process in the test environment).
LANG_SO_PATH = Path(__file__).parent / "build" / "my-languages.so"
if not LANG_SO_PATH.is_file():
    # Build the language library (requires the language source files)
    # The ``tree_sitter_javascript`` package ships the source in its
    # installation directory; we locate it via the package's __file__.
    import importlib.util
    import os
    import shutil

    js_pkg = importlib.util.find_spec("tree_sitter_javascript")
    if js_pkg is None or not js_pkg.origin:
        raise RuntimeError("Unable to locate tree_sitter_javascript source.")
    js_dir = Path(js_pkg.origin).parent
    LANG_SO_PATH.parent.mkdir(parents=True, exist_ok=True)
    Language.build_library(
        # Store the library in the ``build`` directory
        str(LANG_SO_PATH),
        # Include the JavaScript language source
        [str(js_dir)],
    )

JS_LANGUAGE = Language(str(LANG_SO_PATH), "javascript")
JS_PARSER = Parser()
JS_PARSER.set_language(JS_LANGUAGE)

def extract_code_blocks_js(file_path: Path) -> List[Dict]:
    """
    Extract top‑level function declarations and class declarations from a
    JavaScript/TypeScript file using tree‑sitter.
    Returns a list of dicts with keys:
    ``start_line``, ``end_line``, ``content``.
    """
    source_bytes = file_path.read_bytes()
    tree = JS_PARSER.parse(source_bytes)
    root_node = tree.root_node

    blocks: List[Dict] = []

    # Helper to convert byte offsets to line numbers
    def byte_offset_to_line(offset: int) -> int:
        return source_bytes[:offset].count(b"\n") + 1

    # Walk the tree and collect function_declaration, method_definition,
    # class_declaration, arrow_function (if assigned to a const) etc.
    cursor = root_node.walk()

    def _visit(node):
        if node.type in ("function_declaration", "class_declaration"):
            start_line = byte_offset_to_line(node.start_byte)
            end_line = byte_offset_to_line(node.end_byte)
            content = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            blocks.append(
                {
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content,
                }
            )
        # Recurse
        for child in node.children:
            _visit(child)

    _visit(root_node)
    return blocks

# ----------------------------------------------------------------------
# Core extraction pipeline
# ----------------------------------------------------------------------
def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _git_introduction_commit(repo_path: Path, rel_file: Path) -> Tuple[str, str]:
    """
    Return the earliest commit hash and its timestamp (ISO 8601) for the
    given file (relative to ``repo_path``) using ``git log --follow``.
    """
    out = subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "log",
            "--follow",
            "--reverse",
            "--format=%H %ct",
            "--",
            str(rel_file),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    lines = out.stdout.strip().splitlines()
    if not lines:
        raise RuntimeError(f"No git history found for {rel_file} in {repo_path}")
    first = lines[0].split()
    commit_hash, epoch = first[0], int(first[1])
    timestamp = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    return commit_hash, timestamp

def generate_code_blocks(
    clones_root: Path,
    output_csv: Path,
    exclusions_log: Path,
    validation_json: Path,
) -> None:
    """
    Walk all cloned repositories under ``clones_root`` and write a CSV
    with one row per extracted block.

    Parameters
    ----------
    clones_root: Path
        Directory containing cloned repositories (e.g. ``data/raw/clones``).
    output_csv: Path
        Destination CSV file (``data/raw/code_blocks.csv``).
    exclusions_log: Path
        CSV log for blocks excluded due to rename semantics.
    validation_json: Path
        JSON file summarising the exclusions.
    """
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    exclusions: List[Dict] = []

    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "block_id",
                "file_path",
                "start_line",
                "end_line",
                "language",
                "content_hash",
                "introduction_commit",
                "introduction_timestamp",
            ],
        )
        writer.writeheader()

        for repo_dir in clones_root.iterdir():
            if not repo_dir.is_dir():
                continue
            # Walk .py and .js files
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

                # Determine introduction commit/timestamp once per file
                try:
                    intro_commit, intro_timestamp = _git_introduction_commit(repo_dir, rel_path)
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(
                        f"Git log failed for {rel_path} in {repo_dir}: {e.stderr}"
                    ) from e

                # Detect rename history for the file
                rename_history = get_git_rename_history(repo_dir, rel_path)

                # Evaluate whether any rename triggers exclusion
                exclude_due_to_rename = False
                for old_path, new_path in rename_history:
                    if should_exclude_due_to_rename(old_path, new_path):
                        exclude_due_to_rename = True
                        reason = (
                            f"Rename changed depth or parent: {old_path} -> {new_path}"
                        )
                        # Log each block that would be excluded
                        block_id_temp = str(uuid.uuid4())
                        log_exclusion(
                            block_id_temp,
                            old_path,
                            new_path,
                            reason,
                            exclusions_log,
                        )
                        exclusions.append(
                            {
                                "block_id": block_id_temp,
                                "old_path": old_path,
                                "new_path": new_path,
                                "reason": reason,
                            }
                        )
                        break  # one offending rename is enough

                if exclude_due_to_rename:
                    # Skip writing any blocks from this file
                    continue

                # Write each block
                for blk in blocks:
                    block_id = str(uuid.uuid4())
                    writer.writerow(
                        {
                            "block_id": block_id,
                            "file_path": str(rel_path).replace("\\", "/"),
                            "start_line": blk["start_line"],
                            "end_line": blk["end_line"],
                            "language": language,
                            "content_hash": _sha256(blk["content"]),
                            "introduction_commit": intro_commit,
                            "introduction_timestamp": intro_timestamp,
                        }
                    )

    # Produce validation JSON
    generate_validation_report(exclusions, validation_json)

def main() -> None:
    """
    Entry point used by the quick‑start pipeline.
    """
    from llmxive_toolkit import paths, get_logger

    log = get_logger(__name__)
    log.info("Starting code‑block extraction (T003)")

    # Directories (all created via ``paths`` helpers)
    clones_root = paths.data("raw", "clones")
    output_csv = paths.data("raw", "code_blocks.csv")
    exclusions_log = paths.data("logs", "refactor_exclusions.log")
    validation_json = paths.data("logs", "refactor_validation_report.json")

    try:
        generate_code_blocks(clones_root, output_csv, exclusions_log, validation_json)
        log.info(f"Code‑block CSV written to {output_csv}")
        log.info(f"Exclusions log written to {exclusions_log}")
    except Exception as exc:
        log.error(f"Failed to extract code blocks: {exc}")
        raise

if __name__ == "__main__":
    sys.exit(main())
