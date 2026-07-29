"""
Main entry point for the descriptor engineering pipeline.
Orchestrates the CLR transform and descriptor computation.
"""
import os
import sys
import logging
from pathlib import Path

from seed import init_reproducibility
from features.descriptor_engine import DescriptorEngine
from features.transformer import CLRTransformer
from features.collinearity import calculate_vif, get_collinear_features, remove_collinear_features
from utils.logging_config import get_logger
from config import get_data_processed_dir, get_data_outputs_dir, get_vif_threshold

logger = get_logger(__name__)


def main():
    """
    Runs the full descriptor engineering and collinearity check.
    """
    init_reproducibility()

    processed_dir = get_data_processed_dir()
    output_dir = get_data_outputs_dir()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = processed_dir / "solder_hardness_validated.csv"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Run ingestion pipeline first.")
        sys.exit(1)

    logger.info(f"Loading validated data from {input_file}")
    import pandas as pd
    df = pd.read_csv(input_file)

    # Identify composition columns
    # Assuming columns are element symbols (Sn, Pb, Ag, etc.)
    # We'll filter based on a list of known elements
    known_elements = ["Sn", "Pb", "Ag", "Cu", "Bi", "In", "Zn", "Sb", "Au", "Ni", "Fe", "Co", "Mn", "Al", "Mg", "Ca"]
    composition_cols = [c for c in df.columns if c in known_elements]

    if not composition_cols:
        logger.error("No composition columns found in the dataset.")
        sys.exit(1)

    logger.info(f"Detected composition columns: {composition_cols}")

    # Step 1: Compute Descriptors
    logger.info("Step 1: Computing descriptors...")
    engine = DescriptorEngine()
    df_with_descriptors = engine.compute_descriptors(df, composition_cols)

    # Step 2: Save intermediate result
    intermediate_file = output_dir / "solder_hardness_with_descriptors.csv"
    df_with_descriptors.to_csv(intermediate_file, index=False)
    logger.info(f"Saved descriptors to {intermediate_file}")

    # Step 3: Collinearity Check
    logger.info("Step 2: Checking for collinearity...")
    descriptor_cols = [c for c in df_with_descriptors.columns if c in engine.compute_descriptors(df.head(1), composition_cols).columns]
    # Filter out non-descriptor columns if any got mixed in
    descriptor_cols = [c for c in descriptor_cols if c not in composition_cols and c not in ['hardness', 'alloy_id', 'source']]

    if len(descriptor_cols) > 1:
        vif_scores = calculate_vif(df_with_descriptors, descriptor_cols)
        threshold = get_vif_threshold()

        logger.info("VIF Analysis Results:")
        collinear = []
        for feat, score in vif_scores.items():
            flag = " [COLLINEAR]" if score >= threshold else ""
            logger.info(f"  {feat}: {score:.4f}{flag}")
            if score >= threshold:
                collinear.append(feat)

        if collinear:
            logger.warning(f"Collinear features detected: {collinear}")
            df_clean = remove_collinear_features(df_with_descriptors, vif_scores, threshold)
            clean_file = output_dir / "solder_hardness_clean_features.csv"
            df_clean.to_csv(clean_file, index=False)
            logger.info(f"Saved cleaned features to {clean_file}")
        else:
            logger.info("No collinear features detected.")
            # Copy as clean
            df_with_descriptors.to_csv(output_dir / "solder_hardness_clean_features.csv", index=False)
    else:
        logger.info("Not enough descriptors for VIF analysis.")
        df_with_descriptors.to_csv(output_dir / "solder_hardness_clean_features.csv", index=False)

    logger.info("Descriptor engineering pipeline completed.")


if __name__ == "__main__":
    main()