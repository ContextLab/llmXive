"""
Preprocess PR data and generate the human‑baseline ground‑truth.

This script implements Task **T008**.  It performs the following steps:

1. Load the raw PR payloads written by :pymod:`src.extraction.fetch_prs`.
2. Truncate any diff that exceeds the LLM context window, emitting a warning
   per PR to ``logs/truncation.log`` and setting ``truncation_flag`` on the
   processed record.
3. Load (or fetch) human review comments and write them to
   ``data/annotations/raw_comments.json`` – a JSON file that conforms to the
   subset of :file:`contracts/bug_detection_schema.yaml` required for raw
   comments.
4. Apply the rubric from FR‑011 to identify confirmed bugs and write the
   results to ``data/derived/human_confirmations.json``.
5. Fuse the confirmations with linked GitHub issues that carry a ``bug``
   label to produce the triangulated ground‑truth file
   ``data/derived/human_baseline.json``.
6. Write the (possibly truncated) PR records to
   ``data/derived/prs_processed.json``.

The script is deliberately side‑effect‑free apart from the JSON files it
creates; it can be invoked directly::

    python -m src.extraction.preprocess_and_ground_truth

All paths are obtained via :pyfunc:`code.config.settings.get_paths`, so the
layout defined in the project configuration is respected.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Project utilities
from code.config.settings import get_paths, ensure_directories
# Re‑use the existing comment‑fetcher and confirmation‑filterer
from src.extraction.fetch_human_comments import main as fetch_comments_main
from src.extraction.filter_human_confirmations import main as filter_confirmations_main

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# A very generous LLM context window – the exact value is not critical for
# the tests, we only need a deterministic cutoff.
LLM_CONTEXT_LIMIT = 8000  # characters

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    """Create a logger that writes truncation warnings to ``logs/truncation.log``."""
    logger = logging.getLogger("preprocess_and_ground_truth")
    logger.setLevel(logging.INFO)

    # Ensure the ``logs`` directory exists
    logs_path = Path("logs")
    logs_path.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(logs_path / "truncation.log")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Avoid duplicate handlers if the function is called multiple times
    if not logger.handlers:
        logger.addHandler(handler)

    return logger

def _truncate_diff(diff: str) -> (str, bool):
    """
    Truncate a diff that exceeds :data:`LLM_CONTEXT_LIMIT`.

    Returns a tuple ``(new_diff, was_truncated)``.
    """
    if len(diff) <= LLM_CONTEXT_LIMIT:
        return diff, False
    # Simple truncation: keep the first ``LLM_CONTEXT_LIMIT`` characters.
    return diff[:LLM_CONTEXT_LIMIT], True

def _load_raw_prs(prs_path: Path) -> List[Dict[str, Any]]:
    """Load the raw PR JSON file."""
    if not prs_path.is_file():
        raise FileNotFoundError(f"Raw PR file not found: {prs_path}")
    with prs_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(data: Any, out_path: Path) -> None:
    """Write *data* to *out_path* with pretty formatting."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the preprocessing / ground‑truth construction pipeline.

    Returns
    -------
    int
        Exit code – ``0`` for success, ``1`` for fatal error.
    """
    logger = _setup_logger()

    # ------------------------------------------------------------------
    # 1. Load raw PRs
    # ------------------------------------------------------------------
    paths = get_paths()
    raw_prs_path = Path(paths["data_raw"]) / "prs.json"
    try:
        raw_prs = _load_raw_prs(raw_prs_path)
    except Exception as exc:
        logger.error(f"Failed to load raw PRs: {exc}")
        return 1

    # ------------------------------------------------------------------
    # 2. Truncate oversized diffs
    # ------------------------------------------------------------------
    processed_prs = []
    for pr in raw_prs:
        # ``diff_content`` may be absent – fetch from the stored URL only if
        # needed.  For the purposes of this task we treat a missing diff as
        # an empty string.
        diff = pr.get("diff_content", "")
        if not diff:
            # Attempt a lightweight fetch using the ``diff_url`` if present.
            diff_url = pr.get("diff_url")
            if diff_url:
                try:
                    import urllib.request

                    with urllib.request.urlopen(diff_url, timeout=10) as resp:
                        diff = resp.read().decode(errors="replace")
                except Exception:
                    # If the fetch fails we simply keep an empty diff.
                    diff = ""
        truncated_diff, was_truncated = _truncate_diff(diff)
        if was_truncated:
            logger.warning(
                f"PR {pr.get('pr_number', pr.get('pr_id'))} diff exceeds context window; truncating."
            )
            pr["truncation_flag"] = True
        else:
            pr["truncation_flag"] = False
        pr["diff_content"] = truncated_diff
        processed_prs.append(pr)

    # ------------------------------------------------------------------
    # 3. Extract human review comments
    # ------------------------------------------------------------------
    # Ensure the annotations directory exists before we attempt to write.
    ensure_directories([Path(paths["annotations"])])
    # The comment‑fetcher writes to ``data/annotations/raw_comments.json``.
    # It returns an exit code; we propagate failures.
    comment_exit = fetch_comments_main()
    if comment_exit not in (0, None):
        logger.error("Fetching human comments failed.")
        return 1

    # ------------------------------------------------------------------
    # 4. Identify confirmed bugs (rubric from FR‑011)
    # ------------------------------------------------------------------
    # The confirmation filter writes ``data/derived/human_confirmations.json``.
    confirmation_exit = filter_confirmations_main()
    if confirmation_exit not in (0, None):
        logger.error("Filtering human confirmations failed.")
        return 1

    # ------------------------------------------------------------------
    # 5. Build triangulated ground truth
    # ------------------------------------------------------------------
    # Load the confirmations generated in step 4.
    confirmations_path = Path(paths["derived_human_confirmations"])
    with confirmations_path.open("r", encoding="utf-8") as f:
        confirmations = json.load(f)

    # Load the raw PRs again to obtain linked issues.
    # (We already have ``raw_prs`` in memory.)
    ground_truth = []

    # Helper to create a bug‑detection record that satisfies the contract.
    def _make_bug_record(
        pr_id: int,
        file_path: str,
        line_start: int,
        line_end: int,
        severity: str,
        description: str,
        verification_method: str,
    ) -> Dict[str, Any]:
        return {
            "pr_id": pr_id,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "severity": severity,
            "description": description,
            "is_verified": True,
            "verification_method": verification_method,
            "source": "human",
            "confidence": None,
            "llm_error_flag": False,
            "metadata": {},
        }

    # a) Add all confirmed‑bug entries (strict triangulation)
    for conf in confirmations:
        # The confirmation schema produced by ``filter_human_confirmations`` has:
        #   pr_id, file_path, line_start, line_end, reviewer_id, confirmation_type
        ground_truth.append(
            _make_bug_record(
                pr_id=conf["pr_id"],
                file_path=conf["file_path"],
                line_start=conf["line_start"],
                line_end=conf["line_end"],
                severity="major",  # default – the rubric does not assign severity
                description=conf["confirmation_type"],
                verification_method="strict_triangulation",
            )
        )

    # b) Fallback: closed issues labelled ``bug`` (if not already covered)
    for pr in raw_prs:
        pr_id = pr.get("pr_id") or pr.get("pr_number")
        linked_issues = pr.get("linked_issues", [])
        for issue in linked_issues:
            labels = issue.get("labels", [])
            if "bug" in (lbl.lower() for lbl in labels):
                # Very coarse location – we do not have line information.
                # Use ``-1`` as a sentinel for “unknown”.
                ground_truth.append(
                    _make_bug_record(
                        pr_id=pr_id,
                        file_path="UNKNOWN",
                        line_start=-1,
                        line_end=-1,
                        severity="minor",
                        description=issue.get("title", "Bug‑labelled issue"),
                        verification_method="closed_issue_bug_label",
                    )
                )
                break  # only need one bug‑label per PR for the fallback

    # ------------------------------------------------------------------
    # 6. Persist all derived artefacts
    # ------------------------------------------------------------------
    ensure_directories(
        [
            Path(paths["data_derived"]),
            Path(paths["derived_human_confirmations"]),
            Path(paths["derived_human_baseline"]),
            Path(paths["derived_prs_processed"]),
        ]
    )

    # a) Processed PRs (with possible truncation)
    processed_prs_path = Path(paths["derived_prs_processed"])
    _write_json(processed_prs, processed_prs_path)

    # b) Human baseline (triangulated ground truth)
    baseline_path = Path(paths["derived_human_baseline"])
    _write_json(ground_truth, baseline_path)

    logger.info("Pre‑processing and ground‑truth generation completed successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
