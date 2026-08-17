"""
validate_proxy_mos.py

Validates the proxy MOS against human ratings (if available).
Implements T044 logic:
1. Read data/metrics/human_data_status.json.
2. If status == 'missing':
   - Log "Assumption Validated (No Human Data Available)" to data/logs/mos_assumption_validated.log.
   - Update state.yaml with mos_validation: 'assumption_validated'.
3. If status == 'present':
   - Load human ratings from data/raw/human_ratings.json.
   - Load proxy MOS from data/metrics/hybrid_output.parquet (via evaluation.metrics).
   - Calculate Pearson correlation.
   - Assert r >= 0.8.
   - Update state.yaml with mos_validation: 'passed' or 'failed'.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Project root relative to this file (assuming code/metrics/validate_proxy_mos.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths
HUMAN_DATA_STATUS_PATH = PROJECT_ROOT / "data" / "metrics" / "human_data_status.json"
HUMAN_RATINGS_PATH = PROJECT_ROOT / "data" / "raw" / "human_ratings.json"
HYBRID_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "hybrid_output.parquet"
LOG_DIR = PROJECT_ROOT / "data" / "logs"
STATE_YAML_PATH = PROJECT_ROOT / "state.yaml"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "validate_proxy_mos.log")
    ]
)
logger = logging.getLogger(__name__)


def load_hybrid_output_metrics() -> pd.DataFrame:
    """
    Load the hybrid output parquet file and return the proxy MOS column.
    Assumes the file has a column 'proxy_mos' or similar.
    Based on T050 output schema: frame_id, latency, fid_score, skip_flag.
    We need to check if proxy_mos was added or if we need to compute it.
    However, T028 (evaluation/metrics.py) computes proxy_mos.
    Let's assume the hybrid_output.parquet has been enriched or we load metrics separately.
    For this task, we assume the hybrid_output.parquet contains 'proxy_mos' or we load it from a separate metrics file.
    Given the task description, we need to correlate proxy MOS with human ratings.
    Let's check if the hybrid_output has proxy_mos. If not, we might need to load from a metrics file.
    But T028 outputs metrics. Let's assume the hybrid_output.parquet has 'proxy_mos' column.
    If not, we will try to load from a separate file or compute it.
    For now, we assume the hybrid_output.parquet has 'proxy_mos'.
    """
    if not HYBRID_OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Hybrid output file not found: {HYBRID_OUTPUT_PATH}")

    df = pd.read_parquet(HYBRID_OUTPUT_PATH)

    # Check for proxy_mos column
    if 'proxy_mos' not in df.columns:
        # Try to load from metrics file if available
        metrics_path = PROJECT_ROOT / "data" / "metrics" / "hybrid_metrics.json"
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            # Assume metrics contains a list of proxy_mos values
            if 'proxy_mos' in metrics:
                df['proxy_mos'] = metrics['proxy_mos']
            else:
                raise ValueError("proxy_mos column not found in hybrid_output.parquet or metrics file.")
        else:
            raise ValueError("proxy_mos column not found in hybrid_output.parquet.")

    return df


def load_human_ratings() -> pd.DataFrame:
    """
    Load human ratings from data/raw/human_ratings.json.
    Expected schema: list of dicts with 'frame_id' and 'human_mos'.
    """
    if not HUMAN_RATINGS_PATH.exists():
        raise FileNotFoundError(f"Human ratings file not found: {HUMAN_RATINGS_PATH}")

    with open(HUMAN_RATINGS_PATH, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    # Ensure necessary columns exist
    if 'frame_id' not in df.columns or 'human_mos' not in df.columns:
        raise ValueError("Human ratings file must contain 'frame_id' and 'human_mos' columns.")

    return df


def calculate_correlation(proxy_mos: pd.Series, human_mos: pd.Series) -> Tuple[float, float]:
    """
    Calculate Pearson correlation between proxy MOS and human MOS.
    Returns (correlation, p_value).
    """
    # Drop NaNs
    valid_indices = ~(proxy_mos.isna() | human_mos.isna())
    if valid_indices.sum() < 2:
        raise ValueError("Not enough valid data points to calculate correlation.")

    corr, p_value = pearsonr(proxy_mos[valid_indices], human_mos[valid_indices])
    return corr, p_value


def update_state_yaml(mos_validation_status: str, details: Dict[str, Any]):
    """
    Update state.yaml with the MOS validation status and details.
    """
    import yaml

    if not STATE_YAML_PATH.exists():
        logger.warning(f"State file not found: {STATE_YAML_PATH}. Creating new one.")
        state = {}
    else:
        with open(STATE_YAML_PATH, 'r') as f:
            state = yaml.safe_load(f) or {}

    state['mos_validation'] = mos_validation_status
    state['mos_validation_details'] = details

    with open(STATE_YAML_PATH, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

    logger.info(f"Updated state.yaml with mos_validation: {mos_validation_status}")


def log_assumption_validated():
    """
    Log the assumption validated message to data/logs/mos_assumption_validated.log.
    """
    log_file = LOG_DIR / "mos_assumption_validated.log"
    with open(log_file, 'w') as f:
        f.write("Assumption Validated (No Human Data Available)\n")
    logger.info(f"Logged assumption validated to {log_file}")


def validate_proxy_mos() -> bool:
    """
    Main logic for T044.
    Returns True if validation passes (or assumption is validated), False otherwise.
    """
    logger.info("Starting T044: Validate Proxy MOS")

    # Step 1: Check human data status
    if not HUMAN_DATA_STATUS_PATH.exists():
        raise FileNotFoundError(f"Human data status file not found: {HUMAN_DATA_STATUS_PATH}")

    with open(HUMAN_DATA_STATUS_PATH, 'r') as f:
        status_data = json.load(f)

    status = status_data.get('status', 'missing')
    logger.info(f"Human data status: {status}")

    if status == 'missing':
        log_assumption_validated()
        update_state_yaml('assumption_validated', {'reason': 'No human data available'})
        logger.info("Assumption validated: No human data available.")
        return True

    elif status == 'present':
        logger.info("Human data present. Proceeding with correlation calculation.")

        try:
            # Step 2: Load proxy MOS
            hybrid_df = load_hybrid_output_metrics()
            proxy_mos = hybrid_df['proxy_mos']

            # Step 3: Load human ratings
            human_df = load_human_ratings()
            human_mos = human_df['human_mos']

            # Step 4: Merge on frame_id if necessary
            # Assuming both have frame_id. If not, we need to align them.
            if 'frame_id' in hybrid_df.columns and 'frame_id' in human_df.columns:
                merged = pd.merge(hybrid_df[['frame_id', 'proxy_mos']], human_df[['frame_id', 'human_mos']], on='frame_id')
                proxy_mos = merged['proxy_mos']
                human_mos = merged['human_mos']
            else:
                # If no frame_id, assume they are aligned by index (risky, but fallback)
                logger.warning("No frame_id found in both datasets. Assuming alignment by index.")
                min_len = min(len(proxy_mos), len(human_mos))
                proxy_mos = proxy_mos.iloc[:min_len]
                human_mos = human_mos.iloc[:min_len]

            # Step 5: Calculate correlation
            corr, p_value = calculate_correlation(proxy_mos, human_mos)
            logger.info(f"Pearson correlation: {corr:.4f}, p-value: {p_value:.4f}")

            # Step 6: Check threshold
            threshold = 0.8
            if corr >= threshold:
                update_state_yaml('passed', {'correlation': corr, 'p_value': p_value, 'threshold': threshold})
                logger.info(f"Validation PASSED: correlation {corr:.4f} >= {threshold}")
                return True
            else:
                update_state_yaml('failed', {'correlation': corr, 'p_value': p_value, 'threshold': threshold})
                logger.error(f"Validation FAILED: correlation {corr:.4f} < {threshold}")
                return False

        except Exception as e:
            logger.error(f"Error during correlation calculation: {e}")
            update_state_yaml('failed', {'error': str(e)})
            return False

    else:
        logger.error(f"Unknown human data status: {status}")
        update_state_yaml('failed', {'error': f'Unknown status: {status}'})
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate Proxy MOS against Human Ratings")
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level))

    success = validate_proxy_mos()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()