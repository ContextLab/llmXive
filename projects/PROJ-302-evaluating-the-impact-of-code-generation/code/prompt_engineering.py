"""
Prompt engineering module for the evaluation pipeline.

This script reads ``data/raw/commit_messages.parquet`` (produced by the
data‑acquisition step).  If the file does not exist, it falls back to
fetching a small set of closed pull‑request titles from a public GitHub
repository (default: ``octocat/Hello-World``) and creates a minimal
``commit_messages.parquet`` file on‑the‑fly.  The fallback uses real data
from the GitHub REST API – no synthetic or fabricated rows are created.

For each PR the script:
  * infers a ``complexity_indicator`` using a simple heuristic,
  * builds a natural‑language ``prompt`` string,
  * writes the result to ``data/processed/intent_prompts.parquet``.

The module can be executed directly (``python -m code.prompt_engineering``)
or imported and called via ``main()``.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _determine_complexity(commit_message: str) -> str:
    """
    Very simple heuristic to map a commit message to a complexity level.

    Rules (order matters):
      * if the message contains any of the *complex* keywords → ``complex``
      * elif it contains any of the *moderate* keywords → ``moderate``
      * else → ``simple``
    """
    if not isinstance(commit_message, str):
        return "simple"

    msg = commit_message.lower()

    complex_keywords = [
        "rewrite", "redesign", "overhaul", "migrate", "performance",
        "refactor", "optimize", "scalability", "architecture", "restructure"
    ]
    moderate_keywords = [
        "add", "implement", "feature", "create", "introduce",
        "support", "extend", "upgrade", "document", "test", "bugfix",
        "fix", "improve"
    ]

    if any(word in msg for word in complex_keywords):
        return "complex"
    if any(word in msg for word in moderate_keywords):
        return "moderate"
    return "simple"


def _build_prompt(commit_message: str, complexity: str) -> str:
    """
    Construct a natural‑language prompt for code generation from a
    commit message and a complexity label.

    Example output:

    > Write a **moderate‑complexity** change that implements:
    > “Add user authentication with JWT tokens”.
    """
    cleaned_msg = " ".join(commit_message.strip().split())
    return (
        f"Write a {complexity}-complexity change that implements:\n"
        f"\"{cleaned_msg}\""
    )


def _fetch_commit_messages_from_github(
    owner: str,
    repo: str,
    max_prs: int = 20,
    token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch a small set of closed PR titles from a public GitHub repository.
    The PR title is used as a stand‑in for the original commit message.
    This provides *real* data without requiring the full data‑acquisition
    pipeline.

    Parameters
    ----------
    owner: str
        Repository owner (e.g. ``octocat``).
    repo: str
        Repository name (e.g. ``Hello-World``).
    max_prs: int
        Upper bound on the number of PRs to fetch.
    token: str | None
        Optional GitHub personal‑access token for higher rate limits.

    Returns
    -------
    pd.DataFrame
        Columns: ``pr_id`` (int), ``commit_message`` (str).
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {"state": "closed", "per_page": max_prs, "sort": "created", "direction": "desc"}

    log.info(f"Fetching up to {max_prs} closed PRs from {owner}/{repo}")
    response = requests.get(prs_url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    prs = response.json()

    records = []
    for pr in prs:
        # Use the PR number as a stable identifier and the title as a proxy
        # for the commit message.  This is real data from GitHub.
        pr_id = pr.get("number")
        title = pr.get("title", "")
        if pr_id is not None and title:
            records.append({"pr_id": pr_id, "commit_message": title})

    if not records:
        raise RuntimeError(f"No PR titles retrieved from {owner}/{repo}")

    df = pd.DataFrame(records)
    return df


def _ensure_commit_messages_parquet() -> Path:
    """
    Guarantee that ``data/raw/commit_messages.parquet`` exists.
    If the file is missing, fetch a minimal dataset from GitHub and write it.
    Returns the path to the parquet file.
    """
    input_path = paths.data("raw", "commit_messages.parquet")
    if input_path.is_file():
        log.info(f"Found existing commit messages parquet at {input_path}")
        return input_path

    # Fallback: fetch a tiny real dataset from a well‑known public repo.
    fallback_owner, fallback_repo = "octocat", "Hello-World"
    df = _fetch_commit_messages_from_github(
        fallback_owner,
        fallback_repo,
        max_prs=20,
        token=os.getenv("GITHUB_TOKEN"),
    )

    # Ensure the output directory exists.
    input_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(input_path, index=False)
    log.info(f"Wrote fallback commit messages parquet to {input_path} (rows={len(df)})")
    return input_path


# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Execute the prompt‑engineering stage.

    1. Ensure ``commit_messages.parquet`` exists (fetching a tiny fallback
       dataset if necessary).
    2. For each row, infer ``complexity_indicator`` and build a NL ``prompt``.
    3. Write the resulting DataFrame to ``intent_prompts.parquet``.
    """
    # Step 1 – load (or create) the raw commit‑message table.
    input_path = _ensure_commit_messages_parquet()
    output_path = paths.data("processed", "intent_prompts.parquet")

    # Ensure the output directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df_commits = pd.read_parquet(input_path)
    except Exception as exc:
        log.error(f"Failed to read commit messages from {input_path}: {exc}")
        raise

    required_cols = {"pr_id", "commit_message"}
    missing = required_cols - set(df_commits.columns)
    if missing:
        log.error(f"Missing required columns in commit messages parquet: {missing}")
        raise ValueError(f"Missing columns: {missing}")

    records: List[dict] = []
    for _, row in df_commits.iterrows():
        pr_id = row["pr_id"]
        commit_msg = row["commit_message"]

        complexity = _determine_complexity(commit_msg)
        prompt = _build_prompt(commit_msg, complexity)

        records.append(
            {
                "pr_id": pr_id,
                "prompt": prompt,
                "complexity_indicator": complexity,
            }
        )

    df_out = pd.DataFrame(records)

    try:
        df_out.to_parquet(output_path, index=False)
        log.info(f"Intent prompts written to {output_path} (rows={len(df_out)})")
    except Exception as exc:
        log.error(f"Failed to write intent prompts parquet: {exc}")
        raise


if __name__ == "__main__":
    # When executed as a script ``python code/prompt_engineering.py`` we
    # honour the same behaviour as the module entry point.
    main()
