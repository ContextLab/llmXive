import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import datasets

class DataUnavailableError(Exception):
    pass

def fetch_nist_pubchem_data(url: str) -> datasets.Dataset:
    """Fetches polymer data from NIST or PubChem."""
    try:
        dataset = datasets.load_dataset("csv", data_files=url, split="train")
        if len(dataset) < 500:
            raise DataUnavailableError(
                "CRITICAL: Real NIST/PubChem data not found. Project cannot proceed without experimental ground truth."
            )
        return dataset
    except Exception as e:
        raise DataUnavailableError(f"Failed to load dataset from {url}: {e}")

def calculate_mw(smiles: str) -> float:
    """Calculates the molecular weight of a SMILES string."""
    from rdkit import Chem
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.0  # Or raise an exception if invalid SMILES is critical
        return mol.GetMolecularWeight()
    except Exception as e:
        logging.warning(f"Error calculating MW for {smiles}: {e}")
        return 0.0

def smiles_to_polymer_graph(smiles: str) -> Dict[str, Any]:
    """Converts a SMILES string to a polymer graph representation."""
    from rdkit import Chem
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}  # Or raise an exception if invalid SMILES is critical

        # Basic node and edge features (as per FR-001)
        nodes = []
        for atom in mol.GetAtoms():
            node_features = {
                "atom_type": atom.GetSymbol(),
                "hybridization": str(atom.GetHybridization()),
            }
            nodes.append(node_features)

        edges = []
        for bond in mol.GetBonds():
            edge_features = {
                "bond_type": str(bond.GetBondType()),
            }
            edges.append(edge_features)

        graph = {
            "nodes": nodes,
            "edges": edges,
        }
        return graph
    except Exception as e:
        logging.warning(f"Error converting SMILES to graph for {smiles}: {e}")
        return {}



def process_dataset(dataset: datasets.Dataset) -> datasets.Dataset:
    """Processes the dataset, cleaning and transforming data."""
    processed_data = []
    for item in dataset:
        smiles = item.get("smiles")  # Assuming 'smiles' is a column name
        if not smiles:
            continue

        graph = smiles_to_polymer_graph(smiles)
        mw = calculate_mw(smiles)

        processed_data.append({
            "smiles": smiles,
            "graph": graph,
            "molecular_weight": mw,
        })
    return datasets.Dataset.from_list(processed_data)


def main():
    """Main function to fetch and process the dataset."""
    # Replace with actual URL or dataset name
    dataset_url = "https://raw.githubusercontent.com/rdkit/RDKit/master/Doc/examples/data/polymer_data.csv"
    try:
        dataset = fetch_nist_pubchem_data(dataset_url)
        processed_dataset = process_dataset(dataset)

        # Save checksums (placeholder - replace with actual calculation)
        checksums = {"data": "example_checksum"}  # Replace with real checksum
        with open("code/data/raw/checksums.json", "w") as f:
            import json
            json.dump(checksums, f)

        print("Data fetched and processed successfully.")

    except DataUnavailableError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # Basic logging setup
    main()