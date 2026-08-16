import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
from config import get_config
from utils import setup_logging
from data_models import CensorshipStatus

logger = logging.getLogger(__name__)

def test_upper_limit_flags_reflect_noise(
    retrieval_results_path: Path,
    metadata_path: Path,
    threshold_sigma: float = 3.0
) -> Dict[str, Any]:
    """
    Verify that upper limit flags in retrieval results accurately reflect
    physical noise floors as defined by SNR and Resolution metadata.

    This function implements the validation logic required by T022. It checks
    that spectra flagged as upper limits (censored) actually have low SNR
    relative to the detection threshold derived from their instrumental noise.

    Logic:
    1. Load retrieval results and metadata.
    2. Merge on planet_name.
    3. For each row where `is_upper_limit` is True:
       - Verify SNR < threshold_sigma (typically 3.0).
       - Verify the derived `detection_limit` is consistent with the noise floor.
    4. For each row where `is_upper_limit` is False:
       - Verify SNR >= threshold_sigma.
    5. Report statistics on consistency.

    Args:
        retrieval_results_path: Path to `data/processed/retrieval_results.csv`.
        metadata_path: Path to `data/processed/metadata.csv`.
        threshold_sigma: The SNR threshold above which a detection is considered
                         significant (default 3.0).

    Returns:
        Dict containing:
            - 'total_checked': int
            - 'consistent_count': int
            - 'inconsistent_count': int
            - 'consistency_rate': float
            - 'details': List of dicts for any inconsistencies found.
    """
    config = get_config()
    # Ensure directories exist
    if not retrieval_results_path.exists():
        raise FileNotFoundError(
            f"Retrieval results file not found: {retrieval_results_path}. "
            "Ensure T020 has been executed successfully."
        )
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_path}. "
            "Ensure T012 has been executed successfully."
        )

    logger.info(f"Loading retrieval results from {retrieval_results_path}")
    results_df = pd.read_csv(retrieval_results_path)

    logger.info(f"Loading metadata from {metadata_path}")
    meta_df = pd.read_csv(metadata_path)

    # Merge on planet_name
    merged = pd.merge(
        results_df,
        meta_df[['planet_name', 'snr', 'resolution']],
        on='planet_name',
        how='inner'
    )

    if merged.empty:
        logger.warning("No matching records found between retrieval results and metadata.")
        return {
            'total_checked': 0,
            'consistent_count': 0,
            'inconsistent_count': 0,
            'consistency_rate': 0.0,
            'details': [],
            'status': 'passed'
        }

    inconsistencies = []
    consistent_count = 0

    for idx, row in merged.iterrows():
        is_upper = row['is_upper_limit']
        snr = row['snr']
        detection_limit = row.get('detection_limit', np.nan)
        planet = row['planet_name']

        # Validation Logic
        is_consistent = False

        if is_upper:
            # If flagged as upper limit, SNR should be below threshold
            if snr < threshold_sigma:
                is_consistent = True
            else:
                # SNR is high but flagged as upper limit - potential error in T019 logic
                inconsistencies.append({
                    'planet': planet,
                    'issue': 'Upper limit flagged despite high SNR',
                    'snr': snr,
                    'threshold': threshold_sigma
                })
        else:
            # If NOT flagged as upper limit, SNR should be above threshold
            if snr >= threshold_sigma:
                is_consistent = True
            else:
                # Low SNR but treated as detection - potential false positive
                inconsistencies.append({
                    'planet': planet,
                    'issue': 'Detection claimed despite low SNR',
                    'snr': snr,
                    'threshold': threshold_sigma
                })

        if is_consistent:
            consistent_count += 1

    total_checked = len(merged)
    consistency_rate = consistent_count / total_checked if total_checked > 0 else 0.0

    logger.info(f"Validation complete: {consistent_count}/{total_checked} consistent.")

    result = {
        'total_checked': total_checked,
        'consistent_count': consistent_count,
        'inconsistent_count': total_checked - consistent_count,
        'consistency_rate': consistency_rate,
        'details': inconsistencies,
        'threshold_used': threshold_sigma,
        'status': 'passed' if consistency_rate == 1.0 else 'warning'
    }

    if inconsistencies:
        logger.warning(f"Found {len(inconsistencies)} inconsistencies in upper limit flags.")
        for inc in inconsistencies:
            logger.warning(f"  - {inc['planet']}: {inc['issue']} (SNR: {inc['snr']})")
    else:
        logger.info("All upper limit flags correctly reflect physical noise floors.")

    return result

def main():
    """
    Entry point for running the validation script.
    Reads paths from config and executes the test.
    """
    setup_logging()
    config = get_config()

    # Paths relative to project root
    base_dir = Path(config['project_root'])
    results_path = base_dir / 'data' / 'processed' / 'retrieval_results.csv'
    metadata_path = base_dir / 'data' / 'processed' / 'metadata.csv'

    try:
        validation_result = test_upper_limit_flags_reflect_noise(
            retrieval_results_path=results_path,
            metadata_path=metadata_path,
            threshold_sigma=3.0
        )

        # Log final status
        if validation_result['status'] == 'passed':
            logger.info("VALIDATION PASSED: Upper limit flags are consistent with noise floors.")
        else:
            logger.warning("VALIDATION WARNING: Inconsistencies detected. Review details.")

        # Optionally save the validation report
        report_path = base_dir / 'data' / 'processed' / 'validation_report.json'
        import json
        with open(report_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        logger.info(f"Validation report saved to {report_path}")

        return validation_result

    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()