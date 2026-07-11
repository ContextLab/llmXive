"""
Power Analysis Module for Plant Drought Tolerance Study.

Calculates required sample size (N) using statsmodels.stats.power.FTestPower.
Fetches species lists from NPPN (via downloaded images) and TRY database.
Halts with critical error if overlap N < 55.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Set, List, Dict, Any

import yaml
import pandas as pd
from statsmodels.stats.power import FTestPower

# Project imports
from config import ensure_directories, get_config_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("state/power_analysis.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_OVERLAP_SPECIES = 55
EFFECT_SIZE = 0.5  # Medium effect size (Cohen's f)
ALPHA = 0.05
POWER = 0.80

def get_nppn_species_list() -> Set[str]:
    """
    Fetch species list from NPPN dataset (downloaded images).
    Reads species from the metadata or file paths if available.
    Since T012 downloads images, we check for a manifest or infer from filenames.
    For this implementation, we assume a manifest 'data/raw/nppn_images/metadata.csv'
    exists or we derive from the directory structure if T012 produced one.
    If T012 hasn't produced a manifest, we attempt to list unique species
    from the image filenames or a generated list if the download included one.
    """
    nppn_data_dir = Path("data/raw/nppn_images")
    species_set: Set[str] = set()

    if not nppn_data_dir.exists():
        logger.warning(f"NPPN data directory {nppn_data_dir} not found. "
                       "Assuming empty species list from NPPN.")
        return species_set

    # Try to find a manifest or metadata file
    manifest_paths = [
        nppn_data_dir / "metadata.csv",
        nppn_data_dir / "species_list.csv",
        nppn_data_dir / "manifest.csv"
    ]

    for manifest_path in manifest_paths:
        if manifest_path.exists():
            try:
                df = pd.read_csv(manifest_path)
                # Look for a column named 'species' or similar
                species_cols = [col for col in df.columns if 'species' in col.lower()]
                if species_cols:
                    species_set.update(df[species_cols[0]].dropna().astype(str).unique())
                    logger.info(f"Loaded {len(species_set)} species from {manifest_path}")
                    return species_set
            except Exception as e:
                logger.warning(f"Failed to read manifest {manifest_path}: {e}")

    # Fallback: If no manifest, try to infer from directory structure or filenames
    # This assumes images are named like 'species_name_001.png'
    for root, _, files in os.walk(nppn_data_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Simple heuristic: extract species from filename before first underscore or dot
                name_part = file.rsplit('.', 1)[0]
                if '_' in name_part:
                    species = name_part.split('_')[0]
                    if species:
                        species_set.add(species)
                else:
                    # If no underscore, maybe the whole name is species (unlikely but possible)
                    species_set.add(name_part)
    
    logger.info(f"Inferred {len(species_set)} species from NPPN filenames.")
    return species_set

def get_try_species_list() -> Set[str]:
    """
    Fetch species list from TRY database.
    Since T020 (download_traits.py) is not yet complete, we attempt to fetch
    a list of species available in TRY via a lightweight query or a cached list.
    If T020 is not done, we might not have a full list.
    For this task, we assume we can query TRY for a list of species with conductance/photosynthesis data.
    If the trydata package is not fully configured or T020 is pending, we simulate
    a fetch by checking for a pre-downloaded list or returning an empty set if unreachable.
    
    NOTE: In a real run, this would use the 'trydata' package or a direct API call.
    Since T020 is pending, we might not have the full list. We'll attempt to load
    a cached list if T020 has partially run, or return empty if not.
    """
    try_data_dir = Path("data/raw/try_data")
    species_set: Set[str] = set()

    # Check for a pre-downloaded species list (e.g., from T020 if it ran partially)
    manifest_paths = [
        try_data_dir / "species_list.csv",
        try_data_dir / "metadata.csv",
        try_data_dir / "traits_manifest.csv"
    ]

    for manifest_path in manifest_paths:
        if manifest_path.exists():
            try:
                df = pd.read_csv(manifest_path)
                species_cols = [col for col in df.columns if 'species' in col.lower()]
                if species_cols:
                    species_set.update(df[species_cols[0]].dropna().astype(str).unique())
                    logger.info(f"Loaded {len(species_set)} species from {manifest_path}")
                    return species_set
            except Exception as e:
                logger.warning(f"Failed to read manifest {manifest_path}: {e}")

    # If no manifest found, attempt to query TRY directly (if trydata is available)
    # This is a best-effort approach. If trydata is not installed or configured, skip.
    try:
        # Attempt to import trydata (optional dependency)
        import trydata
        # Query for species with stomatal conductance or photosynthesis data
        # This is a simplified example; real implementation would be more complex
        logger.info("Attempting to fetch species list from TRY via trydata...")
        # Placeholder: In real code, this would be a proper query
        # For now, we return an empty set if we can't fetch
        logger.warning("TRY data fetch not fully implemented yet. Returning empty set.")
    except ImportError:
        logger.warning("trydata package not installed. Cannot fetch TRY species list.")
    except Exception as e:
        logger.warning(f"Failed to fetch TRY species list: {e}")

    return species_set

def calculate_sample_size(effect_size: float = EFFECT_SIZE, alpha: float = ALPHA, power: float = POWER) -> int:
    """
    Calculate required sample size using FTestPower.
    Returns the minimum N required for the given parameters.
    """
    solver = FTestPower()
    # For a one-way ANOVA or regression with k predictors, we need to specify k.
    # Here we assume a simple linear regression (k=1) or ANOVA with 2 groups.
    # For a general power analysis, we can use k=1 for simplicity.
    k = 1  # Number of predictors (or groups - 1 for ANOVA)
    n = solver.solve(effect_size=effect_size, alpha=alpha, power=power, k_num=k)
    return int(n)

def main():
    """
    Main entry point for power analysis.
    1. Fetch species from NPPN and TRY.
    2. Compute overlap.
    3. If overlap < 55, halt with critical error.
    4. Otherwise, calculate required sample size and save report.
    """
    logger.info("Starting power analysis...")

    # Ensure output directories exist
    ensure_directories()

    # Fetch species lists
    nppn_species = get_nppn_species_list()
    try_species = get_try_species_list()

    logger.info(f"NPPN species count: {len(nppn_species)}")
    logger.info(f"TRY species count: {len(try_species)}")

    # Compute overlap
    overlap_species = nppn_species.intersection(try_species)
    overlap_count = len(overlap_species)

    logger.info(f"Overlap species count: {overlap_count}")

    # Check minimum overlap
    if overlap_count < MIN_OVERLAP_SPECIES:
        error_msg = f"Insufficient species for power analysis (N < {MIN_OVERLAP_SPECIES}). " \
                    f"Found {overlap_count} overlapping species. " \
                    f"Required: {MIN_OVERLAP_SPECIES}."
        logger.critical(error_msg)
        # Save a failure report before exiting
        report = {
            "status": "failed",
            "reason": "Insufficient species overlap",
            "nppn_species_count": len(nppn_species),
            "try_species_count": len(try_species),
            "overlap_count": overlap_count,
            "minimum_required": MIN_OVERLAP_SPECIES,
            "effect_size": EFFECT_SIZE,
            "alpha": ALPHA,
            "power": POWER,
            "required_sample_size": None
        }
        output_path = Path("state/power_analysis_report.yaml")
        with open(output_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False)
        logger.info(f"Power analysis report saved to {output_path}")
        sys.exit(1)

    # Calculate required sample size
    required_n = calculate_sample_size()
    logger.info(f"Required sample size (N) for power={POWER}, alpha={ALPHA}, effect_size={EFFECT_SIZE}: {required_n}")

    # Prepare report
    report = {
        "status": "success",
        "nppn_species_count": len(nppn_species),
        "try_species_count": len(try_species),
        "overlap_species_count": overlap_count,
        "overlap_species_list": sorted(list(overlap_species)),
        "minimum_required": MIN_OVERLAP_SPECIES,
        "effect_size": EFFECT_SIZE,
        "alpha": ALPHA,
        "power": POWER,
        "required_sample_size": required_n,
        "notes": "Sample size calculated for a linear regression model with 1 predictor. "
                 "Adjust if model complexity changes."
    }

    # Save report
    output_path = Path("state/power_analysis_report.yaml")
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)

    logger.info(f"Power analysis report saved to {output_path}")
    logger.info("Power analysis completed successfully.")

if __name__ == "__main__":
    main()
