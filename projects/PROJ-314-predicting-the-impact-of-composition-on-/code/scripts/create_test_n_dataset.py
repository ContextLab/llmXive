"""
Script to generate the test dataset for T017c.
Creates data/raw/test_n.csv with exactly 29 rows where sample_count < 30.
This is used to verify T017b halts when total row count < 30.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import initialize_config, get_project_config
from logger import setup_citation_logger

# Setup logging
logger = setup_citation_logger("test_dataset")
logger.setLevel(logging.INFO)

def create_test_n_dataset(output_path: str, row_count: int = 29):
    """
    Generate a synthetic test dataset with exactly `row_count` rows.
    All rows have sample_count < 30 to trigger the data gap protocol.
    
    Note: This is a SETUP task artifact, not a data loader for the main pipeline.
    It is strictly for testing the logic of T017b.
    """
    if row_count >= 30:
        raise ValueError(f"Test dataset must have < 30 rows, got {row_count}")

    logger.info(f"Generating test dataset with {row_count} rows...")

    # Define a base composition and vary it slightly to create distinct rows
    base_compositions = [
        "Al2O3", "ZrO2", "SiO2", "TiO2", "MgO", "CaO", "BaO", "SrO", "Y2O3",
        "La2O3", "CeO2", "HfO2", "Ta2O5", "Nb2O5", "SnO2", "In2O3", "Gd2O3",
        "Sm2O3", "Eu2O3", "Dy2O3", "Ho2O3", "Er2O3", "Tm2O3", "Yb2O3",
        "Lu2O3", "Sc2O3", "Bi2O3", "PbO", "ZnO"
    ]

    data = []
    for i in range(row_count):
        # Cycle through compositions if row_count > len(base_compositions)
        comp = base_compositions[i % len(base_compositions)]
        if i >= len(base_compositions):
            comp = f"{comp}_v{i}"

        # Ensure sample_count is strictly < 30
        # Use a deterministic pattern: 5 + (i % 24) ensures range [5, 28]
        sample_count = 5 + (i % 24)
        
        # Generate a plausible weibull_modulus (random but seeded for reproducibility)
        # Using a simple deterministic formula based on index to avoid random seed dependency
        weibull = 5.0 + (i * 0.5) % 15.0 
        
        # Sintering temperature (random-ish but deterministic)
        sintering_temp = 1000 + (i * 17) % 1200

        data.append({
            "composition": comp,
            "weibull_modulus": round(weibull, 2),
            "sample_count": sample_count,
            "sintering_temp": sintering_temp,
            "primary_anion_cation_group": "O-Metal", # Simplified for test data
            "mean_atomic_radius": 1.4,
            "electronegativity_std": 0.8,
            "valence_electron_concentration": 2.0,
            "is_range_flag": False,
            "range_original": None,
            "is_imputed": False
        })

    df = pd.DataFrame(data)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully created test dataset at {output_path}")
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Sample count range: {df['sample_count'].min()} - {df['sample_count'].max()}")

    return df

def main():
    """Main entry point for the script."""
    # Initialize config to ensure paths are set
    config = initialize_config()
    project_root = config.get("project_root", Path(__file__).parent.parent.parent)
    
    # Define output path relative to project root
    output_path = Path(project_root) / "data" / "raw" / "test_n.csv"
    
    try:
        create_test_n_dataset(str(output_path), row_count=29)
        print(f"Test dataset created successfully at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to create test dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
