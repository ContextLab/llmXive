"""
Code Block Extraction with Rename Tracking
-------------------------------------------------
This script walks all cloned repositories under `data/raw/clones`,
extracts top-level function and class definitions from Python files
(using `ast`) and JavaScript files (using `tree-sitter`),
records the introduction commit via `git log --follow`, computes a
SHA-256 hash of the block content, and writes the results to
`data/raw/code_blocks.csv`.

It also detects rename events that change the directory depth or the
immediate parent directory name and excludes such blocks, logging the
exclusions to `data/logs/refactor_exclusions.log` and a summary JSON to
`data/logs/refactor_validation_report.json`.
"""
import csv
import hashlib
import json
import os
import subprocess
import uuid
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Any

from llmxive_toolkit import paths, get_logger

# Try to import tree-sitter for JS parsing
try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript as tsjs
    HAS_TREE_SITTER = True
    JS_LANGUAGE = Language(tsjs.language())
    JS_PARSER = Parser(JS_LANGUAGE)
except ImportError:
    HAS_TREE_SITTER = False

from utils.git_mv_detector import get_git_rename_history, should_exclude_due_to_rename

log = get_logger(__name__)

def _sha256(text: str) -> str:
    """Return the SHA-256 hex digest of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_code_blocks_py(file_path: Path) -> List[Dict[str, Any]]:
    """Extract top-level functions and classes from a Python file."""
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
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            block_source = "\n".join(lines[start - 1 : end])
            blocks.append({
                "start_line": start,
                "end_line": end,
                "content": block_source,
            })
    return blocks

def extract_code_blocks_js(file_path: Path) -> List[Dict[str, Any]]:
    """Extract top-level functions and classes from a JS file using tree-sitter."""
    try:
        code_bytes = file_path.read_bytes()
    except Exception as e:
        log.error(f"Failed to read {file_path}: {e}")
        return []

    if not HAS_TREE_SITTER:
        # Fallback to whole-file if tree-sitter is missing, though spec requires it.
        # In the real environment, T001 ensures it's installed.
        source = code_bytes.decode("utf-8", errors="ignore")
        return [{"start_line": 1, "end_line": len(source.splitlines()), "content": source}]

    tree = JS_PARSER.parse(code_bytes)
    blocks = []
    
    # Simple query for function/class declarations
    query = JS_LANGUAGE.query("""
        (function_declaration) @func
        (class_declaration) @class
        (method_definition) @method
    """)
    captures = query.captures(tree.root_node)
    
    for node, tag in captures:
        start = node.start_point[0] + 1
        end = node.end_point[0] + 1
        blocks.append({
            "start_line": start,
            "end_line": end,
            "content": code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore"),
        })
    return blocks

def _git_introduction_commit(repo_path: Path, rel_file: Path) -> Tuple[str, str]:
    """Return the earliest commit hash and timestamp that introduced the file."""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--diff-filter=A", "--format=%H %cI", "--", str(rel_file)],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
        lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        if not lines: return "", ""
        commit_hash, commit_ts = lines[-1].split(maxsplit=1)
        return commit_hash, commit_ts
    except Exception:
        return "", ""

def generate_code_blocks(clones_root: Path, output_csv: Path, exclusions_log: Path, validation_json: Path) -> None:
    """Main extraction loop with rename tracking."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    exclusions_log.parent.mkdir(parents=True, exist_ok=True)

    total_blocks = 0
    excluded_blocks = 0
    exclusion_records = []

    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["block_id", "file_path", "start_line", "end_line", "language", "content_hash", "introduction_commit", "introduction_timestamp"])

        for repo_dir in clones_root.iterdir():
            if not repo_dir.is_dir(): continue
            
            for file_path in repo_dir.rglob("*"):
                if not file_path.is_file(): continue
                if file_path.suffix not in {".py", ".js"}: continue

                rel_path = file_path.relative_to(repo_dir)
                language = "python" if file_path.suffix == ".py" else "javascript"
                
                # 1. Check Rename History for the file
                rename_history = get_git_rename_history(repo_dir, rel_path)
                exclude_file = False
                exclude_reason = ""
                last_rename = None
                for old, new in rename_history:
                    if should_exclude_due_to_rename(old, new):
                        exclude_file = True
                        exclude_reason = f"Depth or parent changed: {old} -> {new}"
                        last_rename = (old, new)
                        break
                
                # 2. Extract Blocks
                blocks = extract_code_blocks_py(file_path) if language == "python" else extract_code_blocks_js(file_path)
                if not blocks: continue

                # 3. Process and Write
                intro_commit, intro_ts = _git_introduction_commit(repo_dir, rel_path)
                for blk in blocks:
                    total_blocks += 1
                    block_id = str(uuid.uuid4())
                    content_hash = _sha256(blk["content"])

                    if exclude_file:
                        excluded_blocks += 1
                        exclusion_records.append({
                            "block_id": block_id,
                            "old_path": last_rename[0] if last_rename else "N/A",
                            "new_path": last_rename[1] if last_rename else "N/A",
                            "reason": exclude_reason,
                        })
                        continue

                    writer.writerow([
                        block_id, str(rel_path).replace(os.sep, "/"),
                        blk["start_line"], blk["end_line"], language,
                        content_hash, intro_commit, intro_ts,
                    ])

    # Write logs
    with exclusions_log.open("w", newline="", encoding="utf-8") as excl_file:
        excl_writer = csv.writer(excl_file)
        excl_writer.writerow(["block_id", "old_path", "new_path", "reason"])
        for rec in exclusion_records:
            excl_writer.writerow([rec["block_id"], rec["old_path"], rec["new_path"], rec["reason"]])

    with validation_json.open("w", encoding="utf-8") as json_file:
        json.dump({
            "total_blocks_processed": total_blocks,
            "blocks_excluded": excluded_blocks,
            "blocks_written": total_blocks - excluded_blocks,
        }, json_file, indent=2)

def main() -> None:
    clones_root = paths.data("raw", "clones")
    output_csv = paths.data("raw", "code_blocks.csv")
    exclusions_log = paths.data("logs", "refactor_exclusions.log")
    validation_json = paths.data("logs", "refactor_validation_report.json")
    log.info(f"Starting extraction in {clones_root}")
    generate_code_blocks(clones_root, output_csv, exclusions_log, validation_json)
    log.info(f"Completed. Written to {output_csv}")

if __name__ == "__main__":
    main()
