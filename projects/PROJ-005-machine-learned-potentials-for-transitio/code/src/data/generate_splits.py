import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

def load_graphs_for_splitting(graph_path: str) -> pd.DataFrame:
    """Loads graphs from a Parquet file."""
    try:
        graphs = pd.read_parquet(graph_path)
        return graphs
    except FileNotFoundError:
        logging.error(f"Graph file not found: {graph_path}")
        return pd.DataFrame()

def compute_scaffold_clusters(graphs: pd.DataFrame) -> Dict[str, List[int]]:
    """Computes scaffold clusters from a DataFrame of graphs."""
    scaffold_clusters = {}
    for index, row in graphs.iterrows():
        try:
            smiles = row['smiles']  # Assuming 'smiles' column exists
            if smiles not in scaffold_clusters:
                scaffold_clusters[smiles] = []
            scaffold_clusters[smiles].append(index)
        except KeyError:
            logging.warning(f"Smiles column not found in graph {index}")
    return scaffold_clusters

def generate_llso_splits(scaffold_clusters: Dict[str, List[int]], num_folds: int = 5) -> List[Tuple[List[int], List[int]]]:
    """Generates Leave-Ligand-Scaffold-Out splits."""
    scaffolds = list(scaffold_clusters.keys())
    np.random.seed(42)
    np.random.shuffle(scaffolds)
    fold_size = len(scaffolds) // num_folds
    splits = []
    for i in range(num_folds):
        start = i * fold_size
        end = (i + 1) * fold_size
        test_scaffolds = scaffolds[start:end]
        train_scaffolds = scaffolds[:start] + scaffolds[end:]
        test_indices = []
        train_indices = []
        for scaffold in test_scaffolds:
            test_indices.extend(scaffold_clusters[scaffold])
        for scaffold in train_scaffolds:
            train_indices.extend(scaffold_clusters[scaffold])
        splits.append((train_indices, test_indices))
    return splits

def save_splits_to_json(splits: List[Tuple[List[int], List[int]]], output_path: str):
    """Saves the splits to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(splits, f)

def run_split_generation(graph_path: str, output_path: str):
    """Runs the entire split generation process."""
    graphs = load_graphs_for_splitting(graph_path)
    if graphs.empty:
        logging.error("No graphs loaded. Exiting.")
        return
    scaffold_clusters = compute_scaffold_clusters(graphs)
    splits = generate_llso_splits(scaffold_clusters)
    save_splits_to_json(splits, output_path)
    logging.info(f"Splits saved to {output_path}")

def generate_splits():
    """Main function to generate splits."""
    graph_path = "code/data/processed/graphs.parquet"
    output_path = "code/data/processed/splits.json"
    run_split_generation(graph_path, output_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    generate_splits()