"""
Script to generate a bar chart of the top 20 SNPs and metabolites from top_features.csv.
This script is designed for manual visual inspection of biomarker importance.
"""
import os
import sys
import logging
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assuming this script is run from the project root or scripts/ directory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_artifacts_path, get_reports_path
from utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

def load_top_features():
    """
    Load the top features from the biomarker report.
    Expects 'top_features.csv' in the reports directory.
    """
    reports_path = get_reports_path()
    input_file = reports_path / "top_features.csv"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    # Ensure required columns exist
    required_cols = ['feature_id', 'effect_size', 'modality']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_file}: {missing_cols}")

    return df

def plot_top_features(df, output_path, top_n=20):
    """
    Generate a bar chart of the top N features by effect size, separated by modality.
    """
    # Sort by absolute effect size to get the most impactful features
    # Assuming effect_size can be negative, we sort by absolute value for "top" importance
    df_sorted = df.sort_values(by='effect_size', key=abs, ascending=False).head(top_n)

    # Separate by modality
    snps = df_sorted[df_sorted['modality'] == 'SNP']
    metabolites = df_sorted[df_sorted['modality'] == 'Metabolite']

    fig, axs = plt.subplots(1, 2, figsize=(14, 7))

    # Plot SNPs
    if not snps.empty:
        axs[0].barh(snps['feature_id'], snps['effect_size'], color='steelblue')
        axs[0].set_title(f'Top {len(snps)} SNPs by Effect Size')
        axs[0].set_xlabel('Effect Size')
        axs[0].set_ylabel('Feature ID')
        axs[0].invert_yaxis() # Highest effect at top
    else:
        axs[0].text(0.5, 0.5, 'No SNPs found', transform=axs[0].transAxes, ha='center')
        axs[0].set_title('Top SNPs')

    # Plot Metabolites
    if not metabolites.empty:
        axs[1].barh(metabolites['feature_id'], metabolites['effect_size'], color='coral')
        axs[1].set_title(f'Top {len(metabolites)} Metabolites by Effect Size')
        axs[1].set_xlabel('Effect Size')
        axs[1].set_ylabel('Feature ID')
        axs[1].invert_yaxis()
    else:
        axs[1].text(0.5, 0.5, 'No Metabolites found', transform=axs[1].transAxes, ha='center')
        axs[1].set_title('Top Metabolites')

    plt.suptitle('Top 20 Biomarkers by Effect Size', fontsize=16)
    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    logger.info(f"Figure saved to {output_path}")
    plt.close()

def main():
    """
    Main entry point for the visual inspection script.
    """
    try:
        # Load data
        df = load_top_features()

        # Define output path
        figures_path = get_artifacts_path() / "figures"
        output_file = figures_path / "top_20_feature_importance.png"

        # Generate plot
        plot_top_features(df, output_file, top_n=20)

        logger.info("Visual inspection plot generated successfully.")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())