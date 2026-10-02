import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path for imports if running as script
if "code" not in sys.path:
    code_dir = Path(__file__).resolve().parent
    project_root = code_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from logging_config import get_logger

logger = get_logger(__name__)

def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load CBNRM proxy metadata."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    with open(metadata_path, 'r') as f:
        return json.load(f)

def load_validation_results(validation_path: Path) -> Dict[str, Any]:
    """Load proxy validation results (excluded countries)."""
    if not validation_path.exists():
        # If file doesn't exist, assume no exclusions yet (for T009b run first)
        return {"excluded_countries": [], "reasons": {}}
    with open(validation_path, 'r') as f:
        return json.load(f)

def classify_regime(proxy_value: float, threshold: float) -> int:
    """
    Derive binary regime_type.
    If proxy_value > threshold, regime_type = 1 (CBNRM), else 0 (State-led).
    """
    if pd.isna(proxy_value):
        return None
    return 1 if proxy_value > threshold else 0

def apply_classification(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Apply classification logic to a dataframe."""
    df = df.copy()
    df['regime_type'] = df['proxy_value'].apply(lambda x: classify_regime(x, threshold))
    return df

def validate_proxy_variance(df: pd.DataFrame, min_variance_threshold: float = 0.0) -> Dict[str, Any]:
    """
    Step 1 of T009b: Check variance of the fetched CBNRM proxy.
    If a country has zero variance (constant value) over time, exclude it.
    Returns a dict with excluded countries and reasons.
    """
    if 'country_code' not in df.columns or 'proxy_value' not in df.columns:
        raise ValueError("DataFrame must contain 'country_code' and 'proxy_value' columns.")

    excluded_countries = []
    reasons = {}

    # Group by country
    grouped = df.groupby('country_code')

    for country, group in grouped:
        # Remove NaN values for variance calculation
        valid_values = group['proxy_value'].dropna()
        
        if len(valid_values) < 2:
            # Not enough data points to calculate variance
            excluded_countries.append(country)
            reasons[country] = "Insufficient data points (< 2) to calculate variance"
            continue

        variance = valid_values.var()
        
        if variance == 0.0 or variance < min_variance_threshold:
            excluded_countries.append(country)
            reasons[country] = f"Zero variance (constant value: {valid_values.iloc[0]})"

    return {
        "excluded_countries": excluded_countries,
        "reasons": reasons,
        "total_countries_checked": len(grouped),
        "total_excluded": len(excluded_countries)
    }

def save_validation_results(validation_results: Dict[str, Any], output_path: Path):
    """Save validation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"Saved validation results to {output_path}")

def main():
    """
    Main execution for T009b: Validate Proxy.
    This script validates the CBNRM proxy data fetched by T009.
    It checks for zero-variance countries, excludes them, logs the exclusions,
    and saves the results to data/processed/proxy_validation.json.
    """
    config_path = Path("code/config.py")
    # Fallback paths if config not loaded dynamically
    raw_data_path = Path("data/raw/cbnrm_proxy.csv")
    processed_dir = Path("data/processed")
    validation_output_path = processed_dir / "proxy_validation.json"

    logger.info("Starting T009b: Validate Proxy Variance")

    if not raw_data_path.exists():
        logger.warning(f"Raw data file not found: {raw_data_path}. Run T009 first.")
        # Produce empty list as per spec: "If the file is missing or empty, log a warning and produce an empty list"
        save_validation_results({"excluded_countries": [], "reasons": {}, "total_countries_checked": 0, "total_excluded": 0}, validation_output_path)
        return

    # Load data
    try:
        df = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {len(df)} rows from {raw_data_path}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)

    if df.empty:
        logger.warning(f"Raw data file {raw_data_path} is empty.")
        save_validation_results({"excluded_countries": [], "reasons": {}, "total_countries_checked": 0, "total_excluded": 0}, validation_output_path)
        return

    # Validate variance
    try:
        validation_results = validate_proxy_variance(df)
    except ValueError as e:
        logger.error(f"Validation failed due to missing columns: {e}")
        sys.exit(1)

    # Log exclusions
    if validation_results['excluded_countries']:
        logger.warning(f"Excluding {validation_results['total_excluded']} countries due to zero variance.")
        for country, reason in validation_results['reasons'].items():
            logger.warning(f"  - {country}: {reason}")
    else:
        logger.info("No countries excluded based on variance.")

    # Save results
    save_validation_results(validation_results, validation_output_path)

    logger.info("T009b completed successfully.")

if __name__ == "__main__":
    main()