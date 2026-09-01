import os
import pandas as pd
from typing import List, Dict, Any, Optional
from rdkit import Chem
from code.config import DATA_PATH
from code.descriptors import compute_degree_statistics, compute_path_length_statistics, compute_ring_count, compute_huckel_aromaticity_index, compute_aromatic_ring_count, compute_bond_order_annotation, compute_bond_polarity, compute_resonance_energy
import logging

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """Loads SMILES strings from a CSV file and validates them."""
    try:
        df = pd.read_csv(path)
        df['smiles'] = df['smiles'].astype(str)
        df['valid'] = df['smiles'].apply(lambda x: True if Chem.MolFromSmiles(x) is not None else False)
        df['error_msg'] = df['smiles'].apply(lambda x: '' if df['valid'][df.index == df.index[df['smiles'] == x]].iloc[0] else 'Invalid SMILES')
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading SMILES from file: {e}")
        return pd.DataFrame()

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Filters out invalid SMILES from the DataFrame."""
    df = df[df['valid']]
    return df

def main():
    """Main function to load SMILES, compute descriptors, and save to CSV."""
    input_file = os.path.join(DATA_PATH, 'raw', 'molecules.csv')
    output_file = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    smiles_df = load_smiles_from_file(input_file)
    if smiles_df.empty:
        logging.error("No valid SMILES found. Exiting.")
        return

    smiles_df = clean_dataframe(smiles_df)
    if smiles_df.empty:
        logging.error("No valid SMILES after cleaning. Exiting.")
        return

    # Compute descriptors
    smiles_list = smiles_df['smiles'].tolist()
    degree_stats = compute_degree_statistics(smiles_list)
    path_length_stats = compute_path_length_statistics(smiles_list)
    ring_counts = compute_ring_count(smiles_list)
    aromaticity_indices = compute_huckel_aromaticity_index(smiles_list)
    conjugation_lengths = compute_aromatic_ring_count(smiles_list)
    bond_order_annotations = compute_bond_order_annotation(smiles_list)
    bond_polarities = compute_bond_polarity(smiles_list)
    resonance_energies = compute_resonance_energy(smiles_list)

    # Create a new DataFrame with the computed descriptors
    descriptors_data = {
        'smiles': smiles_df['smiles'],
        'status': 'success',
        'degree_mean': degree_stats[0],
        'degree_std': degree_stats[1],
        'degree_max': degree_stats[2],
        'degree_min': degree_stats[3],
        'path_length_mean': path_length_stats[0],
        'path_length_std': path_length_stats[1],
        'path_length_max': path_length_stats[2],
        'path_length_min': path_length_stats[3],
        'aromaticity_index': aromaticity_indices,
        'conjugation_length': conjugation_lengths,
        'ring_count': ring_counts,
        'bond_polarity': bond_polarities,
        'resonance_energy': resonance_energies
    }
    descriptors_df = pd.DataFrame(descriptors_data)

    # Save the DataFrame to CSV
    try:
        descriptors_df.to_csv(output_file, index=False)
        logging.info(f"Descriptors saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving descriptors to CSV: {e}")

if __name__ == "__main__":
    main()