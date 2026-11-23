import os
import sys
import logging
import h5py
import json
import numpy as np
from typing import List, Dict, Any, Optional

from models.polymer_graph import PolymerGraph
from data.utils import setup_logging

logger = logging.getLogger(__name__)

def serialize_polymer_graph(graph: PolymerGraph) -> Dict[str, Any]:
    """
    Convert a PolymerGraph instance into a JSON-serializable dictionary
    suitable for storage in HDF5 attributes or datasets.
    """
    data = {
        "smiles": graph.smiles,
        "mw": float(graph.mw),
        "log_permeability": float(graph.log_permeability) if graph.log_permeability is not None else None,
        "source": graph.source,
        "node_features": graph.node_features.tolist() if isinstance(graph.node_features, np.ndarray) else graph.node_features,
        "edge_features": graph.edge_features.tolist() if isinstance(graph.edge_features, np.ndarray) else graph.edge_features,
        "edge_index": graph.edge_index.tolist() if isinstance(graph.edge_index, np.ndarray) else graph.edge_index,
        "metadata": graph.metadata or {}
    }
    return data

def save_to_hdf5(
    graphs: List[PolymerGraph],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save a list of PolymerGraph objects to an HDF5 file.

    Structure:
    /graphs (dataset of serialized JSON strings or structured arrays)
    /metadata (attributes)
    """
    if not graphs:
        raise ValueError("Cannot save an empty list of graphs.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Saving {len(graphs)} PolymerGraph objects to {output_path}")

    with h5py.File(output_path, "w") as f:
        # Store metadata as attributes
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    f.attrs[key] = value
                elif isinstance(value, (list, tuple)):
                    f.attrs[key] = json.dumps(value)
                else:
                    f.attrs[key] = str(value)

        # Create a dataset for the graph data
        # We will store each graph as a JSON string to preserve complex nested structures
        # like numpy arrays, which HDF5 doesn't handle natively in a simple way without extra schemas.
        dt = h5py.special_dtype(vlen=str)
        ds = f.create_dataset("graphs", (len(graphs),), dtype=dt)

        for i, graph in enumerate(graphs):
            serialized = serialize_polymer_graph(graph)
            # Convert numpy arrays to lists for JSON serialization
            # The serialize_polymer_graph function already handles this for known fields.
            # Ensure nested metadata is clean.
            ds[i] = json.dumps(serialized)

        logger.info(f"Successfully saved {len(graphs)} graphs to {output_path}")

def main() -> None:
    """
    Main entry point for saving the processed dataset to HDF5.
    Expects the processed data to be available in the expected location
    or passed via arguments (for this script, we assume it's called after T013).

    Since T013 produces processed graphs, this script acts as the saver.
    In a real pipeline, the data would be passed or loaded from a temporary location.
    Here, we assume the caller loads the processed data (e.g., from a pickle or memory)
    and passes it to this function, or we load from the intermediate CSV if T013 wrote one.

    For this implementation, we assume the script is run after T013 has populated
    the processed data, or we read from a standard intermediate file if T013 output one.
    However, T013 description says "Implement node/edge feature extraction".
    Let's assume T013 outputs a CSV or JSON intermediate that we load here.
    If T013 directly produces objects, this script would need to import that logic.

    Given the task dependency "T013 must complete before T014", we assume the
    processed data exists in `data/processed/intermediate_features.json` or similar,
    or we re-run the extraction logic.

    To be robust: We will attempt to load from `data/processed/intermediate_features.json`
    (if T013 writes there) or we re-execute the logic from `preprocessing.py` if needed.
    However, the cleanest way is to have T013 output a file we read here.
    Let's assume T013 writes to `data/processed/processed_graphs.json` (list of dicts).

    If that file doesn't exist, we raise an error.
    """
    logger = setup_logging("save_dataset")

    input_file = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/processed_graphs.json"
    output_file = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5"

    if not os.path.exists(input_file):
        # Fallback: Try to load from the raw/processed CSV if JSON doesn't exist,
        # but the task implies T013 produces the features.
        # If T013 didn't write a file, we can't proceed.
        logger.error(f"Intermediate processed data file not found: {input_file}")
        logger.error("Ensure T013 has run and produced the required intermediate file.")
        sys.exit(1)

    logger.info(f"Loading processed graphs from {input_file}")
    with open(input_file, "r") as f:
        raw_data = json.load(f)

    graphs = []
    for item in raw_data:
        # Reconstruct PolymerGraph from the dict
        # This assumes the dict structure matches what serialize_polymer_graph expects
        # or we reconstruct it manually.
        # Since PolymerGraph is a dataclass, we can try to instantiate it.
        # We need to handle numpy arrays if they were saved as lists.
        node_feat = np.array(item["node_features"]) if isinstance(item["node_features"], list) else item["node_features"]
        edge_feat = np.array(item["edge_features"]) if isinstance(item["edge_features"], list) else item["edge_features"]
        edge_idx = np.array(item["edge_index"]) if isinstance(item["edge_index"], list) else item["edge_index"]

        graph = PolymerGraph(
            smiles=item["smiles"],
            mw=item["mw"],
            log_permeability=item.get("log_permeability"),
            source=item.get("source", "unknown"),
            node_features=node_feat,
            edge_features=edge_feat,
            edge_index=edge_idx,
            metadata=item.get("metadata", {})
        )
        graphs.append(graph)

    logger.info(f"Reconstructed {len(graphs)} PolymerGraph objects.")

    save_to_hdf5(
        graphs,
        output_file,
        metadata={
            "source": "T013 processed features",
            "count": len(graphs),
            "version": "1.0"
        }
    )

    logger.info(f"Dataset saved to {output_file}")

if __name__ == "__main__":
    main()