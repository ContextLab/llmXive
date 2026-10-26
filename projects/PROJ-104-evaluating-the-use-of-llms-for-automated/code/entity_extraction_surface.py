"""Surface‑entity extraction (Task T007).

This module extracts three types of surface entities from the human
documentation diffs stored in ``data/raw/commit_pairs.csv`` and from
the LLM‑generated documentation texts stored under
``data/generated/<model_id>/``. The three regex patterns required by
the specification are:

1. File paths      – ``[a-zA-Z0-9_./-]+\\.(py|md|rst)``
2. Function signatures – ``def [a-zA-Z_][a-zA-Z0-9_]*\\(``
3. Version numbers – ``\\d+\\.\\d+\\.\\d+``

For each extracted token we attempt to verify its existence in the
repository’s current codebase using ``git grep -w`` on a local clone
located under ``data/tmp/repos/<repository_name>``.  If the repository
has not been cloned yet the verification step is skipped and the
token is marked as ``verified: false`` – this is intentional: the
verification is a best‑effort check and must never cause the pipeline
to fail.

The output JSON for each sample has the following structure::

    {
        "sample_id": "<commit_hash>",
        "type": "surface",
        "source": "human" | "generated",
        "entities": [
            {"entity": "<token>", "verified": true|false},
            ...
        ]
    }

Files are written to ``data/intermediate/surface_entities/`` with the
naming convention ``{commit_hash}_{source}.json`` for the human
diff and ``{commit_hash}_{model_id}.json`` for each generated output.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict

import pandas as pd

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Regex patterns (compiled for performance)
# ----------------------------------------------------------------------
_PATTERNS: List[re.Pattern] = [
    re.compile(r"[a-zA-Z0-9_./-]+\.(py|md|rst)"),
    re.compile(r"def [a-zA-Z_][a-zA-Z0-9_]*\("),
    re.compile(r"\d+\.\d+\.\d+"),
]

# ----------------------------------------------------------------------
# Helper: run ``git grep -w <token>`` in the repository clone.
# Returns True if at least one match is found, False otherwise.
# ----------------------------------------------------------------------
def _verify_in_repo(repo_path: Path, token: str) -> bool:
    """Verify that *token* exists in the repository at *repo_path*.

    The function runs ``git grep -w`` and returns ``True`` if the command
    exits with status 0 (i.e. at least one match).  Any error (e.g. the
    repository does not exist or ``git`` is not available) results in
    ``False`` – the verification is best‑effort only.
    """
    if not repo_path.is_dir():
        log.debug("Repo path %s does not exist – skipping verification", repo_path)
        return False

    try:
        result = subprocess.run(
            ["git", "grep", "-w", token],
            cwd=repo_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        log.debug("Verification failed for token %s in %s: %s", token, repo_path, e)
        return False

# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def _extract_entities(text: str) -> List[str]:
    """Return a list of unique tokens matched by the three patterns."""
    matches = set()
    for pat in _PATTERNS:
        for m in pat.finditer(text):
            matches.add(m.group(0))
    return sorted(matches)

def _process_text(
    commit_hash: str,
    repo_name: str,
    text: str,
    source: str,
    repos_root: Path,
) -> Dict:
    """Create an EntitySet dict for a given text source."""
    entities = _extract_entities(text or "")
    repo_path = repos_root / repo_name
    verified_entities = [
        {"entity": ent, "verified": _verify_in_repo(repo_path, ent)}
        for ent in entities
    ]
    return {
        "sample_id": commit_hash,
        "type": "surface",
        "source": source,
        "entities": verified_entities,
    }

def run_extraction(
    csv_path: Path | None = None,
    output_dir: Path | None = None,
    repos_root: Path | None = None,
) -> int:
    """Run the surface‑entity extraction pipeline.

    Parameters
    ----------
    csv_path
        Path to ``data/raw/commit_pairs.csv``.  If ``None`` the default
        location is used.
    output_dir
        Directory where the per‑sample JSON files are written.  If
        ``None`` the default ``data/intermediate/surface_entities`` is used.
    repos_root
        Root directory containing cloned repositories (``data/tmp/repos``).
        If ``None`` the default is used.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    csv_path = csv_path or paths.data("raw", "commit_pairs.csv")
    output_dir = output_dir or paths.data("intermediate", "surface_entities")
    repos_root = repos_root or paths.data("tmp", "repos")

    if not csv_path.is_file():
        log.error("Commit‑pair CSV not found: %s", csv_path)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path, dtype=str)

    # Determine which model IDs have generated outputs.
    generated_root = paths.data("generated")
    model_ids = [
        p.name
        for p in generated_root.iterdir()
        if p.is_dir() and any(p.glob("*.txt"))
    ]

    for _, row in df.iterrows():
        commit_hash = row["commit_hash"]
        repo_name = row["repository_name"]
        doc_diff = row.get("doc_diff", "")

        # ---- Human diff ----
        human_entity_set = _process_text(
            commit_hash,
            repo_name,
            doc_diff,
            source="human",
            repos_root=repos_root,
        )
        human_out_path = output_dir / f"{commit_hash}_human.json"
        human_out_path.write_text(
            json.dumps(human_entity_set, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.debug("Wrote human surface entities for %s → %s", commit_hash, human_out_path)

        # ---- Generated docs for each model ----
        for model_id in model_ids:
            gen_txt_path = paths.data("generated", model_id, f"{commit_hash}_{model_id}.txt")
            if not gen_txt_path.is_file():
                # No generated file for this commit/model – skip.
                continue
            try:
                gen_text = gen_txt_path.read_text(encoding="utf-8")
            except Exception as e:
                log.debug("Failed to read generated file %s: %s", gen_txt_path, e)
                continue

            gen_entity_set = _process_text(
                commit_hash,
                repo_name,
                gen_text,
                source="generated",
                repos_root=repos_root,
            )
            gen_out_path = output_dir / f"{commit_hash}_{model_id}.json"
            gen_out_path.write_text(
                json.dumps(gen_entity_set, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            log.debug(
                "Wrote generated surface entities for %s (%s) → %s",
                commit_hash,
                model_id,
                gen_out_path,
            )

    log.info(
        "Surface‑entity extraction complete – %d commit hashes processed.", len(df)
    )
    return 0

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract surface entities from commit‑pair diffs and generated docs."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Path to commit‑pair CSV (default: data/raw/commit_pairs.csv)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory for JSON files (default: data/intermediate/surface_entities)",
    )
    parser.add_argument(
        "--repos",
        type=Path,
        help="Root of cloned repositories (default: data/tmp/repos)",
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    return run_extraction(csv_path=args.csv, output_dir=args.out, repos_root=args.repos)

if __name__ == "__main__":
    raise SystemExit(main())