import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import networkx as nx

# Import from local utils as per API surface
from utils.graph_builder import build_molecular_graph, is_valid_molecule, log_invalid_smiles, setup_invalid_smiles_logger
from utils.persistence_utils import compute_shortest_path_matrix, build_shortest_path_filtration, compute_persistence_diagram, handle_empty_diagram, get_topological_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load the ingested ESOL dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    # Validate expected columns
    required_cols = ['smiles', 'logP']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    return df

def compute_traditional_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute a standard set of traditional molecular descriptors.
    Returns a dictionary of descriptor_name: value.
    """
    if mol is None:
        return {}

    descriptors = {
        'MolWt': Descriptors.MolWt(mol),
        'MolLogP': Descriptors.MolLogP(mol),
        'TPSA': Descriptors.TPSA(mol),
        'NumHDonors': rdMolDescriptors.CalcNumHBD(mol),
        'NumHAcceptors': rdMolDescriptors.CalcNumHBA(mol),
        'NumRotatableBonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
        'NumAromaticRings': rdMolDescriptors.CalcNumAromaticRings(mol),
        'NumSatAromaticRings': rdMolDescriptors.CalcNumAromaticRings(mol), # Alias for consistency
        'NumAliphaticRings': rdMolDescriptors.CalcNumAliphaticRings(mol),
        'NumHeteroatoms': rdMolDescriptors.CalcNumHeteroatoms(mol),
        'FractionCSP3': rdMolDescriptors.CalcFractionCSP3(mol),
        'HeavyAtomCount': rdMolDescriptors.CalcNumHeavyAtoms(mol),
        'RingCount': rdMolDescriptors.CalcNumRings(mol),
    }
    return descriptors

def vectorize_diagram_to_persistence_image(diagram: List[Tuple[float, float]], 
                                           resolution: int = 20, 
                                           bounds: Optional[Tuple[float, float, float, float]] = None,
                                           sigma: float = 0.1) -> np.ndarray:
    """
    Convert a persistence diagram to a persistence image.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (resolution x resolution).
        bounds: (min_birth, max_birth, min_persistence, max_persistence). If None, computed from data.
        sigma: Standard deviation for Gaussian kernel.
    
    Returns:
        1D numpy array representing the vectorized image.
    """
    if not diagram:
        return np.zeros(resolution * resolution)

    births = np.array([d[0] for d in diagram])
    deaths = np.array([d[1] for d in diagram])
    persistences = deaths - births

    if bounds is None:
        min_b, max_b = births.min(), births.max()
        min_p, max_p = persistences.min(), persistences.max()
        # Add small margin to avoid boundary issues
        margin_b = (max_b - min_b) * 0.05 if max_b > min_b else 0.1
        margin_p = (max_p - min_p) * 0.05 if max_p > min_p else 0.1
        bounds = (min_b - margin_b, max_b + margin_b, min_p - margin_p, max_p + margin_p)

    min_b, max_b, min_p, max_p = bounds

    # Create grid
    x = np.linspace(min_b, max_b, resolution)
    y = np.linspace(min_p, max_p, resolution)
    X, Y = np.meshgrid(x, y)
    grid_points = np.vstack([X.ravel(), Y.ravel()]).T

    # Gaussian weights based on persistence
    weights = np.exp(-persistences / (2 * sigma**2))

    # Accumulate contributions
    image = np.zeros((resolution, resolution))
    
    for i, (b, p) in enumerate(zip(births, persistences)):
        if p <= 0: continue
        # Calculate distance to grid centers
        dist_sq = np.sum((grid_points - np.array([b, p]))**2, axis=1)
        gaussian_vals = np.exp(-dist_sq / (2 * sigma**2))
        image += weights[i] * gaussian_vals.reshape(resolution, resolution)

    return image.ravel()

def process_single_molecule(smiles: str, 
                            resolution: int = 20, 
                            log_path: Optional[str] = None) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Process a single molecule: validate, build graph, compute TDA, compute traditional descriptors.
    
    Returns:
        Tuple of (traditional_desc_dict, tda_features_dict) or (None, None) if invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not is_valid_molecule(mol):
        if log_path:
            log_invalid_smiles(smiles, log_path, "Invalid molecule or empty graph")
        return None, None

    # 1. Traditional Descriptors
    trad_desc = compute_traditional_descriptors(mol)

    # 2. TDA Features
    try:
        # Build graph
        G = build_molecular_graph(mol)
        
        if G.number_of_nodes() == 0:
            if log_path:
                log_invalid_smiles(smiles, log_path, "Empty graph after construction")
            return trad_desc, {"tda_status": "empty_graph"}

        # Compute shortest path matrix
        try:
            dist_matrix = compute_shortest_path_matrix(G)
        except Exception as e:
            logger.warning(f"Shortest path computation failed for {smiles}: {e}")
            dist_matrix = None

        if dist_matrix is None or dist_matrix.size == 0:
            # Fallback for disconnected or single node
            tda_features = handle_empty_diagram(resolution)
            return trad_desc, tda_features

        # Build filtration
        filtration = build_shortest_path_filtration(G, dist_matrix)
        
        # Compute diagram
        diagram = compute_persistence_diagram(filtration)
        
        if not diagram:
            tda_features = handle_empty_diagram(resolution)
        else:
            # Vectorize
            pi_vector = vectorize_diagram_to_persistence_image(diagram, resolution=resolution)
            tda_features = {f"PI_{i}": float(val) for i, val in enumerate(pi_vector)}
            tda_features["num_features"] = len(pi_vector)
            tda_features["num_points"] = len(diagram)
            # Add summary stats
            if len(diagram) > 0:
                births = [p[0] for p in diagram]
                deaths = [p[1] for p in diagram]
                pers = [d - b for b, d in zip(births, deaths)]
                tda_features["max_persistence"] = float(max(pers))
                tda_features["mean_persistence"] = float(np.mean(pers))

        return trad_desc, tda_features

    except Exception as e:
        logger.error(f"Error processing TDA for {smiles}: {e}")
        if log_path:
            log_invalid_smiles(smiles, log_path, f"Processing error: {str(e)}")
        return trad_desc, {"tda_status": "error", "error_msg": str(e)}

def run_tda_computation(input_path: str, 
                        output_trad_path: str, 
                        output_tda_path: str,
                        resolution: int = 20,
                        log_path: Optional[str] = None) -> None:
    """
    Main orchestration function to process the entire dataset.
    Generates two CSV files: traditional descriptors and TDA features.
    """
    logger.info(f"Loading data from {input_path}")
    df = load_processed_data(input_path)
    
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        setup_invalid_smiles_logger(log_path)

    logger.info(f"Processing {len(df)} molecules with resolution {resolution}")
    
    traditional_data = []
    tda_data = []
    processed_count = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        smiles = row['smiles']
        logP = row['logP']
        
        trad_desc, tda_features = process_single_molecule(smiles, resolution, log_path)
        
        if trad_desc is None:
            skipped_count += 1
            continue

        # Prepare row for traditional CSV
        trad_row = {'smiles': smiles, 'logP': logP}
        trad_row.update(trad_desc)
        traditional_data.append(trad_row)

        # Prepare row for TDA CSV
        tda_row = {'smiles': smiles, 'logP': logP}
        if tda_features:
            tda_row.update(tda_features)
        tda_data.append(tda_row)
        
        processed_count += 1
        if processed_count % 50 == 0:
            logger.info(f"Processed {processed_count}/{len(df)} molecules")

    logger.info(f"Saving traditional descriptors to {output_trad_path}")
    df_trad = pd.DataFrame(traditional_data)
    df_trad.to_csv(output_trad_path, index=False)

    logger.info(f"Saving TDA features to {output_tda_path}")
    df_tda = pd.DataFrame(tda_data)
    df_tda.to_csv(output_tda_path, index=False)

    logger.info(f"Completed. Processed: {processed_count}, Skipped: {skipped_count}")

def run_sweep(resolutions: List[int], 
              input_path: str, 
              base_output_dir: str) -> None:
    """
    Run TDA computation for multiple resolutions to support sensitivity analysis.
    """
    base_output_dir = Path(base_output_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    for res in resolutions:
        out_trad = base_output_dir / f"traditional_res_{res}.csv"
        out_tda = base_output_dir / f"tda_res_{res}.csv"
        log_file = base_output_dir / f"log_res_{res}.log"
        
        logger.info(f"Running sweep for resolution {res}")
        run_tda_computation(
            input_path=input_path,
            output_trad_path=str(out_trad),
            output_tda_path=str(out_tda),
            resolution=res,
            log_path=str(log_file)
        )

def main():
    """Entry point for script execution."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_data = project_root / "data" / "processed" / "esol_processed.csv"
    output_trad = project_root / "data" / "processed" / "traditional_descriptors.csv"
    output_tda = project_root / "data" / "processed" / "tda_features.csv"
    log_file = project_root / "data" / "logs" / "invalid_smiles.log"
    
    # Ensure output directories exist
    output_trad.parent.mkdir(parents=True, exist_ok=True)
    output_tda.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if not input_data.exists():
        logger.error(f"Input data not found at {input_data}. Please run data ingestion first.")
        sys.exit(1)

    logger.info(f"Starting TDA computation pipeline. Input: {input_data}")
    run_tda_computation(
        input_path=str(input_data),
        output_trad_path=str(output_trad),
        output_tda_path=str(output_tda),
        resolution=20,
        log_path=str(log_file)
    )

if __name__ == "__main__":
    main()