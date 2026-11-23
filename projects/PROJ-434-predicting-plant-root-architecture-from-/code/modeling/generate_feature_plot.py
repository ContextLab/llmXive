"""
Task T025b: Generate feature importance bar chart.

Reads artifacts/feature_importance.csv and generates figures/feature_importance.png.
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure figures directory exists
FIGURES_DIR = Path("figures")
ARTIFACTS_DIR = Path("artifacts")
INPUT_FILE = ARTIFACTS_DIR / "feature_importance.csv"
OUTPUT_FILE = FIGURES_DIR / "feature_importance.png"

def main():
    """Generate the feature importance bar chart."""
    # Ensure directories exist
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check input file exists
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read {INPUT_FILE}: {e}")
        sys.exit(1)

    # Validate columns
    required_cols = {'feature_name', 'importance_score'}
    if not required_cols.issubset(df.columns):
        logger.error(f"Input CSV missing required columns. Found: {df.columns.tolist()}, Required: {required_cols}")
        sys.exit(1)

    # Sort by importance score for better visualization
    df = df.sort_values(by='importance_score', ascending=True)

    # Create plot
    plt.figure(figsize=(10, 6))
    plt.barh(df['feature_name'], df['importance_score'], color='skyblue', edgecolor='navy')
    plt.xlabel('Importance Score')
    plt.ylabel('Feature')
    plt.title('Feature Importance for Root Architecture Prediction')
    plt.gca().invert_yaxis()  # Highest importance at top
    plt.tight_layout()

    # Save plot
    plt.savefig(OUTPUT_FILE, dpi=300)
    plt.close()

    logger.info(f"Successfully generated feature importance plot: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()