"""
Module T039: Calculate Defense Allocation Index (DAI)

Computes the Defense Allocation Index (DAI) = (mean standardized chemical traits) / (mean standardized physical traits)
using compiled data from T025a (TRY) and T025b (Phenoscape/GBIF).

Input: data/processed/trait_fallback_summary.json
Output: data/processed/defense_allocation_index.csv
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Trait classification based on typical plant defense literature
# Chemical: secondary metabolites, toxins, alkaloids, terpenoids, phenolics, etc.
# Physical: structural defenses, thorns, trichomes, leaf thickness, etc.
CHEMICAL_TRAIT_KEYWORDS = [
    'alkaloid', 'terpenoid', 'phenolic', 'flavonoid', 'cyanogenic',
    'glucosinolate', 'tannin', 'saponin', 'latex', 'resin', 'toxin',
    'secondary metabolite', 'volatile', 'defense compound', 'nicotine',
    'caffeine', 'capsaicin', 'strychnine', 'morphine', 'quinine',
    'cardiac glycoside', 'saponin', 'essential oil', 'aromatic compound'
]

PHYSICAL_TRAIT_KEYWORDS = [
    'thorn', 'spine', 'prickle', 'trichome', 'hair', 'leaf thickness',
    'leaf toughness', 'leaf mass per area', 'LMA', 'cuticle', 'wax',
    'silica', 'lignin', 'cellulose', 'structural', 'mechanical',
    'barrier', 'physical defense', 'armor', 'shell', 'hardness',
    'roughness', 'pubescence', 'glandular hair', 'non-glandular hair'
]

def load_trait_data(file_path: Path) -> Dict[str, Any]:
    """Load the trait fallback summary JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"Trait data file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def classify_trait(trait_name: str) -> Optional[str]:
    """
    Classify a trait as 'chemical' or 'physical' based on keywords.
    Returns None if classification is ambiguous.
    """
    trait_lower = trait_name.lower()
    
    chemical_score = sum(1 for kw in CHEMICAL_TRAIT_KEYWORDS if kw in trait_lower)
    physical_score = sum(1 for kw in PHYSICAL_TRAIT_KEYWORDS if kw in trait_lower)
    
    if chemical_score > physical_score and chemical_score > 0:
        return 'chemical'
    elif physical_score > chemical_score and physical_score > 0:
        return 'physical'
    else:
        return None

def standardize_traits(traits_df: pd.DataFrame, group_col: str = 'species_name') -> pd.DataFrame:
    """
    Standardize traits within each type (chemical/physical) using z-score.
    """
    # Group by trait type and species
    result_dfs = []
    
    for trait_type in ['chemical', 'physical']:
        type_mask = traits_df['trait_type'] == trait_type
        type_df = traits_df[type_mask].copy()
        
        if type_df.empty:
            continue
        
        # Calculate mean and std per species for this trait type
        # We need to standardize across all chemical/physical traits for each species
        species_means = type_df.groupby(group_col)['trait_value'].mean()
        species_stds = type_df.groupby(group_col)['trait_value'].std()
        
        # For each row, calculate z-score: (value - species_mean) / species_std
        # But we need to be careful: we want to standardize the trait values
        # across the set of chemical (or physical) traits for each species
        
        # Better approach: for each species, collect all chemical traits, standardize them,
        # then collect all physical traits, standardize them
        
        # Create a copy to avoid SettingWithCopyWarning
        type_df = type_df.copy()
        type_df['mean_value'] = type_df[group_col].map(species_means)
        type_df['std_value'] = type_df[group_col].map(species_stds)
        
        # Calculate z-score
        # Handle case where std is 0 or NaN (only one trait for that type)
        type_df['z_score'] = np.where(
            (type_df['std_value'] > 0) & (~type_df['std_value'].isna()),
            (type_df['trait_value'] - type_df['mean_value']) / type_df['std_value'],
            0.0  # If only one trait, z-score is 0
        )
        
        result_dfs.append(type_df)
    
    if result_dfs:
        return pd.concat(result_dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=['species_name', 'trait_type', 'trait_value', 'z_score'])

def calculate_dai(trait_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate Defense Allocation Index for each species.
    DAI = mean(standardized chemical traits) / mean(standardized physical traits)
    """
    # Combine primary and fallback results
    all_traits = []
    
    # Process primary source results
    if 'primary_source_results' in trait_data:
        for species_name, species_data in trait_data['primary_source_results'].items():
            if 'traits' in species_data:
                for trait in species_data['traits']:
                    all_traits.append({
                        'species_name': species_name,
                        'trait_name': trait.get('trait_name', ''),
                        'trait_value': trait.get('trait_value', 0),
                        'trait_type': classify_trait(trait.get('trait_name', ''))
                    })
    
    # Process fallback results
    if 'fallback_results' in trait_data:
        for species_name, species_data in trait_data['fallback_results'].items():
            if 'traits' in species_data:
                for trait in species_data['traits']:
                    all_traits.append({
                        'species_name': species_name,
                        'trait_name': trait.get('trait_name', ''),
                        'trait_value': trait.get('trait_value', 0),
                        'trait_type': classify_trait(trait.get('trait_name', ''))
                    })
    
    if not all_traits:
        logger.warning("No traits found in input data")
        return pd.DataFrame(columns=['species_name', 'chemical_mean', 'physical_mean', 'dai'])
    
    traits_df = pd.DataFrame(all_traits)
    
    # Filter out unclassified traits
    traits_df = traits_df[traits_df['trait_type'].notna()]
    
    if traits_df.empty:
        logger.warning("No classified traits found after filtering")
        return pd.DataFrame(columns=['species_name', 'chemical_mean', 'physical_mean', 'dai'])
    
    # Standardize traits
    standardized_df = standardize_traits(traits_df)
    
    # Calculate means per species per trait type
    dai_results = []
    
    for species in standardized_df['species_name'].unique():
        species_data = standardized_df[standardized_df['species_name'] == species]
        
        chemical_data = species_data[species_data['trait_type'] == 'chemical']
        physical_data = species_data[species_data['trait_type'] == 'physical']
        
        chemical_mean = chemical_data['z_score'].mean() if not chemical_data.empty else 0.0
        physical_mean = physical_data['z_score'].mean() if not physical_data.empty else 0.0
        
        # Calculate DAI
        # Avoid division by zero
        if abs(physical_mean) < 1e-10:
            dai = float('inf') if chemical_mean > 0 else float('-inf') if chemical_mean < 0 else 0.0
        else:
            dai = chemical_mean / physical_mean
        
        dai_results.append({
            'species_name': species,
            'chemical_mean': chemical_mean,
            'physical_mean': physical_mean,
            'dai': dai
        })
    
    return pd.DataFrame(dai_results)

def main():
    """Main entry point for DAI calculation."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    trait_data_path = project_root / 'data' / 'processed' / 'trait_fallback_summary.json'
    output_path = project_root / 'data' / 'processed' / 'defense_allocation_index.csv'
    
    logger.info(f"Loading trait data from {trait_data_path}")
    
    try:
        trait_data = load_trait_data(trait_data_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load trait data: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in trait data file: {e}")
        sys.exit(1)
    
    logger.info("Calculating Defense Allocation Index...")
    dai_df = calculate_dai(trait_data)
    
    if dai_df.empty:
        logger.warning("No DAI values calculated. Creating empty output file.")
    else:
        logger.info(f"Calculated DAI for {len(dai_df)} species")
        logger.info(f"DAI range: {dai_df['dai'].min():.4f} to {dai_df['dai'].max():.4f}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    dai_df.to_csv(output_path, index=False)
    logger.info(f"Defense Allocation Index saved to {output_path}")
    
    # Print summary
    if not dai_df.empty:
        print("\n=== Defense Allocation Index Summary ===")
        print(f"Species analyzed: {len(dai_df)}")
        print(f"Chemical mean range: {dai_df['chemical_mean'].min():.4f} to {dai_df['chemical_mean'].max():.4f}")
        print(f"Physical mean range: {dai_df['physical_mean'].min():.4f} to {dai_df['physical_mean'].max():.4f}")
        print(f"DAI range: {dai_df['dai'].min():.4f} to {dai_df['dai'].max():.4f}")
        print(f"Mean DAI: {dai_df['dai'].mean():.4f}")
        print(f"Median DAI: {dai_df['dai'].median():.4f}")
        print(f"Std DAI: {dai_df['dai'].std():.4f}")
        print("\nTop 5 species by DAI (highest chemical allocation):")
        print(dai_df.nlargest(5, 'dai')[['species_name', 'dai']])
        print("\nBottom 5 species by DAI (highest physical allocation):")
        print(dai_df.nsmallest(5, 'dai')[['species_name', 'dai']])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
