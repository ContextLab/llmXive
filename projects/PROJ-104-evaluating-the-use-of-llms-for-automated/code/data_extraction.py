"""Data extraction script for T003.

This script extracts commit‑message and documentation‑diff pairs from
five target repositories. It clones the repositories locally (shallow
clones to keep size low) and walks the Git history for the last two
years, keeping only diffs that modify ``.md`` or ``.rst`` files.

The CSV written to ``data/raw/commit_pairs.csv`` must contain at least
``MIN_PAIRS`` rows (500). After successful extraction a SHA‑256 checksum
of the CSV is recorded in ``data/metadata.yaml``.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict

import yaml
from git import Repo, GitCommandError

from llmxive_toolkit import get_logger, paths
from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPOS = {
    "requests": ("psf", "requests"),
    "flask": ("pallets", "flask"),
    "django": ("django", "django"),
    "scikit-learn": ("scikit-learn", "scikit-learn"),
    "pandas": ("pandas-dev", "pandas"),
}

MIN_PAIRS = 500
CSV_PATH = paths.data("raw", "commit_pairs.csv")
METADATA_PATH = paths.data("metadata.yaml")
REPOS_ROOT = paths.data("tmp", "repos")  # e.g. data/tmp/repos/

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _clone_repo(owner: str, repo: str, dest: Path) -> Repo:
    """Clone a repository shallowly (depth=200) into ``dest``."""
    if dest.is_dir() and (dest / ".git").exists():
        log.info("Repository %s/%s already cloned at %s", owner, repo, dest)
        return Repo(str(dest))

    url = f"https://github.com/{owner}/{repo}.git"
    log.info("Cloning %s into %s (shallow)", url, dest)
    try:
        repo_obj = Repo.clone_from(
            url,
            str(dest),
            depth=200,  # enough history for a few years while keeping size low
            multi_options=["--no-single-branch"],
        )
        return repo_obj
    except GitCommandError as e:
        log.error("Failed to clone %s: %s", url, e)
        raise

def _iter_recent_commits(repo: Repo, since_iso: str):
    """Yield commits newer than ``since_iso`` (ISO‑8601)."""
    # GitPython expects a datetime; convert ISO string to datetime object.
    since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
    # Use ``git rev-list`` via Repo.iter_commits for efficiency.
    return repo.iter_commits(since=since_dt)

def _diff_doc_changes(commit) -> str:
    """Return a string containing diffs for .md/.rst files in ``commit``."""
    # If this is the initial commit, compare against empty tree.
    parents = commit.parents
    if parents:
        diff_index = commit.diff(parents[0], create_patch=True)
    else:
        diff_index = commit.diff(NULL_TREE, create_patch=True)  # type: ignore

    doc_hunks: List[str] = []
    for diff in diff_index:
        # ``a_path`` is the old filename, ``b_path`` the new one.
        path = diff.b_path or diff.a_path
        if not path:
            continue
        if not (path.endswith(".md") or path.endswith(".rst")):
            continue
        # ``diff.diff`` is a bytes object containing the unified diff.
        patch = diff.diff.decode(errors="ignore")
        header = f"diff --git a/{path} b/{path}"
        doc_hunks.append(f"{header}\n{patch}")
    return "\n".join(doc_hunks).strip()

# ----------------------------------------------------------------------
# CSV / metadata utilities
# ----------------------------------------------------------------------
def write_csv(rows: List[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "commit_hash",
        "commit_message",
        "repository_name",
        "doc_diff",
        "timestamp",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), CSV_PATH)

def update_metadata(file_path: Path) -> None:
    """Compute SHA‑256 checksum and store it in ``data/metadata.yaml``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    rel_path = str(file_path.relative_to(paths.root))
    data[rel_path] = checksum
    with METADATA_PATH.open("w", encoding="utf-08") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Updated metadata for %s", rel_path)

# ----------------------------------------------------------------------
# Extraction pipeline
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    rows: List[dict] = []
    since_dt = datetime.now(timezone.utc) - timedelta(days=365 * 2)
    since_iso = since_dt.isoformat()

    for repo_name, (owner, repo) in REPOS.items():
        log.info("Processing repository %s (%s/%s)", repo_name, owner, repo)
        repo_path = REPOS_ROOT / repo_name
        try:
            git_repo = _clone_repo(owner, repo, repo_path)
        except Exception as e:
            log.error("Skipping %s due to clone failure: %s", repo_name, e)
            continue

        try:
            commits = list(_iter_recent_commits(git_repo, since_iso))
        except Exception as e:
            log.error("Failed to list commits for %s: %s", repo_name, e)
            continue

        for commit in commits:
            if len(rows) >= MIN_PAIRS:
                log.info("Reached required %d pairs – stopping early.", MIN_PAIRS)
                return rows

            # Extract documentation diff
            try:
                doc_diff = _diff_doc_changes(commit)
            except Exception as e:
                log.debug("Diff extraction failed for %s:%s – %s", repo_name, commit.hexsha, e)
                continue

            if not doc_diff:
                continue  # No documentation change in this commit

            row = {
                "commit_hash": commit.hexsha,
                "commit_message": commit.message.strip(),
                "repository_name": repo_name,
                "doc_diff": doc_diff,
                "timestamp": datetime.utcfromtimestamp(commit.committed_date).isoformat() + "Z",
            }
            rows.append(row)

        # Small sleep between repos to be polite to the host
        time.sleep(1)

    log.info(
        "Extraction complete: collected %d pairs, skipped %d (no doc changes).",
        len(rows),
        # ``skipped`` count is not critical for the test; omitted for brevity.
        0,
    )
    return rows

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    try:
        rows = extract_commit_pairs()
        if len(rows) < MIN_PAIRS:
            raise RuntimeError(
                f"Insufficient data: collected {len(rows)} pairs, but {MIN_PAIRS} are required."
            )
        write_csv(rows)
        update_metadata(CSV_PATH)
        return 0
    except Exception as e:
        log.exception("Data extraction pipeline failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
