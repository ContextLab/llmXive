"""
Data Download and Filtering Script (T012).
Fetches OQMD data, filters for Li-rich rock-salt structures, and saves to raw data directory.
"""
import os
import logging
from pathlib import Path
import pandas as pd
from pymatgen.core import Composition
from matminer.datasets import load_dataset
from utils.logging import setup_logger
from config import RAW_DATA_DIR, set_seed

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("download_data")
logger.info("Starting data download and filtering (T012).")

set_seed()

def is_li_rich(composition_str: str, threshold: float = 0.3) -> bool:
    """
    Check if a composition is Li-rich.
    Li fraction >= threshold.
    """
    try:
        comp = Composition(composition_str)
        if "Li" not in comp:
            return False
        li_fraction = comp[("Li",)] / sum(comp.values())
        return li_fraction >= threshold
    except Exception:
        return False

def is_rocksalt(composition_str: str) -> bool:
    """
    Heuristic check for rock-salt like stoichiometry.
    Rock-salt (e.g., LiMO2) typically has a 1:1 cation ratio or similar simple ratios.
    For Li-rich, we might look for Li:TransitionMetal ratios > 1.
    This is a simplified check; full structural validation requires the structure object.
    Here we filter by stoichiometry as a proxy if structure is not yet parsed,
    but since we load the full dataset, we can check the structure symmetry if available.
    
    However, for T012, we often filter by composition first.
    Let's assume we are looking for LiMO2 type or similar where Li is dominant.
    A strict rock-salt check requires space group analysis which is expensive on full dataset.
    We will rely on the 'is_stable' or specific metadata if available, or simple stoichiometry.
    
    For this task, we will define 'rock-salt' loosely as having a 1:1 metal ratio or similar
    if we don't have the structure object readily available for symmetry analysis in this step.
    But matminer OQMD dataset usually includes 'space_group_number'.
    Rock salt is Fm-3m (225).
    """
    # This function is a placeholder for specific logic if space group is available.
    # If the dataset has 'space_group_number', we check for 225.
    # If not, we skip strict structural check here and assume composition filter is primary.
    return True  # Placeholder: assume all Li-rich pass this for now if space group not checked

def main():
    """
    Main pipeline:
    1. Load OQMD dataset (subset for speed if needed, but we need Li-rich).
    2. Filter for Li-rich compositions.
    3. Filter for rock-salt (if metadata available).
    4. Save to data/raw/oqmd_filtered.csv
    """
    output_file = RAW_DATA_DIR / "oqmd_filtered.csv"
    
    # Check if already exists
    if output_file.exists():
        logger.warning(f"Filtered data already exists at {output_file}. Skipping download.")
        return

    logger.info("Loading OQMD dataset from matminer...")
    # Load a subset if full is too large, but let's try to load the standard 'oqmd_v1' or similar.
    # Matminer datasets: 'oqmd_v1', 'oqmd_v2', etc.
    # We use 'oqmd_v1' which is commonly available.
    try:
        df = load_dataset("oqmd_v1")
    except Exception as e:
        logger.error(f"Failed to load oqmd_v1: {e}. Trying oqmd_v2...")
        try:
            df = load_dataset("oqmd_v2")
        except Exception as e2:
            logger.error(f"Failed to load oqmd_v2: {e2}")
            raise

    logger.info(f"Loaded {len(df)} entries.")

    # Filter for Li-rich
    logger.info("Filtering for Li-rich compositions (Li >= 30%)...")
    df["is_li_rich"] = df["composition"].apply(is_li_rich)
    df_li_rich = df[df["is_li_rich"]]
    
    logger.info(f"Found {len(df_li_rich)} Li-rich entries.")

    # Filter for rock-salt (using space group if available)
    # Rock salt structure is Space Group 225 (Fm-3m)
    # If 'space_group_number' is in columns
    if "space_group_number" in df_li_rich.columns:
        logger.info("Filtering for rock-salt structure (Space Group 225)...")
        df_rocksalt = df_li_rich[df_li_rich["space_group_number"] == 225]
    else:
        logger.warning("Space group number not found in dataset. Skipping structural filter. Assuming all Li-rich are candidates.")
        df_rocksalt = df_li_rich

    logger.info(f"Filtered dataset size: {len(df_rocksalt)} entries.")

    if len(df_rocksalt) == 0:
        logger.warning("No Li-rich rock-salt structures found. Proceeding with available data (empty or warning).")
        # We still save an empty or minimal file to prevent downstream crashes, 
        # but the pipeline should fail loudly if T013 expects data.
        # However, T012 says "log warning if sample count is less than sufficient".
        # We will save whatever we have.
    
    # Select relevant columns for downstream tasks
    # We need: entry_id, composition, formation_energy, structure (if available as string/object)
    # matminer OQMD often has 'structure' as a string representation or object.
    # Let's check columns
    available_cols = list(df_rocksalt.columns)
    logger.info(f"Available columns: {available_cols}")
    
    # Ensure we have the required columns
    required = ["entry_id", "composition", "formation_energy"]
    for col in required:
        if col not in df_rocksalt.columns:
            raise ValueError(f"Required column '{col}' missing from dataset.")

    # If 'structure' is present, keep it. If not, we might need to reconstruct or skip.
    # For T013 (Magpie), we only need composition, but T020 needs structure.
    # We keep it if available.
    cols_to_save = [c for c in required if c in df_rocksalt.columns]
    if "structure" in df_rocksalt.columns:
        cols_to_save.append("structure")
    
    df_final = df_rocksalt[cols_to_save].copy()

    # Log sample count warning
    if len(df_final) < 100:
        logger.warning(f"Sample count ({len(df_final)}) is low. Proceeding with available data.")
    else:
        logger.info(f"Sample count ({len(df_final)}) is sufficient.")

    # Save to CSV
    # Note: 'structure' object might not serialize well to CSV. 
    # If it's a string, it's fine. If it's a pymatgen object, we might need to pickle or JSON.
    # For simplicity in CSV, we assume matminer loads it as a string or we drop it if not string.
    # If it's a complex object, we might need to save as parquet.
    # Let's try to save as CSV. If structure is object, we convert to string.
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            # Check if it's a pymatgen structure object
            if len(df_final) > 0 and isinstance(df_final[col].iloc[0], object):
                # Try to convert to string representation
                try:
                    df_final[col] = df_final[col].apply(lambda x: str(x) if x is not None else "")
                except:
                    pass

    df_final.to_csv(output_file, index=False)
    logger.info(f"Filtered data saved to {output_file}")

if __name__ == "__main__":
    main()