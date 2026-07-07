import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

# Import from existing API surface
from utils.graph_builder import build_molecular_graph, log_invalid_smiles, is_valid_molecule
from utils.persistence_utils import (
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    handle_empty_diagram,
    get_topological_features
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/tda_computation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data')
PROCESSED_DIR = DATA_DIR / 'processed'
LOGS_DIR = DATA_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_RESOLUTION = 20
DEFAULT_GRID_MIN = 0.0
DEFAULT_GRID_MAX = 10.0

def load_processed_data() -> pd.DataFrame:
    """Load the ingested ESOL dataset from data/processed/esol_data.csv."""
    input_file = PROCESSED_DIR / 'esol_data.csv'
    if not input_file.exists():
        raise FileNotFoundError(f"Required input file not found: {input_file}")
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['smiles', 'logP']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input data: {missing}")
    
    logger.info(f"Loaded {len(df)} molecules from {input_file}")
    return df

def compute_traditional_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute traditional molecular descriptors using RDKit.
    Returns a DataFrame with SMILES, logP, and computed descriptors.
    """
    logger.info("Computing traditional descriptors...")
    descriptors_list = []
    invalid_count = 0

    for idx, row in df.iterrows():
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None or not is_valid_molecule(mol):
            log_invalid_smiles(smiles, "Traditional descriptor computation")
            invalid_count += 1
            continue

        # Compute a standard set of descriptors
        desc_vals = {
            'smiles': smiles,
            'logP': row['logP'],
            'mw': Descriptors.MolWt(mol),
            'logP_rdkit': Descriptors.MolLogP(mol),
            'numHDonors': Descriptors.NumHDonors(mol),
            'numHAcceptors': Descriptors.NumHAcceptors(mol),
            'numRotatableBonds': Descriptors.NumRotatableBonds(mol),
            'tpsa': Descriptors.TPSA(mol),
            'numAromaticRings': Descriptors.NumAromaticRings(mol),
            'numAliphaticRings': Descriptors.NumAliphaticRings(mol),
            'numSaturatedRings': Descriptors.NumSaturatedRings(mol),
            'numHeteroatoms': Descriptors.HeavyAtomCount(mol) - Descriptors.NumCarbons(mol),
            'ringCount': Descriptors.RingCount(mol)
        }
        descriptors_list.append(desc_vals)

    logger.info(f"Computed traditional descriptors for {len(descriptors_list)} valid molecules "
                f"({invalid_count} invalid skipped)")
    
    return pd.DataFrame(descriptors_list)

def vectorize_diagram_to_persistence_image(
    diagram: List[Tuple[float, float]],
    resolution: int = DEFAULT_RESOLUTION,
    grid_min: float = DEFAULT_GRID_MIN,
    grid_max: float = DEFAULT_GRID_MAX,
    sigma: Optional[float] = None
) -> np.ndarray:
    """
    Convert a persistence diagram to a persistence image.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (resolution x resolution).
        grid_min: Minimum value for the grid axis.
        grid_max: Maximum value for the grid axis.
        sigma: Standard deviation for Gaussian kernel. If None, computed as grid step.
    
    Returns:
        1D flattened array of the persistence image.
    """
    if not diagram:
        # Handle empty diagram: return zero vector
        return np.zeros(resolution * resolution)

    diagram_arr = np.array(diagram)
    births = diagram_arr[:, 0]
    deaths = diagram_arr[:, 1]
    pers = deaths - births

    # Create grid
    x = np.linspace(grid_min, grid_max, resolution)
    y = np.linspace(grid_min, grid_max, resolution)
    X, Y = np.meshgrid(x, y)
    
    # Initialize image
    img = np.zeros((resolution, resolution))
    
    # Default sigma
    if sigma is None:
        sigma = (grid_max - grid_min) / resolution

    # Weight by persistence
    weights = pers ** 2

    # Gaussian kernel contribution
    for i, (b, d) in enumerate(diagram):
        p = (b, d)
        w = weights[i]
        # 2D Gaussian
        Z = np.exp(-((X - p[0])**2 + (Y - p[1])**2) / (2 * sigma**2))
        img += w * Z

    # Flatten and normalize
    img_flat = img.flatten()
    if np.sum(img_flat) > 0:
        img_flat = img_flat / np.sum(img_flat)
    
    return img_flat

def process_single_molecule(
    smiles: str,
    resolution: int = DEFAULT_RESOLUTION
) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule: build graph, compute persistence diagram, vectorize.
    
    Returns:
        Dictionary with TDA features or None if molecule is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or not is_valid_molecule(mol):
        log_invalid_smiles(smiles, "TDA computation")
        return None

    try:
        # Build molecular graph
        G = build_molecular_graph(mol)
        if G is None or G.number_of_nodes() == 0:
            log_invalid_smiles(smiles, "Empty graph construction")
            return None

        # Compute shortest path matrix
        try:
            dist_matrix = compute_shortest_path_matrix(G)
        except Exception as e:
            logger.warning(f"Shortest path computation failed for {smiles}: {e}")
            return None

        # Build filtration and compute diagram
        filtration = build_shortest_path_filtration(G, dist_matrix)
        diagram = compute_persistence_diagram(filtration)

        # Handle empty diagram
        if not diagram:
            diagram = handle_empty_diagram()

        # Vectorize
        pi_vector = vectorize_diagram_to_persistence_image(diagram, resolution=resolution)

        # Get topological features (Betti numbers, etc.)
        topo_features = get_topological_features(diagram)

        return {
            'smiles': smiles,
            'diagram': diagram,
            'persistence_image': pi_vector,
            'topological_features': topo_features
        }

    except Exception as e:
        logger.error(f"Unexpected error processing {smiles}: {e}")
        return None

def run_tda_computation(
    input_df: pd.DataFrame,
    output_path: Path,
    resolution: int = DEFAULT_RESOLUTION
) -> pd.DataFrame:
    """
    Run TDA computation on the entire dataset.
    
    Args:
        input_df: DataFrame with 'smiles' column.
        output_path: Path to save the output CSV.
        resolution: Grid resolution for persistence images.
    
    Returns:
        DataFrame with TDA features.
    """
    logger.info(f"Starting TDA computation with resolution={resolution}")
    start_time = time.time()

    results = []
    valid_count = 0
    invalid_count = 0

    for idx, row in input_df.iterrows():
        smiles = row['smiles']
        result = process_single_molecule(smiles, resolution=resolution)
        
        if result is not None:
            valid_count += 1
            # Flatten persistence image into columns
            pi_cols = {f'pi_{i}': val for i, val in enumerate(result['persistence_image'])}
            row_dict = {
                'smiles': result['smiles'],
                'num_topological_features': len(result['topological_features'])
            }
            row_dict.update(pi_cols)
            row_dict.update(result['topological_features'])
            results.append(row_dict)
        else:
            invalid_count += 1

    elapsed = time.time() - start_time
    logger.info(f"TDA computation complete: {valid_count} valid, {invalid_count} invalid "
                f"in {elapsed:.2f}s")

    if not results:
        raise RuntimeError("No valid molecules processed. Output would be empty.")

    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved TDA features to {output_path}")

    return output_df

def run_sweep(
    resolutions: List[int] = [10, 20, 30],
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[int, pd.DataFrame]:
    """
    Run TDA computation sweep over multiple resolutions.
    
    Args:
        resolutions: List of grid resolutions to test.
        input_path: Path to input CSV (defaults to data/processed/esol_data.csv).
        output_dir: Directory to save outputs (defaults to data/processed/).
    
    Returns:
        Dictionary mapping resolution to output DataFrame.
    """
    if input_path is None:
        input_path = PROCESSED_DIR / 'esol_data.csv'
    if output_dir is None:
        output_dir = PROCESSED_DIR
    
    input_df = load_processed_data()
    results = {}
    
    for res in resolutions:
        logger.info(f"Running sweep for resolution {res}")
        output_path = output_dir / f'tda_features_res{res}.csv'
        df = run_tda_computation(input_df, output_path, resolution=res)
        results[res] = df
        
    return results

def main():
    """Main entry point for TDA computation."""
    logger.info("Starting TDA computation pipeline...")
    
    # Load data
    df = load_processed_data()
    
    # Compute traditional descriptors
    traditional_df = compute_traditional_descriptors(df)
    traditional_path = PROCESSED_DIR / 'traditional_descriptors.csv'
    traditional_df.to_csv(traditional_path, index=False)
    logger.info(f"Saved traditional descriptors to {traditional_path}")
    
    # Compute TDA features
    tda_df = run_tda_computation(df, PROCESSED_DIR / 'tda_features.csv')
    
    logger.info("TDA computation pipeline completed successfully.")
    
    # Print summary
    print(f"\nPipeline Summary:")
    print(f"  - Input molecules: {len(df)}")
    print(f"  - Traditional descriptors: {len(traditional_df)} rows, {len(traditional_df.columns)} cols")
    print(f"  - TDA features: {len(tda_df)} rows, {len(tda_df.columns)} cols")
    print(f"  - Output files:")
    print(f"      {traditional_path}")
    print(f"      {PROCESSED_DIR / 'tda_features.csv'}")

if __name__ == "__main__":
    main()
