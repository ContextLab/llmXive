"""
Rubric implementation for Human-Agent Alignment scoring.

Implements the scoring function defined in FR-005 and SC-002:
score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness

Components:
- intent_match: Binary (1.0) or continuous (0.0-1.0) score indicating if the agent's
  response matched the user's intent.
- latency_penalty: A normalized penalty (0.0-1.0) derived from the observed latency
  relative to a maximum acceptable threshold. Higher latency = higher penalty.
- ui_completeness: A score (0.0-1.0) representing the completeness of the generated UI
  (e.g., based on element count or structural coverage).
"""

from typing import Optional, Dict, Any
import logging

# Import logging utility from the project's existing API surface
try:
    from utils.logging import get_experiment_logger
except ImportError:
    # Fallback for direct execution without full package context
    def get_experiment_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_experiment_logger(__name__)

# Constants for the scoring function (FR-005, SC-002)
WEIGHT_INTENT_MATCH = 0.4
WEIGHT_LATENCY_PENALTY = 0.3
WEIGHT_UI_COMPLETENESS = 0.3

# Default maximum acceptable latency in seconds for penalty calculation
# This value can be configured or passed as an argument
DEFAULT_MAX_LATENCY_SECONDS = 5.0


def calculate_latency_penalty(
    observed_latency_seconds: float,
    max_latency_seconds: Optional[float] = None
) -> float:
    """
    Calculate the latency penalty component (0.0 to 1.0).

    The penalty is 0.0 if latency is 0, and increases linearly up to 1.0
    when observed_latency equals max_latency_seconds.
    Values exceeding max_latency_seconds are capped at 1.0.

    Args:
        observed_latency_seconds: The measured latency in seconds.
        max_latency_seconds: The threshold beyond which penalty is 1.0.
                             Defaults to DEFAULT_MAX_LATENCY_SECONDS.

    Returns:
        A float between 0.0 and 1.0 representing the latency penalty.
    """
    if max_latency_seconds is None:
        max_latency_seconds = DEFAULT_MAX_LATENCY_SECONDS

    if max_latency_seconds <= 0:
        logger.warning("max_latency_seconds must be positive. Defaulting to 1.0s.")
        max_latency_seconds = 1.0

    penalty = observed_latency_seconds / max_latency_seconds
    return min(1.0, max(0.0, penalty))


def calculate_alignment_score(
    intent_match: float,
    observed_latency_seconds: float,
    ui_completeness: float,
    max_latency_seconds: Optional[float] = None
) -> float:
    """
    Calculate the Human-Agent Alignment score.

    Formula (FR-005, SC-002):
    score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness

    Args:
        intent_match: Score between 0.0 and 1.0 indicating intent matching quality.
        observed_latency_seconds: The actual latency observed during the interaction.
        ui_completeness: Score between 0.0 and 1.0 indicating UI completeness.
        max_latency_seconds: The threshold for calculating latency penalty.

    Returns:
        A float between 0.0 and 1.0 representing the final alignment score.
    """
    # Validate inputs
    if not 0.0 <= intent_match <= 1.0:
        raise ValueError(f"intent_match must be between 0.0 and 1.0, got {intent_match}")
    if not 0.0 <= ui_completeness <= 1.0:
        raise ValueError(f"ui_completeness must be between 0.0 and 1.0, got {ui_completeness}")
    if observed_latency_seconds < 0:
        raise ValueError(f"observed_latency_seconds cannot be negative, got {observed_latency_seconds}")

    # Calculate components
    latency_penalty = calculate_latency_penalty(observed_latency_seconds, max_latency_seconds)
    latency_component = 1.0 - latency_penalty

    # Calculate final score
    score = (
        WEIGHT_INTENT_MATCH * intent_match +
        WEIGHT_LATENCY_PENALTY * latency_component +
        WEIGHT_UI_COMPLETENESS * ui_completeness
    )

    logger.debug(
        f"Alignment Score Calculation: "
        f"intent_match={intent_match:.3f}, "
        f"latency_penalty={latency_penalty:.3f} (latency={observed_latency_seconds:.3f}s), "
        f"ui_completeness={ui_completeness:.3f} -> "
        f"score={score:.3f}"
    )

    return score


def score_interaction(
    interaction_data: Dict[str, Any],
    max_latency_seconds: Optional[float] = None
) -> Dict[str, float]:
    """
    Score a single interaction based on rubric metrics.

    Expected keys in interaction_data:
    - 'intent_match': float (0.0-1.0)
    - 'latency_seconds': float
    - 'ui_completeness': float (0.0-1.0)

    Args:
        interaction_data: Dictionary containing interaction metrics.
        max_latency_seconds: Optional override for max latency threshold.

    Returns:
        Dictionary with individual component scores and the final alignment score.
    """
    intent_match = interaction_data.get('intent_match', 0.0)
    latency_seconds = interaction_data.get('latency_seconds', 0.0)
    ui_completeness = interaction_data.get('ui_completeness', 0.0)

    latency_penalty = calculate_latency_penalty(latency_seconds, max_latency_seconds)
    alignment_score = calculate_alignment_score(
        intent_match, latency_seconds, ui_completeness, max_latency_seconds
    )

    return {
        'intent_match': intent_match,
        'latency_penalty': latency_penalty,
        'latency_seconds': latency_seconds,
        'ui_completeness': ui_completeness,
        'alignment_score': alignment_score
    }


def main():
    """
    CLI entry point for testing the rubric scoring function.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Calculate Human-Agent Alignment Score")
    parser.add_argument('--intent-match', type=float, required=True, help="Intent match score (0.0-1.0)")
    parser.add_argument('--latency', type=float, required=True, help="Observed latency in seconds")
    parser.add_argument('--ui-completeness', type=float, required=True, help="UI completeness score (0.0-1.0)")
    parser.add_argument('--max-latency', type=float, default=DEFAULT_MAX_LATENCY_SECONDS,
                        help=f"Max latency threshold (default: {DEFAULT_MAX_LATENCY_SECONDS}s)")
    parser.add_argument('--output', type=str, help="Output JSON file path")

    args = parser.parse_args()

    result = score_interaction(
        {
            'intent_match': args.intent_match,
            'latency_seconds': args.latency,
            'ui_completeness': args.ui_completeness
        },
        max_latency_seconds=args.max_latency
    )

    output_json = json.dumps(result, indent=2)
    print(output_json)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        logger.info(f"Results written to {args.output}")


if __name__ == '__main__':
    main()