import os
import logging
from pathlib import Path
import pandas as pd
from pymatgen.core import Composition
from matminer.datasets import load_dataset
from config import RAW_DATA_DIR
from utils.logging import setup_logger

# Setup logger
logger = setup_logger(__name__)

def is_li_rich(composition_str: str, li_threshold: float = 0.3) -> bool:
    """
    Check if a composition is Li-rich.

    Args:
        composition_str: Composition string (e.g., "Li2O")
        li_threshold: Minimum Li fraction to be considered Li-rich

    Returns:
        True if Li-rich, False otherwise
    """
    try:
        comp = Composition(composition_str)
        li_fraction = comp.get_el_amt_dict().get('Li', 0) / sum(comp.get_el_amt_dict().values())
        return li_fraction >= li_threshold
    except Exception as e:
        logger.warning(f"Failed to parse composition {composition_str}: {e}")
        return False

def is_rocksalt(composition_str: str) -> bool:
    """
    Check if a composition is likely to form a rock-salt structure.

    Args:
        composition_str: Composition string

    Returns:
        True if likely rock-salt, False otherwise
    """
    try:
        comp = Composition(composition_str)
        elements = list(comp.elements)

        # Rock-salt typically has 2 elements with 1:1 ratio
        if len(elements) != 2:
            return False

        amounts = [comp.get_el_amt_dict()[str(el)] for el in elements]
        ratio = min(amounts) / max(amounts)

        return 0.9 <= ratio <= 1.1
    except Exception as e:
        logger.warning(f"Failed to check rock-salt for {composition_str}: {e}")
        return False

def main():
    """
    Download and filter OQMD data for Li-rich rock-salt structures.
    """
    logger.info("Starting data download and filtering...")

    try:
        # Load OQMD dataset (using a subset for demonstration)
        # In production, download the full dataset
        logger.info("Loading OQMD dataset...")
        df = load_dataset("oqmd_entries", shuffle=False)

        # Filter for Li-rich compositions
        logger.info("Filtering for Li-rich compositions...")
        df['is_li_rich'] = df['composition'].apply(is_li_rich)
        df_li_rich = df[df['is_li_rich']].copy()

        # Filter for rock-salt structures
        logger.info("Filtering for rock-salt structures...")
        df_li_rich['is_rocksalt'] = df_li_rich['composition'].apply(is_rocksalt)
        df_filtered = df_li_rich[df_li_rich['is_rocksalt']].copy()

        # Log sample count
        sample_count = len(df_filtered)
        logger.info(f"Filtered dataset contains {sample_count} entries")

        if sample_count < 100:
            logger.warning(f"Sample count ({sample_count}) is below threshold of 100. Proceeding with available data.")

        # Save to raw data directory
        output_path = RAW_DATA_DIR / "oqmd_filtered.csv"
        df_filtered.to_csv(output_path, index=False)
        logger.info(f"Saved filtered data to {output_path}")

        return df_filtered

    except Exception as e:
        logger.error(f"Failed to download or filter data: {e}")
        raise

if __name__ == "__main__":
    main()
