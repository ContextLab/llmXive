import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

def calculate_ecfp_correlation(df, fp_length=2048):
    """Calculates Pearson correlation between ECFP fingerprints."""
    fps = [AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(smi), fp_length) for smi in df['smi']]
    fps_array = np.array(fps)
    correlation_matrix = np.corrcoef(fps_array)
    return correlation_matrix

def calculate_gnn_similarity(df, embeddings):
    """Calculates cosine similarity between GNN embeddings."""
    # Assuming embeddings are already calculated and available in df
    embeddings_array = np.array(embeddings)
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(embeddings_array)
    return similarity_matrix

def check_collinearity(df, correlation_threshold=0.9):
    """Checks for collinearity based on correlation threshold."""
    correlation_matrix = calculate_ecfp_correlation(df)
    flags = []
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if abs(correlation_matrix[i, j]) >= correlation_threshold:
                flags.append((i, j))  # Store indices of collinear features
    return flags

def check_gnn_similarity(df, embeddings, similarity_threshold=0.9):
    """Checks for high GNN embedding similarity."""
    similarity_matrix = calculate_gnn_similarity(df, embeddings)
    flags = []
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if abs(similarity_matrix[i, j]) >= similarity_threshold:
                flags.append((i, j))  # Store indices of similar features
    return flags

def main():
    """Main function to calculate collinearity and GNN similarity."""
    logger = logging.getLogger(__name__)
    data_path = Path("data/processed/train.csv")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        sys.exit(1)
    
    # Placeholder for GNN embeddings - replace with actual values from model output
    gnn_embeddings = [np.random.rand(128) for _ in range(len(df))]  

    ecfp_collinearity_flags = check_collinearity(df)
    gnn_similarity_flags = check_gnn_similarity(df, gnn_embeddings)

    redundancy_masks = {}
    for i in range(len(df)):
        mask = [0] * len(df['smi'])  # Initialize mask with zeros
        # Mark features as redundant based on collinearity and similarity flags
        for col1, col2 in ecfp_collinearity_flags:
            if col1 == i or col2 == i:
                mask[i] = 1
        for col1, col2 in gnn_similarity_flags:
            if col1 == i or col2 == i:
                mask[i] = 1

        redundancy_masks[i] = mask

    output_path = Path("data/processed/redundancy_masks.json")
    with open(output_path, "w") as f:
        json.dump(redundancy_masks, f)

    logger.info(f"Redundancy masks saved to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()