import logging
import argparse
from pathlib import Path
import pandas as pd

from src.services.vif_checker import run_vif_diagnostic
from src.config.logging_config import setup_logger

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Validate features using VIF diagnostic.")
    parser.add_argument("--input", type=Path, required=True, help="Path to training_sample.parquet")
    parser.add_argument("--threshold", type=float, default=10.0, help="VIF threshold for warning")
    args = parser.parse_args()

    setup_logger("validate_features", log_file=Path("logs/pipeline.log"))

    logger.info(f"Loading data from {args.input}")
    df = pd.read_parquet(args.input)

    logger.info("Running VIF diagnostic...")
    vif_results = run_vif_diagnostic(df)

    # Log results
    for feature, vif in vif_results.items():
        logger.info(f"VIF for {feature}: {vif:.2f}")
        if vif > args.threshold:
            logger.warning(f"High collinearity detected for {feature} (VIF={vif:.2f} > {args.threshold})")

    logger.info("Feature validation complete.")

if __name__ == "__main__":
    main()
