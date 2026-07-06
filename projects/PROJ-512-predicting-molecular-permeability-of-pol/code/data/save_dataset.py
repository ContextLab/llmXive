"""
Save cleaned and processed polymer dataset to HDF5 format.

This script consumes the cleaned dataset produced by the ingestion pipeline
(T010-T013) and serializes it to `data/processed/polymers.h5` in HDF5 format.
It ensures the output directory exists, handles serialization of complex
objects (PolymerGraph, PermeabilityRecord), and logs the process.
"""
import os
import sys
import logging
import h5py
import json
import numpy as np
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.ingestion import process_dataset, CleanedDataset
from data.utils import setup_logging, set_seed

logger = logging.getLogger(__name__)

OUTPUT_PATH = "data/processed/polymers.h5"

def serialize_polymer_graph(graph) -> Dict[str, Any]:
    """
    Serialize a PolymerGraph object to a dictionary suitable for HDF5 storage.
    Converts numpy arrays to lists for JSON/HDF5 compatibility.
    """
    if graph is None:
        return None

    data = {
        "smiles": graph.smiles,
        "mw": float(graph.mw) if graph.mw is not None else None,
        "permeability": graph.permeability,
        "node_features": None,
        "edge_features": None,
        "adjacency": None,
        "atom_types": None,
        "bond_types": None,
        "hybridization": None
    }

    if hasattr(graph, 'node_features') and graph.node_features is not None:
        data["node_features"] = graph.node_features.tolist()
    if hasattr(graph, 'edge_features') and graph.edge_features is not None:
        data["edge_features"] = graph.edge_features.tolist()
    if hasattr(graph, 'adjacency') and graph.adjacency is not None:
        data["adjacency"] = graph.adjacency.tolist()
    if hasattr(graph, 'atom_types') and graph.atom_types is not None:
        data["atom_types"] = graph.atom_types.tolist()
    if hasattr(graph, 'bond_types') and graph.bond_types is not None:
        data["bond_types"] = graph.bond_types.tolist()
    if hasattr(graph, 'hybridization') and graph.hybridization is not None:
        data["hybridization"] = graph.hybridization.tolist()
    
    # Serialize metadata if present
    if hasattr(graph, 'metadata') and graph.metadata:
        # Convert nested dict to JSON string if too complex for direct storage
        data["metadata_json"] = json.dumps(graph.metadata, default=str)

    return data

def save_to_hdf5(dataset: CleanedDataset, output_path: str):
    """
    Save the CleanedDataset to an HDF5 file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    logger.info(f"Saving dataset to {output_path}...")
    logger.info(f"Dataset contains {len(dataset.records)} records.")

    with h5py.File(output_path, 'w') as hf:
        # Store metadata
        meta_grp = hf.create_group("metadata")
        meta_grp.attrs["total_records"] = len(dataset.records)
        meta_grp.attrs["excluded_count"] = len(dataset.excluded) if dataset.excluded else 0
        meta_grp.attrs["small_molecule_count"] = dataset.small_molecule_count if hasattr(dataset, 'small_molecule_count') else 0
        meta_grp.attrs["version"] = "1.0"

        # Create dataset for records
        # We store each record as a JSON string in a dataset of strings
        # This is a robust way to handle variable-length structured data in HDF5
        dt = h5py.special_dtype(vlen=str)
        records_ds = hf.create_dataset("records", (len(dataset.records),), dtype=dt)

        for i, record in enumerate(dataset.records):
            serialized = serialize_polymer_graph(record)
            records_ds[i] = json.dumps(serialized, default=str)
        
        logger.info(f"Successfully saved {len(dataset.records)} records to HDF5.")

def main():
    """
    Main entry point for the save dataset script.
    """
    set_seed(42)
    setup_logging(level=logging.INFO)
    
    logger.info("Starting dataset serialization (T014)...")
    
    try:
        # Load the cleaned dataset from the previous stage (T012/T013)
        # The ingestion pipeline typically writes a temporary intermediate file
        # or we assume the process_dataset function returns the object directly.
        # Based on T010-T013 flow, we assume process_dataset returns the CleanedDataset.
        
        # Note: T010-T013 are designed to be run sequentially or via a pipeline.
        # We assume the data has been processed and is available via the ingestion module's
        # main entry or by re-running the processing logic if a cache file exists.
        # For this task, we assume the 'process_dataset' function in ingestion.py
        # is designed to return the CleanedDataset object if called with appropriate flags,
        # or we load from a temporary intermediate file if T012 wrote one.
        
        # Since T012 logs exclusions to a CSV and T013 processes graphs,
        # we assume the full pipeline up to T013 has been run and the result
        # is available. To ensure this script is standalone and runnable as per T014,
        # we will invoke the ingestion logic to fetch and process the data
        # if a pre-processed cache isn't strictly required by the spec to be separate.
        # However, to respect the pipeline flow, we assume the data is already
        # in memory or we re-run the fetch+process step here to guarantee
        # the output file is generated from real data as per FR-001.
        
        # Re-running the full ingestion pipeline to ensure data freshness and
        # compliance with "real data only" constraint.
        logger.info("Fetching and processing dataset from source...")
        cleaned_data = process_dataset()
        
        if not cleaned_data or not cleaned_data.records:
            logger.error("No data processed. Aborting save.")
            sys.exit(1)

        save_to_hdf5(cleaned_data, OUTPUT_PATH)
        
        logger.info(f"Task T014 completed successfully. Output: {OUTPUT_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to save dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()