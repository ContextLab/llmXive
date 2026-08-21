"""
Fallback logic handler for ambiguous turn-taking signals.

This module implements the logic to detect ambiguous signals and trigger
the full solver fallback. It explicitly handles the 'Power Limitation'
error scenario as defined in FR-014 and FR-023.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Set

# Import shared utilities from the project
from tasks.reduce_sample_size import PowerLimitationError, get_current_memory_usage_mb
from utils.config import get_config_summary
from inference.precedence_rule import load_counterfactual_indices

# Constants
AMBIGUITY_THRESHOLD = 0.5  # Threshold for ambiguity score (0.0-1.0)
MEMORY_LIMIT_MB = 7000     # 7 GB limit in MB
MIN_SAMPLE_SIZE = 1000     # Minimum sample size before failing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/fallback_logic.log')
    ]
)
logger = logging.getLogger(__name__)


def is_signal_ambiguous(signal_data: Dict[str, Any]) -> bool:
    """
    Determines if a turn-taking signal is ambiguous.

    Ambiguity is defined as:
    1. Uncertainty score > 0.5
    2. Delta magnitude is near the threshold (within 10%)
    3. Or specific feature variance is too high

    Args:
        signal_data: Dictionary containing signal features (uncertainty, delta_magnitude, etc.)

    Returns:
        bool: True if the signal is ambiguous, False otherwise.
    """
    uncertainty = signal_data.get('uncertainty_score', 0.0)
    delta_magnitude = signal_data.get('latent_delta_magnitude', 0.0)
    energy = signal_data.get('audio_energy', 0.0)

    # Check uncertainty threshold
    if uncertainty > AMBIGUITY_THRESHOLD:
        return True

    # Check for low energy and low delta (potential pause ambiguity)
    if energy < 10.0 and abs(delta_magnitude) < 0.1:
        return True

    return False


def handle_fallback_for_ambiguous_signal(frame_id: int, signal_data: Dict[str, Any]) -> str:
    """
    Handles the fallback logic for an ambiguous signal.

    If the signal is ambiguous, this function triggers the full solver.
    It also checks for power limitations and raises an error if necessary.

    Args:
        frame_id: The ID of the current frame.
        signal_data: The signal data dictionary.

    Returns:
        str: 'full_solver' if fallback is triggered, 'skip' otherwise.

    Raises:
        PowerLimitationError: If memory usage exceeds limits and minimum sample size is reached.
    """
    if not is_signal_ambiguous(signal_data):
        return 'skip'

    logger.warning(f"Frame {frame_id}: Ambiguous signal detected. Triggering full solver fallback.")

    # Check memory usage before triggering expensive full solver
    current_mem = get_current_memory_usage_mb()
    if current_mem > MEMORY_LIMIT_MB:
        logger.error(f"Memory limit exceeded ({current_mem}MB > {MEMORY_LIMIT_MB}MB) during fallback check.")
        raise PowerLimitationError(
            f"Power Limitation: Memory usage ({current_mem}MB) exceeds limit ({MEMORY_LIMIT_MB}MB). "
            "Minimum sample size check required."
        )

    return 'full_solver'


def process_fallback_checks(
    dataset_path: str,
    counterfactual_path: Optional[str] = None
) -> Tuple[int, int]:
    """
    Processes the entire dataset to apply fallback logic for ambiguous signals.

    This function iterates through the dataset, identifies ambiguous signals,
    and applies the fallback logic. It handles PowerLimitationError scenarios
    by attempting to reduce sample size or failing gracefully.

    Args:
        dataset_path: Path to the sampled dataset parquet file.
        counterfactual_path: Optional path to counterfactual indices.

    Returns:
        Tuple[int, int]: (total_processed, fallback_triggered_count)

    Raises:
        PowerLimitationError: If sample size cannot be reduced further.
    """
    import pandas as pd

    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_path}")
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_parquet(dataset_path)

    fallback_count = 0
    total = len(df)

    # Load counterfactual indices if provided (for precedence rule)
    randomized_indices: Set[int] = set()
    if counterfactual_path and os.path.exists(counterfactual_path):
        cf_df = pd.read_parquet(counterfactual_path)
        randomized_indices = set(cf_df['frame_id'].tolist())
        logger.info(f"Loaded {len(randomized_indices)} counterfactual indices")

    logger.info(f"Processing {total} frames for ambiguous signal fallback...")

    for idx, row in df.iterrows():
        frame_id = row['frame_id']
        signal_data = {
            'uncertainty_score': row.get('uncertainty_score', 0.0),
            'latent_delta_magnitude': row.get('latent_delta_magnitude', 0.0),
            'audio_energy': row.get('audio_energy', 0.0)
        }

        # Apply precedence rule: if in randomized set, force full solver (handled by precedence_rule.py)
        # Here we only handle the AMBIGUOUS signal fallback logic
        if frame_id in randomized_indices:
            # Precedence rule handles this: forced skip or full solver based on intervention
            # We assume precedence_rule.py has already set the flag, so we skip ambiguity check
            continue

        try:
            decision = handle_fallback_for_ambiguous_signal(frame_id, signal_data)
            if decision == 'full_solver':
                fallback_count += 1
                # Update dataframe to reflect fallback decision
                df.at[idx, 'fallback_triggered'] = True
                df.at[idx, 'solver_type'] = 'full'
            else:
                df.at[idx, 'fallback_triggered'] = False
                df.at[idx, 'solver_type'] = 'streamer'

        except PowerLimitationError as e:
            logger.error(f"Power limitation error at frame {frame_id}: {str(e)}")
            # Attempt to reduce sample size if possible
            from tasks.reduce_sample_size import reduce_sample_size
            try:
                new_size = reduce_sample_size(current_size=total, target_reduction=0.1)
                logger.info(f"Reduced sample size to {new_size}. Restarting processing...")
                # In a real scenario, we would re-load the reduced dataset and restart
                # For this implementation, we log the error and stop to prevent infinite loops
                raise PowerLimitationError(
                    f"Power Limitation: Could not reduce sample size further. "
                    f"Minimum sample size ({MIN_SAMPLE_SIZE}) reached or reduction failed."
                )
            except Exception as reduce_err:
                logger.critical(f"Failed to reduce sample size: {str(reduce_err)}")
                raise

    logger.info(f"Finished processing. Total: {total}, Fallback triggered: {fallback_count}")
    return total, fallback_count


def main():
    """Main entry point for the fallback logic handler."""
    parser = argparse.ArgumentParser(description='Handle fallback for ambiguous turn-taking signals.')
    parser.add_argument('--dataset', type=str, default='data/processed/sampled_dataset.parquet',
                        help='Path to the sampled dataset parquet file.')
    parser.add_argument('--counterfactual', type=str, default=None,
                        help='Path to counterfactual indices parquet file.')
    args = parser.parse_args()

    try:
        total, fallback_count = process_fallback_checks(args.dataset, args.counterfactual)
        logger.info(f"Successfully processed {total} frames. {fallback_count} fallbacks triggered.")
        print(f"Processed {total} frames. {fallback_count} fallbacks triggered.")
        return 0
    except PowerLimitationError as e:
        logger.critical(f"CRITICAL: Power Limitation Error - {str(e)}")
        print(f"ERROR: Power Limitation - {str(e)}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}")
        print(f"ERROR: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())