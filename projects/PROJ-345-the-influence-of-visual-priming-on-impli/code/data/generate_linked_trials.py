"""
Generate linked_trials.csv from preprocessed data with linkage derivation.
Implements T016 and T017: Linkage derivation and metadata percentage calculation.
"""
import os
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import get_path
from data.linkage import derive_stimulus_id_from_trial_id, run_linkage_derivation

logger = logging.getLogger(__name__)


def load_preprocessed_trials(
    input_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load preprocessed trial data.

    Args:
        input_path: Path to preprocessed trials CSV. Defaults to data/processed/preprocessed_trials.csv

    Returns:
        DataFrame with trial data
    """
    if input_path is None:
        input_path = get_path("data", "processed", "preprocessed_trials.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed trials file not found: {input_path}")

    logger.info(f"Loading preprocessed trials from: {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} trials")
    return df


def ensure_linkage(
    df: pd.DataFrame,
    linkage_method: str = "hash_derivation",
    halt_threshold: float = 0.10
) -> pd.DataFrame:
    """
    Ensure all trials have a stimulus_id via linkage derivation.

    Args:
        df: DataFrame with trial data
        linkage_method: Method to use for linkage (currently only 'hash_derivation')
        halt_threshold: If more than this fraction fail linkage, halt execution

    Returns:
        DataFrame with stimulus_id column populated where possible
    """
    logger.info(f"Ensuring linkage for {len(df)} trials using method: {linkage_method}")

    if "stimulus_id" not in df.columns:
        df["stimulus_id"] = None

    # Count existing valid linkages
    existing_valid = df["stimulus_id"].notna() & (df["stimulus_id"] != "")
    existing_count = existing_valid.sum()
    logger.info(f"Trials with existing valid stimulus_id: {existing_count}")

    # Identify trials needing linkage
    needs_linkage = ~existing_valid
    trials_to_link = df[needs_linkage].copy()

    if len(trials_to_link) == 0:
        logger.info("All trials already have valid stimulus_id")
        return df

    logger.info(f"Attempting linkage derivation for {len(trials_to_link)} trials")

    # Apply linkage derivation
    derived_ids = []
    failed_trials = []

    for idx, row in trials_to_link.iterrows():
        trial_id = row.get("trial_id", "")
        try:
            stimulus_id = derive_stimulus_id_from_trial_id(trial_id, method=linkage_method)
            if stimulus_id:
                derived_ids.append(stimulus_id)
            else:
                derived_ids.append(None)
                failed_trials.append(trial_id)
        except Exception as e:
            logger.warning(f"Linkage derivation failed for trial {trial_id}: {e}")
            derived_ids.append(None)
            failed_trials.append(trial_id)

    # Update the dataframe
    df.loc[needs_linkage, "stimulus_id"] = derived_ids

    # Calculate failure rate
    total_trials = len(df)
    final_linked = df["stimulus_id"].notna() & (df["stimulus_id"] != "")
    final_linked_count = final_linked.sum()
    failure_count = total_trials - final_linked_count
    failure_rate = failure_count / total_trials

    logger.info(f"Linkage derivation complete:")
    logger.info(f"  - Total trials: {total_trials}")
    logger.info(f"  - Successfully linked: {final_linked_count}")
    logger.info(f"  - Failed linkage: {failure_count}")
    logger.info(f"  - Failure rate: {failure_rate:.2%}")

    # Check halt threshold
    if failure_rate > halt_threshold:
        error_msg = (
            f"Data Gap: Linkage derivation failed for >{int(halt_threshold*100)}% of trials "
            f"({failure_rate:.2%}). Halting execution per SC-001 requirements."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if failure_rate > 0:
        logger.warning(
            f"Linkage derivation failed for {failure_rate:.2%} of trials. "
            f"Proceeding with warning."
        )

    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and types for linked_trials.csv.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with normalized columns
    """
    required_columns = ["trial_id", "response_time", "stimulus_id", "prime_condition", "participant_id"]

    # Check for required columns
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Select and order columns
    df = df[required_columns].copy()

    # Ensure types
    df["trial_id"] = df["trial_id"].astype(str)
    df["response_time"] = pd.to_numeric(df["response_time"], errors="coerce")
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    df["prime_condition"] = df["prime_condition"].astype(str)
    df["participant_id"] = df["participant_id"].astype(str)

    return df


def write_linked_trials(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Write linked trials to CSV.

    Args:
        df: DataFrame with linked trial data
        output_path: Output path. Defaults to data/processed/linked_trials.csv

    Returns:
        Path to the written file
    """
    if output_path is None:
        output_path = get_path("data", "processed", "linked_trials.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} trials to {output_path}")

    return output_path


def verify_metadata_percentage(
    linked_trials_path: Optional[Path] = None,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Verify that the percentage of trials with linked metadata meets the threshold.

    Args:
        linked_trials_path: Path to linked_trials.csv
        threshold: Minimum required percentage (default 0.95)

    Returns:
        Dictionary with verification results
    """
    if linked_trials_path is None:
        linked_trials_path = get_path("data", "processed", "linked_trials.csv")

    if not linked_trials_path.exists():
        raise FileNotFoundError(f"Linked trials file not found: {linked_trials_path}")

    df = pd.read_csv(linked_trials_path)

    total = len(df)
    linked = df["stimulus_id"].notna() & (df["stimulus_id"] != "")
    linked_count = linked.sum()

    percentage = linked_count / total if total > 0 else 0.0

    result = {
        "total_trials": total,
        "linked_trials": int(linked_count),
        "unlinked_trials": int(total - linked_count),
        "percentage": round(percentage, 4),
        "threshold": threshold,
        "meets_threshold": percentage >= threshold
    }

    logger.info(f"Metadata percentage verification: {percentage:.2%} (threshold: {threshold:.2%})")

    return result


def main():
    """
    Main entry point for generating linked_trials.csv.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting linked trials generation (T016, T017)")

    try:
        # Step 1: Load preprocessed trials
        input_path = get_path("data", "processed", "preprocessed_trials.csv")
        if not input_path.exists():
            # Try to find any preprocessed file
            input_path = get_path("data", "processed")
            csv_files = list(input_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(
                    "No preprocessed trials file found. "
                    "Ensure data ingestion (T013-T015) has been completed."
                )
            input_path = csv_files[0]
            logger.info(f"Using found file: {input_path}")

        df = load_preprocessed_trials(input_path)

        # Step 2: Ensure linkage
        df = ensure_linkage(df, halt_threshold=0.10)

        # Step 3: Normalize columns
        df = normalize_columns(df)

        # Step 4: Write output
        output_path = write_linked_trials(df)

        # Step 5: Verify metadata percentage
        result = verify_metadata_percentage(output_path, threshold=0.95)

        if not result["meets_threshold"]:
            logger.warning(
                f"SC-001 target not met: {result['percentage']:.2%} < {result['threshold']:.2%}. "
                f"Consider reviewing linkage derivation logic."
            )
        else:
            logger.info(
                f"SC-001 target met: {result['percentage']:.2%} >= {result['threshold']:.2%}. "
                f"'Vast majority' of trials have linked metadata."
            )

        logger.info("Linked trials generation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Linked trials generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
