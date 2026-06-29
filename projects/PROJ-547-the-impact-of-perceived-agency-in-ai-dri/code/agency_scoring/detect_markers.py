from __future__ import annotations

import re
from typing import Dict, List

# Logging utilities
from logging.pipeline_logger import get_logger, log_dict


def _detect_marker_in_utterance(utterance: str) -> Dict[str, bool]:
    """
    Detect the presence of predefined linguistic markers in a single utterance.

    Markers:
    - modal: modal verbs (can, could, may, might, must, should, will, would)
    - choice: choice constructions (either, or, whether)
    - collaborative: collaborative phrasing (we, let's, together, us)
    - open_question: open‑ended questions (how, what, why, tell me, describe) ending with '?'

    Returns a dictionary mapping marker names to booleans.
    """
    text = utterance.lower()

    markers = {
        "modal": bool(re.search(r"\b(can|could|may|might|must|should|will|would)\b", text)),
        "choice": bool(re.search(r"\b(either|or|whether)\b", text)),
        "collaborative": bool(re.search(r"\b(we|let's|together|us)\b", text)),
        "open_question": bool(re.search(r"^(how|what|why|tell me|describe)\b.*\?$", text)),
    }
    return markers


def detect_markers(utterances: List[str]) -> List[Dict[str, bool]]:
    """
    Detect linguistic markers for each utterance in a list.

    Parameters
    ----------
    utterances: List[str]
        List of utterance strings.

    Returns
    -------
    List[Dict[str, bool]]
        A list where each element corresponds to an utterance and contains a dict of
        marker detections.
    """
    logger = get_logger()
    results: List[Dict[str, bool]] = []

    for utt in utterances:
        detection = _detect_marker_in_utterance(utt)
        results.append(detection)

    # Log after processing the batch
    log_dict(
        {
            "step": "detect_markers",
            "status": "completed",
            "utterances_processed": len(utterances),
        }
    )
    logger.debug(f"Marker detection results: {results}")
    return results


def main() -> None:
    """
    Simple CLI for manual testing. Reads a JSON file containing a list of utterances.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Detect linguistic markers")
    parser.add_argument(
        "utterances_path", type=str, help="Path to JSON file containing a list of utterances"
    )
    args = parser.parse_args()

    with open(args.utterances_path, "r", encoding="utf-8") as f:
        utterances = json.load(f)

    detections = detect_markers(utterances)
    print(detections)