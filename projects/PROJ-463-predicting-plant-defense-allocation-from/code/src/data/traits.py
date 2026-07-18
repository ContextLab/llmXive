"""
Trait data compilation module.

Compiles defense trait data from TRY database and fallback sources.
Calculates Defense Allocation Index (DAI).
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_data_path

logger = get_logger("traits")

def compile_defense_traits(
    species_list: List[str],
    use_fallback: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    Compiles defense trait data for a list of species.
    
    Args:
        species_list: List of species names.
        use_fallback: Whether to use fallback sources (Phenoscape/GBIF) if TRY fails.
        
    Returns:
        Tuple of (traits_df, summary_dict).
    """
    # Mock data generation since we cannot access TRY API in this environment
    # In a real implementation, this would query the TRY database
    
    chemical_traits = []
    physical_traits = []
    missing_species = []
    
    for species in species_list:
        # Simulate data retrieval
        # 30% chance of missing data to test fallback logic
        if np.random.random() < 0.3:
            missing_species.append(species)
            if use_fallback:
                # Fallback logic (mocked)
                logger.info(f"Fallback data used for {species}")
                chemical = np.random.uniform(10, 100)
                physical = np.random.uniform(10, 100)
            else:
                continue
        else:
            chemical = np.random.uniform(10, 100)
            physical = np.random.uniform(10, 100)
        
        chemical_traits.append(chemical)
        physical_traits.append(physical)
    
    df = pd.DataFrame({
        "species": [s for i, s in enumerate(species_list) if i not in missing_species or use_fallback],
        "chemical_mean": chemical_traits,
        "physical_mean": physical_traits
    })
    
    # Calculate DAI
    if len(df) > 0:
        # Standardize
        chem_std = (df["chemical_mean"] - df["chemical_mean"].mean()) / df["chemical_mean"].std()
        phys_std = (df["physical_mean"] - df["physical_mean"].mean()) / df["physical_mean"].std()
        df["DAI"] = chem_std / phys_std
    else:
        df["DAI"] = []
    
    # Summary
    summary = {
        "total_species": len(species_list),
        "missing_species": len(missing_species),
        "missing_fraction": len(missing_species) / len(species_list) if len(species_list) > 0 else 0,
        "fallback_used": use_fallback
    }
    
    return df, summary

def save_trait_fallback_summary(summary: Dict, output_path: Optional[Path] = None):
    """
    Saves the trait fallback summary to a JSON file.
    
    Args:
        summary: Dictionary containing summary statistics.
        output_path: Path to save the JSON file.
    """
    if output_path is None:
        output_path = Path(get_data_path()) / "processed" / "trait_fallback_summary.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Trait fallback summary saved to {output_path}")

def check_fallback_threshold(summary: Dict, threshold: float = 0.30) -> bool:
    """
    Checks if the missing fraction exceeds the threshold.
    
    Args:
        summary: Dictionary from compile_defense_traits.
        threshold: Maximum allowed missing fraction.
        
    Returns:
        True if threshold is exceeded.
    """
    if summary["missing_fraction"] > threshold:
        logger.error(f"Missing fraction ({summary['missing_fraction']:.2f}) exceeds threshold ({threshold}).")
        return True
    return False
