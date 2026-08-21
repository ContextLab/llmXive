"""
Precedence Rule Logic Module (FR-017)

This module explicitly enforces the precedence rule where the randomized
counterfactual intervention (T047) overrides the deterministic fallback
for frames in the randomized subset.

Logic: resolve_skip_decision(frame_id, uncertainty, randomized_flag)
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Set

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def load_counterfactual_indices(counterfactual_path: str) -> Set[int]:
    """
    Load the set of frame IDs that are part of the randomized counterfactual intervention.

    Args:
        counterfactual_path: Path to the parquet file containing frame_id column.

    Returns:
        A set of integers representing frame IDs in the randomized subset.
    """
    import pandas as pd

    path = Path(counterfactual_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Counterfactual indices file not found: {counterfactual_path}. "
            "Ensure T047 has completed successfully."
        )

    logger.info(f"Loading counterfactual indices from {counterfactual_path}")
    df = pd.read_parquet(path)

    if "frame_id" not in df.columns:
        raise ValueError(
            f"Expected 'frame_id' column in {counterfactual_path}, "
            f"found columns: {list(df.columns)}"
        )

    indices = set(df["frame_id"].astype(int).tolist())
    logger.info(f"Loaded {len(indices)} counterfactual frame IDs")
    return indices

def resolve_skip_decision(
    frame_id: int,
    uncertainty: float,
    randomized_flag: bool,
    fallback_threshold: float = 0.8,
    delta_magnitude: Optional[float] = None,
    high_delta_threshold: float = 0.5
) -> Tuple[bool, str]:
    """
    Enforce the precedence rule (FR-017) to determine if a frame should be skipped.

    Precedence Rule Logic:
    1. If the frame is in the randomized counterfactual subset (randomized_flag=True),
       the decision is OVERRIDDEN to force a skip (skip=True) regardless of the
       estimator's uncertainty or delta magnitude. This ensures the intervention
       is applied as designed.
    2. If the frame is NOT in the randomized subset, use the deterministic fallback logic:
       - Skip if uncertainty > fallback_threshold OR delta_magnitude > high_delta_threshold.
       - Otherwise, do not skip (run full solver).

    Args:
        frame_id: The unique identifier for the current frame.
        uncertainty: The uncertainty score predicted by the estimator (0.0 to 1.0).
        randomized_flag: Boolean indicating if this frame is in the randomized subset.
        fallback_threshold: Threshold for uncertainty to trigger fallback (default 0.8).
        delta_magnitude: The predicted latent delta magnitude (optional).
        high_delta_threshold: Threshold for delta magnitude to trigger fallback.

    Returns:
        Tuple of (skip_decision: bool, reason: str).
        - skip_decision: True if the frame should be skipped (use estimator), False if full solver.
        - reason: Explanation of why the decision was made.
    """
    # Precedence Rule: Randomized intervention overrides deterministic fallback
    if randomized_flag:
        # FR-017: Randomized counterfactual intervention overrides deterministic fallback
        return True, "Precedence Rule: Forced skip due to randomized counterfactual intervention (T047)"

    # Deterministic fallback logic (only if not randomized)
    reason_parts = []
    should_skip = False

    # Check uncertainty threshold
    if uncertainty > fallback_threshold:
        should_skip = True
        reason_parts.append(f"uncertainty ({uncertainty:.4f}) > {fallback_threshold}")

    # Check delta magnitude threshold if provided
    if delta_magnitude is not None:
        if delta_magnitude > high_delta_threshold:
            should_skip = True
            reason_parts.append(f"delta_magnitude ({delta_magnitude:.4f}) > {high_delta_threshold}")

    if should_skip:
        return True, f"Deterministic fallback triggered: {'; '.join(reason_parts)}"
    else:
        return False, "Deterministic fallback: No thresholds exceeded, running full solver"

def apply_precedence_rule(
    frame_id: int,
    uncertainty: float,
    randomized_indices: Set[int],
    delta_magnitude: Optional[float] = None
) -> Tuple[bool, str]:
    """
    High-level wrapper to apply the precedence rule given a set of randomized indices.

    Args:
        frame_id: The current frame ID.
        uncertainty: The model's uncertainty score.
        randomized_indices: The set of frame IDs from the counterfactual intervention.
        delta_magnitude: Optional delta magnitude for deterministic logic.

    Returns:
        Tuple of (skip_decision, reason).
    """
    randomized_flag = frame_id in randomized_indices
    return resolve_skip_decision(
        frame_id=frame_id,
        uncertainty=uncertainty,
        randomized_flag=randomized_flag,
        delta_magnitude=delta_magnitude
    )

def main():
    """
    CLI entry point for testing the precedence rule logic.
    """
    parser = argparse.ArgumentParser(
        description="Test the precedence rule logic for T045a"
    )
    parser.add_argument(
        "--counterfactual-path",
        type=str,
        default="data/processed/counterfactual_indices.parquet",
        help="Path to the counterfactual indices parquet file"
    )
    parser.add_argument(
        "--test-frame",
        type=int,
        default=12345,
        help="A sample frame ID to test"
    )
    parser.add_argument(
        "--test-uncertainty",
        type=float,
        default=0.9,
        help="A sample uncertainty score to test"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Load randomized indices
        randomized_indices = load_counterfactual_indices(args.counterfactual_path)

        # Test 1: Frame in randomized set (should force skip)
        test_frame_in = list(randomized_indices)[0] if randomized_indices else args.test_frame
        skip_in, reason_in = apply_precedence_rule(
            frame_id=test_frame_in,
            uncertainty=0.1, # Low uncertainty, normally would NOT skip
            randomized_indices=randomized_indices
        )
        print(f"\nTest 1 (Randomized Frame {test_frame_in}):")
        print(f"  Uncertainty: 0.1 (Low)")
        print(f"  Skip Decision: {skip_in}")
        print(f"  Reason: {reason_in}")
        assert skip_in is True, "Randomized frames must always be skipped"
        assert "Precedence Rule" in reason_in

        # Test 2: Frame NOT in randomized set, high uncertainty (should skip deterministically)
        skip_out_high, reason_out_high = apply_precedence_rule(
            frame_id=args.test_frame,
            uncertainty=0.95,
            randomized_indices=randomized_indices
        )
        print(f"\nTest 2 (Non-Randomized Frame {args.test_frame}, High Uncertainty):")
        print(f"  Uncertainty: 0.95")
        print(f"  Skip Decision: {skip_out_high}")
        print(f"  Reason: {reason_out_high}")
        assert skip_out_high is True

        # Test 3: Frame NOT in randomized set, low uncertainty (should NOT skip)
        skip_out_low, reason_out_low = apply_precedence_rule(
            frame_id=args.test_frame,
            uncertainty=0.2,
            randomized_indices=randomized_indices
        )
        print(f"\nTest 3 (Non-Randomized Frame {args.test_frame}, Low Uncertainty):")
        print(f"  Uncertainty: 0.2")
        print(f"  Skip Decision: {skip_out_low}")
        print(f"  Reason: {reason_out_low}")
        assert skip_out_low is False

        print("\n[SUCCESS] All precedence rule tests passed.")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("Please ensure T047 (generate_counterfactual_indices) has run successfully.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during precedence rule test")
        sys.exit(1)

if __name__ == "__main__":
    main()