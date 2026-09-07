"""
T053: Formalize Statistical Power Reporting

Enhances the power analysis output to include sample size, achieved power,
and a specific warning if the sample size is below the threshold of 300.

Dependencies:
  - T014a (Data Splitting) -> Provides sample size context via config_state or train_set
  - T044 (Power Analysis) -> Provides the base power analysis data (or generates it if missing)

Output:
  - data/processed/power_analysis.json (Updated with warning and sample size)
"""
import os
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
POWER_ANALYSIS_PATH = PROCESSED_DIR / "power_analysis.json"
CONFIG_STATE_PATH = PROCESSED_DIR / "config_state.json"
TRAIN_SET_PATH = PROCESSED_DIR / "train_set.csv"

# Constants
SAMPLE_SIZE_THRESHOLD = 300
WARNING_MESSAGE = "Statistical power marginal; results should be interpreted with caution."
ALPHA = 0.05
TARGET_POWER = 0.80

def ensure_directories():
    """Ensure the processed directory exists."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_existing_power_analysis() -> Dict[str, Any]:
    """
    Load existing power analysis if it exists.
    If T044 hasn't run or failed, we attempt to compute a basic one or return defaults.
    """
    if POWER_ANALYSIS_PATH.exists():
        try:
            with open(POWER_ANALYSIS_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing power_analysis.json: {e}. Starting fresh.")
            return {}
    return {}

def load_sample_size_from_splits() -> int:
    """
    Attempt to determine the sample size (n) from the training set.
    Falls back to config_state if CSV is missing.
    """
    n = 0

    # Priority 1: Count rows in train_set.csv
    if TRAIN_SET_PATH.exists():
        try:
            # Simple line count for CSV (assuming no empty lines at end)
            with open(TRAIN_SET_PATH, 'r') as f:
                # Count non-empty lines
                lines = [line for line in f if line.strip()]
                # Subtract 1 for header
                n = max(0, len(lines) - 1)
            logger.info(f"Derived sample size n={n} from {TRAIN_SET_PATH.name}")
            return n
        except Exception as e:
            logger.warning(f"Failed to count rows in {TRAIN_SET_PATH}: {e}")

    # Priority 2: Check config_state.json for split info
    if CONFIG_STATE_PATH.exists():
        try:
            with open(CONFIG_STATE_PATH, 'r') as f:
                config = json.load(f)
            if 'train_size' in config:
                n = config['train_size']
                logger.info(f"Derived sample size n={n} from {CONFIG_STATE_PATH.name}")
                return n
        except Exception as e:
            logger.warning(f"Failed to read config_state.json: {e}")

    # Fallback: If we can't find the data, we cannot compute power meaningfully.
    # We return 0 to trigger a warning in the logic below.
    logger.error("Could not determine sample size from splits or config.")
    return 0

def calculate_power_effect_size(n: int, alpha: float = 0.05, power: float = 0.80) -> Optional[float]:
    """
    Approximate the detectable effect size (Cohen's d) for a two-sample t-test
    given n, alpha, and target power.
    Uses a simplified approximation: d ≈ 2 * z_{1-alpha/2} / sqrt(n) for large n,
    but for small n, power is low.
    
    A more robust approximation for two-sample t-test (equal variance):
    n_per_group = n / 2
    d = (z_alpha + z_beta) * sqrt(2/n_per_group)
    """
    if n < 2:
        return None

    n_per_group = n / 2
    if n_per_group < 2:
        return None

    # Z-scores
    # z_alpha for two-tailed 0.05 is ~1.96
    # z_beta for 0.80 power is ~0.84
    z_alpha = 1.96
    z_beta = 0.84

    # Approximation: d = (z_alpha + z_beta) * sqrt(2 / n_per_group)
    d = (z_alpha + z_beta) * math.sqrt(2 / n_per_group)
    return d

def main():
    logger.info("Starting T053: Formalize Statistical Power Reporting")
    ensure_directories()

    # 1. Load or initialize power analysis data
    power_data = load_existing_power_analysis()

    # 2. Determine sample size
    n = load_sample_size_from_splits()
    
    # 3. Update/Compute metrics
    power_data['sample_size'] = n
    
    # If we have a sample size, calculate the detectable effect size
    if n > 0:
        effect_size = calculate_power_effect_size(n)
        if effect_size:
            power_data['detectable_effect_size_cohen_d'] = round(effect_size, 4)
        else:
            power_data['detectable_effect_size_cohen_d'] = None
    else:
        power_data['detectable_effect_size_cohen_d'] = None

    # 4. Apply the warning logic
    if n < SAMPLE_SIZE_THRESHOLD:
        power_data['warning'] = WARNING_MESSAGE
        power_data['marginal_power'] = True
        logger.warning(f"Sample size n={n} is below threshold {SAMPLE_SIZE_THRESHOLD}. Warning added.")
    else:
        power_data['warning'] = None
        power_data['marginal_power'] = False
        logger.info(f"Sample size n={n} meets threshold {SAMPLE_SIZE_THRESHOLD}.")

    # 5. Write the output
    try:
        with open(POWER_ANALYSIS_PATH, 'w') as f:
            json.dump(power_data, f, indent=2)
        logger.info(f"Successfully updated {POWER_ANALYSIS_PATH}")
    except IOError as e:
        logger.error(f"Failed to write {POWER_ANALYSIS_PATH}: {e}")
        raise

if __name__ == "__main__":
    main()