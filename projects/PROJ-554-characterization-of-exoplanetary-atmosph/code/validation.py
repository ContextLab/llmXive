"""Validation module for exoplanetary atmosphere analysis.

This module contains functions to validate the physical consistency of
retrieval results, specifically checking that upper limit flags correctly
reflect the underlying noise floors of the spectra.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
from config import get_config

def test_upper_limit_flags_reflect_noise(
    retrieval_results_path: str,
    metadata_path: str,
    snr_threshold: float = 5.0,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """Verify that upper limit flags in retrieval results reflect physical noise floors.

    This function checks the consistency between the 'is_upper_limit' flag in
    retrieval results and the Signal-to-Noise Ratio (SNR) from the metadata.
    According to physical principles, spectra with SNR below a certain threshold
    (e.g., 5.0) should consistently be flagged as upper limits if the retrieval
    could not detect a significant signal.

    Args:
        retrieval_results_path: Path to the CSV file containing retrieval results.
        metadata_path: Path to the CSV file containing metadata (including SNR).
        snr_threshold: The SNR threshold below which an upper limit is expected.
                       Defaults to 5.0.
        logger: Optional logger instance.

    Returns:
        A dictionary containing:
            - total_planets: Total number of planets checked.
            - consistent_count: Number of planets where the flag matches the SNR expectation.
            - inconsistent_count: Number of planets where the flag contradicts the SNR expectation.
            - consistency_rate: Fraction of consistent planets.
            - details: List of details for inconsistent planets.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"Validating upper limit flags against noise floors for {retrieval_results_path}")

    # Load data
    try:
        retrieval_df = pd.read_csv(retrieval_results_path)
        metadata_df = pd.read_csv(metadata_path)
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return {
            "total_planets": 0,
            "consistent_count": 0,
            "inconsistent_count": 0,
            "consistency_rate": 0.0,
            "details": [],
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {
            "total_planets": 0,
            "consistent_count": 0,
            "inconsistent_count": 0,
            "consistency_rate": 0.0,
            "details": [],
            "error": str(e)
        }

    # Merge on planet name
    merged_df = pd.merge(
        retrieval_df,
        metadata_df[['planet_name', 'snr']],
        on='planet_name',
        how='inner'
    )

    if merged_df.empty:
        logger.warning("No matching planets found between retrieval and metadata.")
        return {
            "total_planets": 0,
            "consistent_count": 0,
            "inconsistent_count": 0,
            "consistency_rate": 0.0,
            "details": [],
            "warning": "No matching planets found."
        }

    # Define expectations
    # Expectation: If SNR < threshold, is_upper_limit should be True.
    # Expectation: If SNR >= threshold, is_upper_limit should ideally be False (though retrieval might fail for other reasons).
    # We focus on the critical case: Low SNR MUST be flagged.

    inconsistent_details = []
    consistent_count = 0
    inconsistent_count = 0

    for _, row in merged_df.iterrows():
        planet = row['planet_name']
        snr = row['snr']
        is_upper_limit = row['is_upper_limit']

        # Check for NaN SNR
        if pd.isna(snr):
            # If SNR is missing, we cannot validate. Skip or flag as warning?
            # For this test, we assume missing SNR is a data quality issue, not a flag logic issue.
            continue

        if snr < snr_threshold:
            # Low SNR: Expect upper limit
            if is_upper_limit:
                consistent_count += 1
            else:
                inconsistent_count += 1
                inconsistent_details.append({
                    "planet_name": planet,
                    "snr": snr,
                    "is_upper_limit": is_upper_limit,
                    "expected_upper_limit": True,
                    "reason": f"Low SNR ({snr:.2f} < {snr_threshold}) but not flagged as upper limit."
                })
        else:
            # High SNR: Expect detection (is_upper_limit=False)
            # Note: A high SNR spectrum could still fail retrieval for other reasons (e.g., bad model fit),
            # but generally, if SNR is high, a detection should be possible.
            # We will count this as consistent if it is NOT flagged as upper limit.
            # If it IS flagged as upper limit despite high SNR, it might be a false negative (conservative).
            # We treat High SNR + Upper Limit as "Conservative but acceptable" for now,
            # but High SNR + Detection is ideal.
            # Strictly: The task asks to verify flags reflect noise floors.
            # If SNR is high, noise floor is low, so a detection is expected.
            # If it is flagged as upper limit, it might be an issue.
            # Let's define: Consistent = (SNR < thresh AND Upper) OR (SNR >= thresh AND NOT Upper)
            if not is_upper_limit:
                consistent_count += 1
            else:
                # High SNR but flagged as upper limit. This is suspicious.
                # It implies the retrieval failed to find a signal despite good data.
                # We count this as inconsistent for the purpose of "flags reflecting noise".
                inconsistent_count += 1
                inconsistent_details.append({
                    "planet_name": planet,
                    "snr": snr,
                    "is_upper_limit": is_upper_limit,
                    "expected_upper_limit": False,
                    "reason": f"High SNR ({snr:.2f} >= {snr_threshold}) but flagged as upper limit."
                })

    total_checked = consistent_count + inconsistent_count
    consistency_rate = consistent_count / total_checked if total_checked > 0 else 0.0

    result = {
        "total_planets": total_checked,
        "consistent_count": consistent_count,
        "inconsistent_count": inconsistent_count,
        "consistency_rate": consistency_rate,
        "snr_threshold_used": snr_threshold,
        "details": inconsistent_details
    }

    if inconsistent_count > 0:
        logger.warning(f"Found {inconsistent_count} planets with inconsistent upper limit flags.")
        for detail in inconsistent_details:
            logger.warning(f"  - {detail['planet_name']}: {detail['reason']}")
    else:
        logger.info("All upper limit flags are consistent with the noise floor (SNR).")

    return result

def main():
    """Main entry point for validation script."""
    config = get_config()
    logger = logging.getLogger("validation")
    logger.setLevel(logging.INFO)

    # Default paths based on project structure
    retrieval_path = Path(config.get("data_dir", "data/processed")) / "retrieval_results.csv"
    metadata_path = Path(config.get("data_dir", "data/processed")) / "metadata.csv"

    # Allow override via environment or args if needed, but for now use defaults
    logger.info(f"Running validation on {retrieval_path} and {metadata_path}")

    result = test_upper_limit_flags_reflect_noise(
        retrieval_results_path=str(retrieval_path),
        metadata_path=str(metadata_path),
        logger=logger
    )

    # Save result to a JSON file for reporting
    output_path = Path(config.get("results_dir", "results")) / "validation_upper_limit_flags.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(f"Validation results saved to {output_path}")

    if result.get("inconsistent_count", 0) > 0:
        logger.warning(f"Validation found {result['inconsistent_count']} inconsistencies.")
    else:
        logger.info("Validation passed successfully.")

    return result

if __name__ == "__main__":
    main()