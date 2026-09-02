import os
import sys
import logging
import json
import math
from pathlib import Path
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from typing import List, Dict, Any, Optional

from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CURATED_DATA_PATH = Path("data/curated/curated_dataset.csv")
OUTPUT_PATH = Path("data/curated/curated_dataset.csv") # Overwrite with processed version if needed

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned and validated curated dataset."""
    if not CURATED_DATA_PATH.exists():
        raise DataError(f"Curated dataset not found at {CURATED_DATA_PATH}. Run clean.py first.")
    return pd.read_csv(CURATED_DATA_PATH)

def compute_graph_properties(smiles: str) -> Dict[str, Any]:
    """
    Compute basic graph properties for a SMILES string.
    Returns degree, density, clustering coefficient.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            'degree': 0,
            'density': 0.0,
            'clustering': 0.0
        }
    
    # Get number of atoms and bonds
    num_atoms = mol.GetNumAtoms()
    num_bonds = mol.GetNumBonds()
    
    if num_atoms < 2:
        return {
            'degree': 0,
            'density': 0.0,
            'clustering': 0.0
        }
    
    # Average Degree = 2 * num_bonds / num_atoms
    avg_degree = (2 * num_bonds) / num_atoms
    
    # Graph Density = 2 * num_bonds / (num_atoms * (num_atoms - 1))
    max_bonds = num_atoms * (num_atoms - 1) / 2
    density = (num_bonds / max_bonds) if max_bonds > 0 else 0.0
    
    # Clustering Coefficient (Average local clustering)
    # RDKit doesn't have a direct 'clustering coefficient' for the whole graph,
    # but we can approximate or use a related metric.
    # For this task, we will use a simplified metric or 0 if not directly available.
    # A common proxy is the transitivity or average local clustering.
    # Since RDKit doesn't expose this directly in a single call for the whole graph,
    # we will calculate a simple approximation or set to 0 if complex.
    # However, for T018 we need 'clustering'. We can calculate it manually or use a library.
    # Given constraints, we'll use a simple heuristic or skip if not easily available.
    # Let's try to calculate average local clustering coefficient.
    # This requires iterating over neighbors, which is O(N^2) or O(N*E).
    # For small molecules, this is fine.
    
    clustering_sum = 0.0
    count = 0
    for atom in mol.GetAtoms():
        neighbors = [a.GetIdx() for a in atom.GetNeighbors()]
        k = len(neighbors)
        if k < 2:
            continue
        
        # Count edges between neighbors
        edges_between = 0
        for i in range(k):
            for j in range(i + 1, k):
                n1 = neighbors[i]
                n2 = neighbors[j]
                # Check if bond exists
                bond = mol.GetBondBetweenAtoms(n1, n2)
                if bond is not None:
                    edges_between += 1
        
        max_edges = k * (k - 1) / 2
        if max_edges > 0:
            clustering_sum += edges_between / max_edges
            count += 1
    
    avg_clustering = clustering_sum / count if count > 0 else 0.0

    return {
        'degree': avg_degree,
        'density': density,
        'clustering': avg_clustering
    }

def generate_curated_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate the final curated dataset with graph properties.
    For T017, we just need to ensure the schema is correct and valid.
    The properties are calculated in T018, but we can do a sanity check here.
    """
    # Validate schema
    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    if not all(col in df.columns for col in required_cols):
        raise DataError(f"Curated dataset missing required columns: {required_cols}")
    
    # Ensure types
    df['polymer_smiles'] = df['polymer_smiles'].astype(str)
    df['filler_smiles'] = df['filler_smiles'].astype(str)
    df['adhesion_energy'] = pd.to_numeric(df['adhesion_energy'], errors='coerce')
    
    # Drop rows with invalid SMILES or energy (already done in clean.py, but double check)
    df = df.dropna(subset=['polymer_smiles', 'filler_smiles', 'adhesion_energy'])
    
    # Validate row count
    if len(df) < 100:
        raise DataError(f"Curated dataset has {len(df)} rows, less than required 100.")
    
    # Validate missing values
    missing_pct = df.isnull().mean() * 100
    if (missing_pct > 5.0).any():
        raise DataError(f"Curated dataset has columns with >5% missing values.")
    
    return df

def main():
    """Main entry point for generating curated dataset."""
    try:
        # Load cleaned data
        df = load_cleaned_data()
        logger.info(f"Loaded {len(df)} rows from {CURATED_DATA_PATH}")
        
        # Generate/validate curated dataset
        df_curated = generate_curated_dataset(df)
        
        # Save to output path (overwrite to ensure it's the final version)
        df_curated.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Saved final curated dataset to {OUTPUT_PATH} with {len(df_curated)} rows.")
        
        logger.info("Curated dataset generation completed successfully.")
        
    except DataError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()