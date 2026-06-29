"""Compute agency scores for AI‑CBT conversation sessions.

This script reads a transcript CSV (produced by ``ingest_transcripts``), detects
linguistic markers of perceived agency, applies configurable marker weights,
and writes a CSV with a normalized agency score per session.

Edge‑case handling (FR‑003):
* If a transcript row has an empty or missing ``utterances`` field, the
  session receives a score of ``0.0`` and a warning is logged.
* If the input file cannot be read (e.g. unreadable CSV), the script logs a
  warning and creates an empty output file.

The script is invoked via the ``main`` entry point and can also be used as a
library by calling :func:`compute_agency_scores`.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd

from agency_scoring.detect_markers import detect_markers
from config.config_loader import load_config
from logging.pipeline_logger import get_logger, log_dict

__all__ = ["compute_agency_scores", "main"]

LOGGER = get_logger(__name__)

def _load_transcripts(transcript_path: Path) -> pd.DataFrame:
    """Load the transcript CSV.

    The expected columns are ``session_id`` and ``utterances``. ``utterances``
    should contain a JSON‑encoded list of strings (one utterance per item) or
    a plain string where utterances are separated by ``\\n``.

    Returns an empty DataFrame on failure and logs a warning.
    """
    if not transcript_path.exists():
        log_dict(
            {
                "event": "transcript_file_missing",
                "path": str(transcript_path),
                "message": "Transcript file not found – proceeding with empty data.",
            }
        )
        return pd.DataFrame(columns=["session_id", "utterances"])

    try:
        df = pd.read_csv(transcript_path, dtype=str)
    except Exception as exc:  # pragma: no cover – defensive
        log_dict(
            {
                "event": "transcript_file_unreadable",
                "path": str(transcript_path),
                "error": str(exc),
                "message": "Unable to read transcript file – proceeding with empty data.",
            }
        )
        return pd.DataFrame(columns=["session_id", "utterances"])

    # Ensure required columns exist
    required = {"session_id", "utterances"}
    missing = required - set(df.columns)
    if missing:
        log_dict(
            {
                "event": "transcript_missing_columns",
                "missing_columns": list(missing),
                "message": "Missing required columns – treating rows as empty.",
            }
        )
        # Fill missing columns with empty strings so downstream logic works
        for col in missing:
            df[col] = ""
    return df

def _normalize_score(raw_score: float, max_score: float) -> float:
    """Normalize a raw score to the range [0, 1]."""
    if max_score == 0:
        return 0.0
    return max(0.0, min(1.0, raw_score / max_score))

def compute_agency_scores(
    transcript_path: Path,
    weights_path: Path,
    output_path: Path,
) -> None:
    """Compute agency scores and write them to ``output_path``.

    Parameters
    ----------
    transcript_path
        Path to the CSV file containing ``session_id`` and ``utterances``.
    weights_path
        Path to a YAML file mapping marker names to numeric weights.
    output_path
        Destination CSV file with columns ``session_id`` and ``agency_score``.
    """
    LOGGER.info("Starting agency score computation.")
    df = _load_transcripts(transcript_path)

    # Load weights – fallback to equal weighting if the file is missing/invalid
    try:
        weights: Dict[str, float] = load_config(weights_path)
    except Exception as exc:  # pragma: no cover – defensive
        log_dict(
            {
                "event": "weights_load_failure",
                "path": str(weights_path),
                "error": str(exc),
                "message": "Using default weight of 1.0 for all markers.",
            }
        )
        weights = {}

    # Default weight of 1.0 for any marker not explicitly weighted
    default_weight = 1.0
    all_weights = {marker: weights.get(marker, default_weight) for marker in detect_markers.__annotations__.get("return", [])}
    # If we cannot infer marker names, just use a generic weight dict
    if not all_weights:
        all_weights = {marker: default_weight for marker in ["modal_verb", "choice_construction", "collaborative_phrase", "open_ended_question"]}

    max_possible_score = sum(all_weights.values())

    results: List[Dict[str, object]] = []

    for _, row in df.iterrows():
        session_id = row.get("session_id", "")
        utterances_raw = row.get("utterances", "")

        # Normalise utterances into a list of strings
        if pd.isna(utterances_raw) or not utterances_raw.strip():
            # Edge case: empty or missing utterances
            log_dict(
                {
                    "event": "empty_transcript",
                    "session_id": session_id,
                    "message": "Empty or unreadable transcript – assigning score 0.0",
                }
            )
            score = 0.0
            results.append({"session_id": session_id, "agency_score": score})
            continue

        # Attempt to parse JSON list; fall back to newline split
        try:
            utterances: List[str] = pd.read_json(utterances_raw, typ="series").tolist()
        except Exception:
            utterances = [u.strip() for u in utterances_raw.splitlines() if u.strip()]

        # Concatenate utterances for marker detection
        concatenated = " ".join(utterances)

        # Detect markers
        try:
            detected_markers = detect_markers(concatenated)
        except Exception as exc:  # pragma: no cover – defensive
            log_dict(
                {
                    "event": "marker_detection_failure",
                    "session_id": session_id,
                    "error": str(exc),
                    "message": "Marker detection failed – assigning score 0.0",
                }
            )
            detected_markers = []

        # Compute weighted score
        raw_score = sum(all_weights.get(marker, default_weight) for marker in detected_markers)
        score = _normalize_score(raw_score, max_possible_score)

        results.append({"session_id": session_id, "agency_score": score})

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["session_id", "agency_score"])
        writer.writeheader()
        writer.writerows(results)

    LOGGER.info("Agency score computation completed.")
    log_dict(
        {
            "event": "agency_scores_written",
            "output_path": str(output_path),
            "records_written": len(results),
        }
    )

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute agency scores from transcript data."
    )
    parser.add_argument(
        "--transcripts",
        type=Path,
        required=True,
        help="Path to CSV file containing session transcripts.",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="Path to YAML file with marker weights.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination CSV file for agency scores.",
    )
    return parser

def main() -> None:
    """Entry point for the CLI."""
    parser = _build_arg_parser()
    args = parser.parse_args()
    compute_agency_scores(args.transcripts, args.weights, args.output)

if __name__ == "__main__":
    main()
