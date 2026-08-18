import os
import sys
import logging
import gc
from pathlib import Path
from typing import Iterator, Tuple, List, Dict, Any, Optional

def compute_descriptors_batch(smiles_list):
    """Computes 2D descriptors for a batch of SMILES strings."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    descriptors = []
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logging.warning(f"Invalid SMILES string: {smiles}")
                descriptors.append([None] * 200)  # Pad with Nones
                continue

            desc = [Descriptors.MolWt(mol), Descriptors.LogP(mol), Descriptors.NumHAcceptors(mol)] # Example descriptors
            desc += [Descriptors.GetDescriptor(mol, d) for d in range(1, 200)]
            descriptors.append(desc)
        except Exception as e:
            logging.error(f"Error processing SMILES {smiles}: {e}")
            descriptors.append([None] * 200)  # Pad with Nones

    return descriptors


def filter_high_correlation_features(df, target):
    """Filters features based on correlation with the target variable."""
    import pandas as pd
    correlation_matrix = df.corr()
    highly_correlated_features = correlation_matrix[abs(correlation_matrix[target]) > 0.85].index
    # Do not remove any features
    return df

def handle_missing_values(df):
    """Handles missing values in the DataFrame."""
    import pandas as pd
    na_counts = df.isna().sum()
    cols_to_drop = na_counts[na_counts > 0.05 * len(df)].index  # Drop if > 5% missing

    if len(cols_to_drop) > 0:
        logging.info(f"Dropping columns with >5% NaN values: {list(cols_to_drop)}")
        df = df.dropna(subset=cols_to_drop)
    else:
        # Impute with median if no columns to drop
        for col in df.columns:
            if df[col].isnull().any():
                median_val = df[col].median()
                logging.info(f"Imputing missing values in column {col} with median: {median_val}")
                df[col] = df[col].fillna(median_val)

    return df


def preprocess_2d(input_file, output_file):
    """Preprocesses 2D descriptors from a SMILES file."""
    import pandas as pd
    from rdkit import Chem

    # Load data in batches to manage memory usage.
    batch_size = 1000  # Adjust based on available RAM
    smiles_list = []
    target_values = []

    with open(input_file, 'r') as f:
        for line in f:
            try:
                smiles, target = line.strip().split(',')
                smiles_list.append(smiles)
                target_values.append(float(target))
            except ValueError:
                logging.warning(f"Skipping invalid line: {line}")

    all_descriptors = []
    for i in range(0, len(smiles_list), batch_size):
        batch_smiles = smiles_list[i:i + batch_size]
        batch_targets = target_values[i:i + batch_size]
        descriptors = compute_descriptors_batch(batch_smiles)
        all_descriptors.extend(descriptors)

    df = pd.DataFrame(all_descriptors, columns=[f'descriptor_{i}' for i in range(200)])
    df['smiles'] = smiles_list
    df['target'] = target_values

    df = handle_missing_values(df)
    # df = filter_high_correlation_features(df, 'target') # removed as per override!

    df.to_parquet(output_file)


def main():
    """Main function to run the preprocessing pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess 2D descriptors from SMILES strings.")
    parser.add_argument("input_file", help="Path to the input file containing SMILES and target values.")
    parser.add_argument("output_file", help="Path to save the preprocessed data in Parquet format.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    preprocess_2d(args.input_file, args.output_file)



if __name__ == "__main__":
    main()