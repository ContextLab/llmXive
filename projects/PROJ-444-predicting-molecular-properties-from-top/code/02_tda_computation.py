import os
import sys
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix, diags
import networkx as nx

from utils.graph_builder import build_molecular_graph, get_molecular_weight, log_invalid_smiles, is_valid_molecule
from utils.persistence_utils import compute_shortest_path_matrix, build_shortest_path_filtration, compute_persistence_diagram, handle_empty_diagram, compute_betti_numbers, get_topological_features

def generate_tda_features_csv(data_path, output_path_tda, output_path_descriptors):
    """
    Generates TDA features and traditional descriptors for a given dataset.
    """

    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logging.error(f"File not found: {data_path}")
        return

    smiles_list = df['smiles'].tolist()
    logp_list = df['logP'].tolist()

    tda_features = []
    traditional_descriptors = []

    for smiles, logp in zip(smiles_list, logp_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                log_invalid_smiles(smiles)
                continue

            if not is_valid_molecule(mol):
                log_invalid_smiles(smiles)
                continue

            graph = build_molecular_graph(mol)
            if graph is None:
                continue

            weight_matrix = compute_shortest_path_matrix(graph)
            if weight_matrix is None:
                continue

            filtration = build_shortest_path_filtration(weight_matrix)

            try:
                diagrams = compute_persistence_diagram(filtration)
                betti_numbers = compute_betti_numbers(diagrams)
                topological_features = get_topological_features(diagrams)
            except Exception as e:
                logging.error(f"Error computing TDA features for {smiles}: {e}")
                topological_features = [0.0] * 10  # Zero vector fallback

            traditional_descriptor = [logp, get_molecular_weight(mol)]

            tda_features.append(topological_features)
            traditional_descriptors.append(traditional_descriptor)

        except Exception as e:
            logging.error(f"Error processing {smiles}: {e}")
            continue

    tda_df = pd.DataFrame(tda_features)
    traditional_df = pd.DataFrame(traditional_descriptors, columns=['logP', 'MolecularWeight'])

    tda_df.to_csv(output_path_tda, index=False)
    traditional_df.to_csv(output_path_descriptors, index=False)
    logging.info(f"TDA features saved to {output_path_tda}")
    logging.info(f"Traditional descriptors saved to {output_path_descriptors}")
