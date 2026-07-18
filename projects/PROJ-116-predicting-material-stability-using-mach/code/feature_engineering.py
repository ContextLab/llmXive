import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from matminer.featurizers.composition import Magpie
from matminer.featurizers.site import SiteStatsFingerprint
from matminer.featurizers.structure import CrystalGraph, StructuralHierarchy
from pymatgen.analysis.local_env import VoronoiNN
from pymatgen.core import Structure
import json
from typing import List, Dict, Any, Optional, Tuple

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, OUTPUTS_LOGS_DIR
from utils.logging import setup_logger
from utils.validation import validate_structure, check_degenerate_voronoi_cells, check_missing_bond_lengths

# Setup logger
logger = setup_logger("feature_engineering", log_file="feature_engineering.log")

def load_raw_data() -> pd.DataFrame:
    """
    Load raw data from data/raw/.
    Expects a parquet or csv file with a 'structure' column containing Structure objects or serialized data.
    """
    raw_dir = RAW_DATA_DIR
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    # Look for parquet files first
    parquet_files = list(raw_dir.glob("*.parquet"))
    if parquet_files:
        df = pd.read_parquet(parquet_files[0])
    else:
        # Fallback to CSV
        csv_files = list(raw_dir.glob("*.csv"))
        if csv_files:
            df = pd.read_csv(csv_files[0])
            # Reconstruct Structure objects if needed (assuming string representation)
            if "structure" in df.columns:
                df["structure"] = df["structure"].apply(lambda x: Structure.from_str(x) if isinstance(x, str) else x)
        else:
            raise FileNotFoundError(f"No data files found in {raw_dir}")
    
    logger.info(f"Loaded {len(df)} raw entries from {parquet_files[0] if parquet_files else csv_files[0]}")
    return df

def compute_magpie_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Compute Magpie compositional features.
    Returns (df_with_features, count_imputed).
    """
    magpie = Magpie.from_preset("ElemStat")
    
    # Extract composition strings
    compositions = df["composition"].tolist()
    
    # Featurize
    features = magpie.featurize_dataframe(compositions, col_id="composition")
    
    # Handle missing values
    count_imputed = 0
    if features.isnull().sum().sum() > 0:
        count_imputed = features.isnull().sum().sum()
        median_values = features.median()
        features = features.fillna(median_values)
        logger.warning(f"Imputed {count_imputed} missing values with median")
    
    # Merge back to original dataframe
    df_features = pd.concat([df.reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    
    return df_features, count_imputed

def compute_voronoi_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Compute local coordination features using Voronoi tessellation.
    Features: coordination number, face area, solid angle statistics.
    Returns (df_with_features, count_skipped).
    """
    voronoi_features_list = []
    count_skipped = 0
    skipped_ids = []
    
    vnn = VoronoiNN()
    
    # Define site fingerprint for Voronoi stats
    # We will compute stats over all sites in the structure
    site_features = ["coordination_number", "face_area", "solid_angle"]
    
    for idx, row in df.iterrows():
        structure = row.get("structure")
        material_id = row.get("material_id", idx)
        
        if structure is None:
            logger.warning(f"Skipping entry {material_id}: structure is None")
            count_skipped += 1
            skipped_ids.append(material_id)
            voronoi_features_list.append({f"{site_features[i]}_mean": np.nan for i in range(len(site_features))})
            continue
        
        try:
            # Check for degenerate cells
            if check_degenerate_voronoi_cells(structure):
                logger.warning(f"Skipping entry {material_id}: degenerate Voronoi cells")
                count_skipped += 1
                skipped_ids.append(material_id)
                voronoi_features_list.append({f"{site_features[i]}_mean": np.nan for i in range(len(site_features))})
                continue
            
            # Check for missing bond lengths
            if check_missing_bond_lengths(structure):
                logger.warning(f"Skipping entry {material_id}: missing bond lengths")
                count_skipped += 1
                skipped_ids.append(material_id)
                voronoi_features_list.append({f"{site_features[i]}_mean": np.nan for i in range(len(site_features))})
                continue
            
            # Compute Voronoi neighbors for each site
            site_stats = []
            for site_idx in range(len(structure)):
                neighbors = vnn.get_nn(structure, site_idx)
                if not neighbors:
                    continue
                
                cn = len(neighbors)
                face_areas = [n.polyhedron_area for n in neighbors if hasattr(n, 'polyhedron_area') and n.polyhedron_area is not None]
                solid_angles = [n.solid_angle for n in neighbors if hasattr(n, 'solid_angle') and n.solid_angle is not None]
                
                if face_areas:
                    site_stats.append({
                        "coordination_number": cn,
                        "face_area_mean": np.mean(face_areas),
                        "face_area_std": np.std(face_areas),
                        "solid_angle_mean": np.mean(solid_angles),
                        "solid_angle_std": np.std(solid_angles)
                    })
            
            if not site_stats:
                logger.warning(f"No valid site stats for entry {material_id}")
                voronoi_features_list.append({
                    "coordination_number_mean": np.nan,
                    "face_area_mean": np.nan,
                    "face_area_std": np.nan,
                    "solid_angle_mean": np.nan,
                    "solid_angle_std": np.nan
                })
            else:
                # Aggregate over sites
                df_site = pd.DataFrame(site_stats)
                agg_features = {
                    "coordination_number_mean": df_site["coordination_number"].mean(),
                    "face_area_mean": df_site["face_area_mean"].mean(),
                    "face_area_std": df_site["face_area_std"].mean(),
                    "solid_angle_mean": df_site["solid_angle_mean"].mean(),
                    "solid_angle_std": df_site["solid_angle_std"].mean()
                }
                voronoi_features_list.append(agg_features)
                
        except Exception as e:
            logger.error(f"Error computing Voronoi features for entry {material_id}: {e}")
            count_skipped += 1
            skipped_ids.append(material_id)
            voronoi_features_list.append({
                "coordination_number_mean": np.nan,
                "face_area_mean": np.nan,
                "face_area_std": np.nan,
                "solid_angle_mean": np.nan,
                "solid_angle_std": np.nan
            })
    
    df_voronoi = pd.DataFrame(voronoi_features_list)
    df_voronoi.index = df.index
    
    # Combine with original dataframe
    df_combined = pd.concat([df.reset_index(drop=True), df_voronoi.reset_index(drop=True)], axis=1)
    
    logger.info(f"Computed Voronoi features. Skipped {count_skipped} entries.")
    if skipped_ids:
        logger.debug(f"Skipped IDs: {skipped_ids[:10]}...")
    
    return df_combined, count_skipped

def compute_bond_length_histograms(df: pd.DataFrame, n_bins: int = 20) -> Tuple[pd.DataFrame, int]:
    """
    Compute bond-length histogram features.
    Returns (df_with_features, count_skipped).
    """
    bond_length_features_list = []
    count_skipped = 0
    skipped_ids = []
    
    for idx, row in df.iterrows():
        structure = row.get("structure")
        material_id = row.get("material_id", idx)
        
        if structure is None:
            logger.warning(f"Skipping entry {material_id}: structure is None")
            count_skipped += 1
            skipped_ids.append(material_id)
            # Create empty features
            bond_length_features_list.append({f"bond_length_bin_{i}": np.nan for i in range(n_bins)})
            continue
        
        try:
            # Get all bond lengths
            bond_lengths = []
            for i in range(len(structure)):
                for j in range(i + 1, len(structure)):
                    dist = structure[i].distance_to(structure[j])
                    if 0 < dist < 10: # Filter reasonable bond lengths
                        bond_lengths.append(dist)
            
            if not bond_lengths:
                logger.warning(f"No bond lengths found for entry {material_id}")
                count_skipped += 1
                skipped_ids.append(material_id)
                bond_length_features_list.append({f"bond_length_bin_{i}": np.nan for i in range(n_bins)})
                continue
            
            # Compute histogram
            hist, bin_edges = np.histogram(bond_lengths, bins=n_bins, range=(0, 10))
            
            # Normalize
            hist_norm = hist / len(bond_lengths)
            
            features = {f"bond_length_bin_{i}": hist_norm[i] for i in range(n_bins)}
            features["bond_length_mean"] = np.mean(bond_lengths)
            features["bond_length_std"] = np.std(bond_lengths)
            features["bond_length_min"] = np.min(bond_lengths)
            features["bond_length_max"] = np.max(bond_lengths)
            
            bond_length_features_list.append(features)
            
        except Exception as e:
            logger.error(f"Error computing bond length features for entry {material_id}: {e}")
            count_skipped += 1
            skipped_ids.append(material_id)
            bond_length_features_list.append({f"bond_length_bin_{i}": np.nan for i in range(n_bins)})
            bond_length_features_list[-1].update({
                "bond_length_mean": np.nan,
                "bond_length_std": np.nan,
                "bond_length_min": np.nan,
                "bond_length_max": np.nan
            })
    
    df_bond = pd.DataFrame(bond_length_features_list)
    df_bond.index = df.index
    
    # Combine with original dataframe
    df_combined = pd.concat([df.reset_index(drop=True), df_bond.reset_index(drop=True)], axis=1)
    
    logger.info(f"Computed bond length histograms. Skipped {count_skipped} entries.")
    if skipped_ids:
        logger.debug(f"Skipped IDs: {skipped_ids[:10]}...")
    
    return df_combined, count_skipped

def log_imputation(imputation_log_path: Path, count_imputed: int, count_skipped: int) -> None:
    """
    Log imputation and skipping statistics.
    """
    imputation_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(imputation_log_path, 'w') as f:
        f.write(f"Imputation Log\n")
        f.write(f"==============\n")
        f.write(f"Total imputed values: {count_imputed}\n")
        f.write(f"Total skipped entries (Voronoi/Bond): {count_skipped}\n")

def main():
    """
    Main function to run feature engineering pipeline.
    1. Load raw data
    2. Compute Magpie features
    3. Compute Voronoi features (local coordination)
    4. Compute Bond Length features
    5. Combine and save
    """
    logger.info("Starting feature engineering pipeline...")
    
    # Load raw data
    df = load_raw_data()
    logger.info(f"Loaded {len(df)} raw entries")
    
    # Compute Magpie features
    df_magpie, count_imputed = compute_magpie_features(df)
    logger.info(f"Magpie features computed. Imputed {count_imputed} values.")
    
    # Compute Voronoi features (Local Coordination)
    df_voronoi, count_voronoi_skipped = compute_voronoi_features(df_magpie)
    logger.info(f"Voronoi features computed. Skipped {count_voronoi_skipped} entries.")
    
    # Compute Bond Length features
    df_bond, count_bond_skipped = compute_bond_length_histograms(df_voronoi)
    logger.info(f"Bond length features computed. Skipped {count_bond_skipped} entries.")
    
    # Total skipped
    total_skipped = count_voronoi_skipped + count_bond_skipped
    
    # Log imputation/skipping
    log_imputation(OUTPUTS_LOGS_DIR / "imputation_log.txt", count_imputed, total_skipped)
    
    # Select feature columns (exclude non-feature columns)
    exclude_cols = ["material_id", "composition", "structure", "structure_data", "formation_energy_per_atom", "energy_above_hull", "elements", "num_elements", "num_sites"]
    feature_cols = [col for col in df_bond.columns if col not in exclude_cols]
    
    # Prepare final dataframe
    df_final = df_bond[feature_cols].copy()
    
    # Add material_id for tracking
    df_final.insert(0, "material_id", df_bond["material_id"])
    
    # Save to parquet
    output_path = PROCESSED_DATA_DIR / "augmented_features.parquet"
    df_final.to_parquet(output_path, index=False)
    logger.info(f"Saved augmented features to {output_path}")
    logger.info(f"Total features: {len(feature_cols)}")
    
    return df_final

if __name__ == "__main__":
    main()
