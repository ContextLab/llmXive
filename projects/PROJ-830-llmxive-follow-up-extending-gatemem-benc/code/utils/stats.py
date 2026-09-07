import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import glm as sm_glm
from statsmodels.formula.api import mixedlm as sm_mixedlm

logger = logging.getLogger(__name__)

def pair_episodes(
    gatekeeper_results: List[Dict[str, Any]],
    baseline_results: List[Dict[str, Any]]
) -> List[Tuple[float, float]]:
    """
    Match episodes across Gatekeeper and Baseline conditions using `episode_id`.

    This is a definition-only task (T008f) intended to be executed later when
    real pipeline outputs (T023, T017c) are available.

    Args:
        gatekeeper_results: List of dicts from Gatekeeper pipeline.
            Expected keys: ['episode_id', 'score', ...]
        baseline_results: List of dicts from Baseline pipeline.
            Expected keys: ['episode_id', 'score', ...]

    Returns:
        List of tuples (gatekeeper_score, baseline_score) paired by episode_id.

    Raises:
        ValueError: If `episode_id` is missing from an episode or if an episode_id
                    in one list does not have a matching pair in the other.
    """
    logger.debug(f"Pairing {len(gatekeeper_results)} Gatekeeper episodes with {len(baseline_results)} Baseline episodes.")

    # Index baseline results by episode_id for O(1) lookup
    baseline_map: Dict[str, float] = {}
    for entry in baseline_results:
        if 'episode_id' not in entry:
            raise ValueError("Baseline episode missing 'episode_id' key.")
        if 'score' not in entry:
            raise ValueError(f"Baseline episode {entry['episode_id']} missing 'score' key.")
        baseline_map[entry['episode_id']] = float(entry['score'])

    paired_data: List[Tuple[float, float]] = []
    unmatched_gk: List[str] = []
    unmatched_b: List[str] = []

    for entry in gatekeeper_results:
        if 'episode_id' not in entry:
            raise ValueError("Gatekeeper episode missing 'episode_id' key.")
        if 'score' not in entry:
            raise ValueError(f"Gatekeeper episode {entry['episode_id']} missing 'score' key.")

        gid = entry['episode_id']
        g_score = float(entry['score'])

        if gid in baseline_map:
          paired_data.append((g_score, baseline_map[gid]))
        else:
          unmatched_gk.append(gid)

    # Check for baseline episodes that were not matched
    for b_id in baseline_map:
        if b_id not in [e['episode_id'] for e in gatekeeper_results]:
            unmatched_b.append(b_id)

    if unmatched_gk or unmatched_b:
        error_msg = "Episode ID mismatch detected during pairing.\n"
        if unmatched_gk:
            error_msg += f"  Gatekeeper episodes without baseline match: {unmatched_gk[:5]}... (total {len(unmatched_gk)})\n"
        if unmatched_b:
            error_msg += f"  Baseline episodes without Gatekeeper match: {unmatched_b[:5]}... (total {len(unmatched_b)})"
        raise ValueError(error_msg)

    logger.info(f"Successfully paired {len(paired_data)} episodes.")
    return paired_data