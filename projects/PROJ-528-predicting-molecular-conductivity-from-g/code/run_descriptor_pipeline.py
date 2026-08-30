import os
import sys
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from rdkit import Chem
from rdkit.Chem import AllChem
from code.config import DATA_PATH
from code.descriptors import compute_degree_statistics, compute_path_length_statistics, compute_ring_count, compute_huckel_aromaticity_index, compute_aromatic_ring_count, compute_bond_order_annotation, compute_bond_polarity, compute_resonance_energy
from code.error_handler import validate_smiles_batch, check_conductivity_column, handle_invalid_smiles, handle_missing_conductivity

def load_smiles_from_file(filepath: str) -> pd.DataFrame:
    """Loads SMILES strings from a CSV file and performs basic validation."""
    try:
        df = pd.read_csv(filepath)
        df['valid'] = df['smiles'].apply(lambda x: validate_smiles_batch([x])[0])
        df['error_msg'] = df['smiles'].apply(lambda x: handle_invalid_smiles(x))
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return pd.DataFrame()

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
  """Cleans the dataframe by removing invalid SMILES and handling missing values."""
  df = df[df['valid']]  # Keep only valid SMILES
  return df
      

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    smiles_file = os.path.join(DATA_PATH, 'raw', 'molecules.csv')  # Assuming molecules.csv is in data/raw

    df = load_smiles_from_file(smiles_file)
    if df.empty:
        logging.error("No valid SMILES found.")
        sys.exit(1)

    df = clean_dataframe(df)

    # Compute descriptors
    try:
      degree_stats = compute_degree_statistics(df['smiles'])
      path_length_stats = compute_path_length_statistics(df['smiles'])
      ring_counts = compute_ring_count(df['smiles'])
      aromaticity_indices = compute_huckel_aromaticity_index(df['smiles'])
      aromatic_ring_counts = compute_aromatic_ring_count(df['smiles'])
      bond_order_annotations = compute_bond_order_annotation(df['smiles'])
      bond_polarities = compute_bond_polarity(df['smiles'])
      resonance_energies = compute_resonance_energy(df['smiles'])

    except Exception as e:
        logging.error(f"Error computing descriptors: {e}")
        sys.exit(1)


    # Create the final DataFrame with all descriptors
    descriptor_data = {
        'smiles': df['smiles'],
        'status': 'computed',  # Assuming successful computation
        'degree_mean': degree_stats['mean'],
        'degree_std': degree_stats['std'],
        'degree_max': degree_stats['max'],
        'degree_min': degree_stats['min'],
        'path_length_mean': path_length_stats['mean'],
        'path_length_std': path_length_stats['std'],
        'path_length_max': path_length_stats['max'],
        'path_length_min': path_length_stats['min'],
        'aromaticity_index': aromaticity_indices,
        'conjugation_length': aromatic_ring_counts,  # Using ring count as proxy for conjugation length
        'ring_count': ring_counts,
        'bond_polarity': bond_polarities,
        'resonance_energy': resonance_energies
    }

    descriptors_df = pd.DataFrame(descriptor_data)

    # Save to CSV
    output_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    try:
        descriptors_df.to_csv(output_path, index=False)
        logging.info(f"Descriptors saved to {output_path}")
    except Exception as e:
        logging.error(f"Error saving descriptors to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()