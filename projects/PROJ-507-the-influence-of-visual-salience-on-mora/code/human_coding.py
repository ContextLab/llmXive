"""
Human coding utilities for processing ambiguity annotations.

This module provides:
- `calculate_fleiss_kappa`: compute Fleiss' Kappa for inter‑rater agreement.
- `process_annotations`: apply majority‑vote logic, enforce a minimum number of
  annotators per scenario, and return the cleaned annotation table together
  with the overall kappa score.
- `cross_reference_external_validation`: compare a list of scenario IDs against an
  external MoralD JSON file and keep only those marked as ambiguous (or those not
  present in the external file, which are kept by default).

The functions are deliberately lightweight and have no side‑effects – they are
pure data‑processing helpers used by the pipeline script
``code/03_process_human_coding.py`` and by the unit tests in
``tests/unit/test_human_coding.py``.
"""

import json
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa

# ----------------------------------------------------------------------
# Configuration constants (used by the tests)
# ----------------------------------------------------------------------
MIN_ANNOTATORS: int = 3
"""Minimum number of distinct annotators required for a scenario to be kept."""

KAPPA_THRESHOLD: float = 0.6
"""Minimum Fleiss' Kappa required for the set of retained scenarios."""

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _build_rating_matrix(df: pd.DataFrame) -> np.ndarray:
    """
    Build the rating‑count matrix required by ``statsmodels``' ``fleiss_kappa``.
    Rows correspond to items (scenarios), columns to rating categories
    (1‑5). Each cell contains the number of annotators that gave that rating.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``scenario_id`` and ``rating`` columns.

    Returns
    -------
    np.ndarray
        Shape ``(n_items, n_categories)``.
    """
    # Ensure the rating column is integer and within 1‑5
    df = df.copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype(int)
    # Build a crosstab: rows = scenario_id, columns = rating (1‑5)
    matrix = pd.crosstab(df["scenario_id"], df["rating"])
    # Ensure all five categories are present as columns
    for cat in range(1, 6):
        if cat not in matrix.columns:
            matrix[cat] = 0
    # Order columns 1‑5
    matrix = matrix[[1, 2, 3, 4, 5]]
    return matrix.values

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def calculate_fleiss_kappa(df: pd.DataFrame) -> float:
    """
    Compute Fleiss' Kappa for a set of annotations.

    The function expects a DataFrame with columns ``scenario_id``,
    ``annotator_id`` and ``rating`` (1‑5 Likert).  Scenarios with fewer
    than ``MIN_ANNOTATORS`` annotators are ignored for the purpose of the
    agreement calculation – this mirrors the behaviour of the
    ``process_annotations`` helper.

    Parameters
    ----------
    df : pd.DataFrame
        Annotation table.

    Returns
    -------
    float
        Fleiss' Kappa (range ``[-1, 1]``).  ``1`` indicates perfect
        agreement, values near ``0`` indicate chance‑level agreement.
    """
    # Filter out scenarios that do not meet the annotator minimum
    annotator_counts = df.groupby("scenario_id")["annotator_id"].nunique()
    valid_scenarios = annotator_counts[annotator_counts >= MIN_ANNOTATORS].index
    filtered = df[df["scenario_id"].isin(valid_scenarios)]

    if filtered.empty:
        # No data to compute agreement – by definition agreement is 0
        return 0.0

    rating_matrix = _build_rating_matrix(filtered)
    # ``fleiss_kappa`` returns a tuple (kappa, se); we only need the kappa.
    kappa = fleiss_kappa(rating_matrix)
    return float(kappa)

def process_annotations(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """
    Apply majority‑vote logic to raw annotation rows.

    The workflow mirrors the specification in ``tasks.md`` and the unit
    tests:

    * Exclude any scenario that has fewer than ``MIN_ANNOTATORS`` distinct
      annotators.
    * For each remaining scenario, compute the most common rating.
      If that rating appears **strictly more** than half of the annotators,
      it is taken as the ``final_rating``; otherwise the scenario is
      discarded (no clear majority).
    * Return a DataFrame with columns ``scenario_id`` and ``final_rating``,
      together with the overall Fleiss' Kappa for the retained data.

    Parameters
    ----------
    df : pd.DataFrame
        Raw annotation table (must contain ``scenario_id``,
        ``annotator_id`` and ``rating``).

    Returns
    -------
    Tuple[pd.DataFrame, float]
        ``(result_df, kappa)`` where ``result_df`` holds the majority‑voted
        ratings and ``kappa`` is the agreement score.
    """
    # ------------------------------------------------------------------
    # 1. Enforce minimum annotator count per scenario
    # ------------------------------------------------------------------
    annotator_counts = df.groupby("scenario_id")["annotator_id"].nunique()
    sufficient = annotator_counts[annotator_counts >= MIN_ANNOTATORS].index
    df_sufficient = df[df["scenario_id"].isin(sufficient)].copy()

    # ------------------------------------------------------------------
    # 2. Majority‑vote per scenario
    # ------------------------------------------------------------------
    def majority_vote(group: pd.DataFrame) -> Tuple[int, bool]:
        """
        Return (rating, has_majority). ``has_majority`` is True iff the
        most common rating occurs > 50 % of the annotations.
        """
        counts = group["rating"].value_counts()
        top_rating = counts.idxmax()
        top_count = counts.max()
        has_majority = top_count > (len(group) / 2)
        return top_rating, has_majority

    records = []
    for scenario_id, grp in df_sufficient.groupby("scenario_id"):
        rating, has_majority = majority_vote(grp)
        if has_majority:
            records.append({"scenario_id": scenario_id, "final_rating": rating})

    result_df = pd.DataFrame(records)

    # ------------------------------------------------------------------
    # 3. Compute overall Fleiss' Kappa on the *original* (filtered) data
    # ------------------------------------------------------------------
    kappa = calculate_fleiss_kappa(df)

    return result_df, kappa

def cross_reference_external_validation(
    scenario_ids: List[str],
    external_json_path: str,
) -> List[str]:
    """
    Keep only those ``scenario_ids`` that are either:

    * Not present in the external JSON file, or
    * Present **and** marked ``\"is_ambiguous\": true``.

    The external file follows the format used in
    ``data/external/morald_tags.json`` – a mapping from scenario ID to a
    dictionary that contains at least the key ``is_ambiguous``.

    Parameters
    ----------
    scenario_ids : List[str]
        List of scenario identifiers produced by the pipeline.
    external_json_path : str
        Path to the JSON file containing external validation information.

    Returns
    -------
    List[str]
        Sub‑set of ``scenario_ids`` that survive the external check.
    """
    with open(external_json_path, "r") as f:
        external_data = json.load(f)

    kept = []
    for sid in scenario_ids:
        entry = external_data.get(sid)
        if entry is None:
            # No entry → assume ambiguous (fallback behaviour)
            kept.append(sid)
        else:
            if entry.get("is_ambiguous", False):
                kept.append(sid)
            # else: explicitly non‑ambiguous → drop
    return kept
