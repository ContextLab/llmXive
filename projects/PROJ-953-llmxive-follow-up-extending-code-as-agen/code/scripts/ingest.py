import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from scripts.config import SAMPLE_SIZE

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_valid_python_syntax(code: Any) -> bool:
    """
    Return True if *code* is a non‑empty string containing valid Python syntax.
    """
    import ast

    if not isinstance(code, str) or not code.strip():
        return False
    try:
        ast.parse(code)
        return True
    except Exception:  # pragma: no cover – syntax errors are expected in tests
        return False

# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_swe_bench(streaming: bool = True) -> Iterable[Dict[str, Any]]:
    """
    Load the SWE‑Bench Lite dataset from HuggingFace.
    """
    logger.info("Loading SWE‑Bench Lite dataset (streaming=%s)", streaming)
    return load_dataset(
        "princeton-nlp/SWE-bench_Lite",
        split="train",
        streaming=streaming,
    )

def load_agent_bench(streaming: bool = True) -> Iterable[Dict[str, Any]]:
    """
    Load the AgentBench dataset from HuggingFace.
    """
    logger.info("Loading AgentBench dataset (streaming=%s)", streaming)
    return load_dataset(
        "openbmb/AgentBench",
        split="dev",
        streaming=streaming,
    )

# ---------------------------------------------------------------------------
# Parsing logic – matches unit‑tests expectations
# ---------------------------------------------------------------------------

def parse_swe_bench(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single SWE‑Bench record.

    Expected output keys (used later by the pipeline):
        - task_id
        - source_dataset
        - code_diff
        - original_code
        - problem_statement
        - hints
        - eval_info
        - repo
        - dataset_name
        - status
        - is_unparseable
    """
    # Basic fields – fall back to empty strings if missing
    task_id = record.get("instance_id", "unknown")
    code_diff = record.get("patch", "")
    original_code = record.get("base_commit_code", "")
    problem_statement = record.get("problem_statement", "")
    hints = record.get("hints_text", "")
    eval_info = {
        "FAIL_TO_PASS": record.get("FAIL_TO_PASS", []),
        "PASS_TO_PASS": record.get("PASS_TO_PASS", []),
    }
    repo = record.get("repo", "")

    # Determine parseability of the *diff* (the code we will try to apply)
    unparseable = not _is_valid_python_syntax(code_diff)

    return {
        "task_id": task_id,
        "source_dataset": "swe-bench",
        "code_diff": code_diff,
        "original_code": original_code,
        "problem_statement": problem_statement,
        "hints": hints,
        "eval_info": json.dumps(eval_info),
        "repo": repo,
        "dataset_name": "swe-bench",
        "status": "Unparseable" if unparseable else "Parsed",
        "is_unparseable": unparseable,
    }

def parse_agent_bench(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single AgentBench record.

    Expected output keys match those of ``parse_swe_bench`` where applicable.
    """
    task_id = record.get("instance_id", record.get("id", "unknown"))
    # Prefer ``answer``; fall back to ``context`` if answer is empty
    code_diff = record.get("answer") or record.get("context", "")
    original_code = ""  # AgentBench does not provide original code
    problem_statement = record.get("question", "")
    repo = ""  # Not provided by AgentBench

    unparseable = not _is_valid_python_syntax(code_diff)

    return {
        "task_id": task_id,
        "source_dataset": "agent-bench",
        "code_diff": code_diff,
        "original_code": original_code,
        "problem_statement": problem_statement,
        "hints": "",
        "eval_info": json.dumps({}),
        "repo": repo,
        "dataset_name": "agent-bench",
        "status": "Unparseable" if unparseable else "Parsed",
        "is_unparseable": unparseable,
    }

# ---------------------------------------------------------------------------
# Merging and sampling
# ---------------------------------------------------------------------------

def merge_datasets(
    swe_iter: Iterable[Dict[str, Any]],
    agent_iter: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Consume the two iterables, parse each entry and return a combined list.
    """
    merged: List[Dict[str, Any]] = []

    for raw in swe_iter:
        merged.append(parse_swe_bench(raw))

    for raw in agent_iter:
        merged.append(parse_agent_bench(raw))

    return merged

def sample_subset(
    data: List[Dict[str, Any]], sample_size: int
) -> List[Dict[str, Any]]:
    """
    Return exactly ``sample_size`` items.
    If the source contains fewer items, the whole list is returned.
    """
    if len(data) <= sample_size:
        return data
    # deterministic sampling for reproducibility – take the first N items
    return data[:sample_size]

# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def write_parquet(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

def write_json(data: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest SWE‑Bench and AgentBench, sample, and write parquet files."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=SAMPLE_SIZE,
        help="Number of tasks to sample from the combined datasets (default: env SAMPLE_SIZE).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Placeholder argument kept for compatibility with the quick‑start script.",
    )
    args = parser.parse_args()

    # Load raw streaming datasets
    swe_iter = load_swe_bench(streaming=True)
    agent_iter = load_agent_bench(streaming=True)

    # Parse & merge
    logger.info("Parsing and merging datasets...")
    merged = merge_datasets(swe_iter, agent_iter)

    # Sample
    logger.info("Sampling %d tasks...", args.sample_size)
    sampled = sample_subset(merged, args.sample_size)

    # Convert to DataFrame
    df = pd.DataFrame(sampled)

    # Write parquet files – one per original dataset
    swe_df = df[df["source_dataset"] == "swe-bench"]
    agent_df = df[df["source_dataset"] == "agent-bench"]

    swe_path = paths.data("raw", "swe_bench_subset.parquet")
    agent_path = paths.data("raw", "agentbench_subset.parquet")
    write_parquet(swe_df, swe_path)
    write_parquet(agent_df, agent_path)

    # Log sampling metadata
    log_path = paths.data("logs", "ingest_sample_log.json")
    log_data = {
        "requested_sample_size": args.sample_size,
        "actual_sample_size": len(sampled),
        "swe_bench_rows": int(swe_df.shape[0]),
        "agentbench_rows": int(agent_df.shape[0]),
    }
    write_json(log_data, log_path)

    logger.info("Ingestion complete. Parquet files written to %s and %s", swe_path, agent_path)
    logger.info("Sampling log written to %s", log_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        sys.exit(1)