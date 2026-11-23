"""
Complexity Calculator Module.

This module handles the aggregation of syntactic and lexical metrics
into a final Syntactic Complexity Score.

It implements the weighted average formula and the critical normalization
logic to clamp the raw score strictly to the [0.0, 1.0] range.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def calculate_raw_score(
    parse_depth: float,
    clause_count: float,
    mtld: float,
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate the raw weighted average score from individual metrics.

    Args:
        parse_depth: Tree depth from syntactic parsing.
        clause_count: Number of clauses detected.
        mtld: Measure of Textual Lexical Diversity.
        weights: Optional dictionary of weights for each metric.
                 Defaults to equal weighting.

    Returns:
        float: The un-normalized raw score.
    """
    if weights is None:
        weights = {
            "parse_depth": 1.0,
            "clause_count": 1.0,
            "mtld": 1.0
        }

    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0

    weighted_sum = (
        (parse_depth * weights.get("parse_depth", 0)) +
        (clause_count * weights.get("clause_count", 0)) +
        (mtld * weights.get("mtld", 0))
    )

    return weighted_sum / total_weight


def normalize_score(raw_score: float) -> float:
    """
    Normalize the raw score to the strict [0.0, 1.0] range.

    This function implements the min-max scaling logic required by
    the project specification (Task T013b). It ensures that the
    Syntactic Complexity Score is bounded, preventing outliers from
    skewing downstream routing decisions.

    Logic:
    1. If raw_score < 0.0, clamp to 0.0.
    2. If raw_score > 1.0, clamp to 1.0.
    3. Otherwise, return raw_score as-is.

    Args:
        raw_score (float): The un-normalized score calculated by
                           `calculate_raw_score`.

    Returns:
        float: The normalized score strictly within [0.0, 1.0].
    """
    if raw_score < 0.0:
        logger.warning(f"Raw score {raw_score} is below 0.0. Clamping to 0.0.")
        return 0.0
    if raw_score > 1.0:
        logger.warning(f"Raw score {raw_score} is above 1.0. Clamping to 1.0.")
        return 1.0
    return float(raw_score)


def compute_complexity_score(
    parse_depth: float,
    clause_count: float,
    mtld: float,
    weights: Dict[str, float] = None
) -> float:
    """
    End-to-end function to compute the final normalized Syntactic Complexity Score.

    This function orchestrates the calculation of the raw weighted score
    and its subsequent normalization to the [0.0, 1.0] interval.

    Args:
        parse_depth (float): Syntactic tree depth.
        clause_count (float): Clause count.
        mtld (float): Lexical diversity metric.
        weights (Dict[str, float], optional): Weights for the metrics.

    Returns:
        float: The final normalized score in [0.0, 1.0].
    """
    raw = calculate_raw_score(parse_depth, clause_count, mtld, weights)
    normalized = normalize_score(raw)
    return normalized
