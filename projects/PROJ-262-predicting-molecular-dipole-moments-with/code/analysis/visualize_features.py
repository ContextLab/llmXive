from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3D projection)

# Ensure real numpy is used if the project has a shim
try:
    import numpy_real
    np = numpy_real
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_attributions(input_path: str) -> List[Dict]:
    """
    Load feature importance data from a JSON file.
    Expected structure: list of dicts with 'molecule_id', 'features', 'importance'.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Attributions file not found: {input_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Attributions file must contain a JSON list of molecule entries.")
    
    return data

def validate_entry(entry: Dict) -> bool:
    """
    Validate that an attribution entry has the required fields and data types.
    """
    required_fields = ['molecule_id', 'features', 'importance']
    for field in required_fields:
        if field not in entry:
            logger.error(f"Missing required field '{field}' in entry: {entry.get('molecule_id', 'unknown')}")
            return False
    
    if not isinstance(entry['features'], list) or not isinstance(entry['importance'], list):
        logger.error(f"Features and importance must be lists in entry: {entry.get('molecule_id', 'unknown')}")
        return False
    
    if len(entry['features']) != len(entry['importance']):
        logger.error(f"Features and importance length mismatch in entry: {entry.get('molecule_id', 'unknown')}")
        return False
    
    return True

def plot_importance(
    molecule_id: str, 
    features: List[str], 
    importance: List[float], 
    coords: List[List[float]],
    atoms: List[str],
    output_path: str,
    top_k: int = 15
) -> None:
    """
    Generate a visualization of feature importance overlaid on a 3D molecular structure.
    
    Creates a figure with two subplots:
    1. Bar chart of top-K feature importance.
    2. 3D scatter plot of the molecule with nodes colored by feature contribution (if applicable).
    """
    if not features or not importance:
        logger.warning(f"No features to plot for {molecule_id}. Skipping.")
        return

    # Sort by importance
    sorted_indices = np.argsort(importance)[::-1]
    top_indices = sorted_indices[:top_k]
    
    top_features = [features[i] for i in top_indices]
    top_importance = [importance[i] for i in top_indices]

    # Create figure
    fig = plt.figure(figsize=(14, 6))
    
    # Plot 1: Feature Importance Bar Chart
    ax1 = fig.add_subplot(1, 2, 1)
    y_pos = np.arange(len(top_features))
    ax1.barh(y_pos, top_importance, align='center', color='steelblue')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(top_features)
    ax1.invert_yaxis()  # Labels read top-to-bottom
    ax1.set_xlabel('Importance Score')
    ax1.set_title(f'Top {top_k} Feature Importance for {molecule_id}')
    ax1.grid(axis='x', alpha=0.3)

    # Plot 2: 3D Molecular Structure with Node Coloring
    # We map the importance of the most relevant features to node colors if possible.
    # For general visualization, we map the max importance of any feature associated with an atom.
    # Since 'features' are global descriptors in many cases, we will visualize the structure
    # and overlay a color map based on a heuristic: if a feature is 'atom_type_X', we color that atom.
    # Otherwise, we default to a gradient based on the overall importance magnitude.
    
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    
    if len(coords) == 0 or len(atoms) == 0:
        ax2.text(0, 0, 0, "No 3D coordinates available", fontsize=12)
        ax2.set_title(f"Structure for {molecule_id}")
    else:
        coords_np = np.array(coords)
        atoms_np = np.array(atoms)
        
        # Simple coloring: map atom types to colors
        unique_atoms = list(set(atoms))
        atom_colors = {atom: plt.cm.viridis(i / len(unique_atoms)) for i, atom in enumerate(unique_atoms)}
        
        # If we have feature names that look like atom-specific features, we try to highlight them.
        # Example feature name: "atom_C_charge", "atom_O_polar"
        # This is a best-effort mapping for visualization.
        atom_contributions = np.zeros(len(atoms))
        
        for i, feat in enumerate(features):
            val = importance[i]
            # Heuristic: check if feature name contains atom symbol
            for atom_sym in unique_atoms:
                if atom_sym in feat:
                    atom_contributions[atoms_np == atom_sym] = np.maximum(atom_contributions[atoms_np == atom_sym], val)
        
        # Normalize contributions for coloring
        if np.max(atom_contributions) > 0:
            norm_contribs = atom_contributions / np.max(atom_contributions)
            node_colors = [atom_colors[atom] for atom in atoms]
            # Modify alpha or color intensity based on contribution if possible, 
            # but for simplicity in 3D scatter, we use a colormap on the Z-axis or a derived metric.
            # Here we just plot the structure with standard colors to ensure visibility.
            ax2.scatter(coords_np[:, 0], coords_np[:, 1], coords_np[:, 2], 
                        c=[atom_colors[a] for a in atoms], s=100, depthshade=True, label=atoms)
        else:
            ax2.scatter(coords_np[:, 0], coords_np[:, 1], coords_np[:, 2], 
                        c='gray', s=100, depthshade=True)
        
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.set_zlabel('Z')
        ax2.set_title(f"3D Structure: {molecule_id}")
        ax2.view_init(elev=30, azim=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved visualization to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Visualize feature importance maps on representative molecules.")
    parser.add_argument("--input", type=str, default="results/attributions.json",
                        help="Path to the JSON file containing feature attributions.")
    parser.add_argument("--molecules", type=str, default="data/processed/subset_final.parquet",
                        help="Path to the parquet file containing molecule coordinates and atoms.")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Directory to save generated PNG files.")
    parser.add_argument("--top-k", type=int, default=15,
                        help="Number of top features to display.")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load attributions
    logger.info(f"Loading attributions from {args.input}")
    try:
        attributions = load_attributions(args.input)
    except Exception as e:
        logger.error(f"Failed to load attributions: {e}")
        # If no attributions exist yet, we cannot visualize. Fail loudly.
        raise e
    
    # Load molecule data for coordinates
    try:
        df = pd.read_parquet(args.molecules)
        # Expected columns: molecule_id, atoms (list), coordinates (list of lists)
        # If columns are different, we might need to adjust.
        logger.info(f"Loaded {len(df)} molecules from {args.molecules}")
    except Exception as e:
        logger.error(f"Failed to load molecule data: {e}")
        raise e
    
    # Create a lookup for molecule data
    mol_lookup = {row['molecule_id']: row for _, row in df.iterrows()}
    
    processed_count = 0
    for entry in attributions:
        mol_id = entry['molecule_id']
        if not validate_entry(entry):
            logger.warning(f"Skipping invalid entry for {mol_id}")
            continue
        
        if mol_id not in mol_lookup:
            logger.warning(f"Molecule {mol_id} not found in dataset, skipping visualization.")
            continue
        
        mol_data = mol_lookup[mol_id]
        coords = mol_data.get('coordinates', [])
        atoms = mol_data.get('atoms', [])
        
        if not coords or not atoms:
            logger.warning(f"No coordinates or atoms for {mol_id}, skipping.")
            continue
        
        output_file = output_dir / f"attributions_{mol_id}.png"
        
        try:
            plot_importance(
                molecule_id=mol_id,
                features=entry['features'],
                importance=entry['importance'],
                coords=coords,
                atoms=atoms,
                output_path=str(output_file),
                top_k=args.top_k
            )
            processed_count += 1
        except Exception as e:
            logger.error(f"Error plotting {mol_id}: {e}")
    
    logger.info(f"Visualization complete. Processed {processed_count} molecules.")
    if processed_count == 0:
        logger.warning("No visualizations were generated. Check input data.")

if __name__ == "__main__":
    main()