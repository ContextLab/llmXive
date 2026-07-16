import os
import sys
import logging
import h5py
import json
import numpy as np
from typing import List, Dict, Any, Optional

# Import from existing API surface
from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord
from data.utils import setup_logging

logger = logging.getLogger(__name__)

def serialize_polymer_graph(graph: PolymerGraph) -> Dict[str, Any]:
    """
    Serializes a PolymerGraph object into a dictionary suitable for HDF5 storage.
    Extracts node features, edge features, and metadata.
    """
    if not hasattr(graph, 'nodes') or not hasattr(graph, 'edges'):
        raise ValueError("Invalid PolymerGraph: missing nodes or edges")

    node_features = []
    for node_id, node_data in graph.nodes.items():
        # Ensure all feature arrays are numpy arrays for HDF5 compatibility
        features = {}
        for key, value in node_data.items():
            if isinstance(value, (list, np.ndarray)):
                features[key] = np.array(value, dtype=np.float32)
            else:
                features[key] = value
        node_features.append({
            'id': node_id,
            'features': features
        })

    edge_features = []
    for edge_data in graph.edges:
        features = {}
        for key, value in edge_data.items():
            if isinstance(value, (list, np.ndarray)):
                features[key] = np.array(value, dtype=np.float32)
            else:
                features[key] = value
        edge_features.append(features)

    return {
        'nodes': node_features,
        'edges': edge_features,
        'metadata': {
            'smiles': graph.metadata.get('smiles', ''),
            'molecular_weight': graph.metadata.get('molecular_weight', 0.0),
            'repeat_unit': graph.metadata.get('repeat_unit', ''),
            'source': graph.metadata.get('source', 'unknown')
        }
    }

def save_to_hdf5(graphs: List[PolymerGraph], output_path: str) -> None:
    """
    Saves a list of PolymerGraph objects to an HDF5 file.
    Structure:
    /dataset
      /graphs
        /0, /1, ... (groups for each graph)
          /nodes (dataset of serialized nodes)
          /edges (dataset of serialized edges)
          /metadata (attributes)
    /stats (attributes: count, avg_mw, etc.)
    """
    if not graphs:
        raise ValueError("No graphs provided to save.")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving {len(graphs)} graphs to {output_path}")

    with h5py.File(output_path, 'w') as f:
        # Create a group for the dataset
        ds = f.create_group('dataset')
        
        # Create a group for graphs
        graphs_group = ds.create_group('graphs')
        
        # Create a group for metadata/stats
        stats_group = ds.create_group('stats')
        
        total_mw = 0.0
        count = 0

        for i, graph in enumerate(graphs):
            serialized = serialize_polymer_graph(graph)
            
            grp = graphs_group.create_group(str(i))
            
            # Save nodes
            # We store nodes as a structured dataset or JSON string for simplicity
            # Given variable node counts, JSON string is safer for variable length
            nodes_json = json.dumps(serialized['nodes'])
            grp.create_dataset('nodes_json', data=nodes_json, dtype=h5py.string_dtype())
            
            # Save edges
            edges_json = json.dumps(serialized['edges'])
            grp.create_dataset('edges_json', data=edges_json, dtype=h5py.string_dtype())
            
            # Save metadata as attributes
            grp.attrs['smiles'] = serialized['metadata']['smiles']
            mw = float(serialized['metadata']['molecular_weight'])
            grp.attrs['molecular_weight'] = mw
            total_mw += mw
            count += 1
            grp.attrs['repeat_unit'] = serialized['metadata']['repeat_unit']
            grp.attrs['source'] = serialized['metadata']['source']

        # Write summary stats
        stats_group.attrs['count'] = count
        stats_group.attrs['average_molecular_weight'] = total_mw / count if count > 0 else 0.0
        stats_group.attrs['timestamp'] = str(os.path.getmtime(output_path) if os.path.exists(output_path) else 'N/A')

    logger.info(f"Successfully saved {count} graphs to {output_path}")

def main() -> None:
    """
    Main entry point for saving the cleaned dataset.
    Expects the cleaned dataset to be available via a mechanism defined in ingestion.py
    or passed as a command line argument. For this task, we assume the pipeline
    calls this function after T013 processing.
    
    In a real pipeline, the 'graphs' list would be passed from the ingestion step.
    Since we are implementing the script to be run, we simulate the flow by
    importing the process_dataset function if available, or expecting the user
    to provide the data.
    
    However, per task T014 description: "Save cleaned dataset to HDF5".
    We assume the 'cleaned dataset' is the output of the previous steps.
    To make this script executable and produce the artifact, we will:
    1. Try to load the processed data if it exists in a temporary state (e.g. from a previous run or pickle)
    2. OR, if this is a standalone script, it should be called by a runner that provides the data.
    
    Given the constraints of "real code", and that T010-T013 are "completed",
    we assume the data flow is:
    ingestion.py -> process_dataset() -> list of PolymerGraph
    
    We will create a simple runner that calls the ingestion process and saves it.
    """
    setup_logging(level=logging.INFO)
    
    # Import process_dataset from ingestion to get the data
    # This ensures we use the real data pipeline defined in T010-T013
    try:
        from data.ingestion import process_dataset
    except ImportError:
        logger.error("Could not import process_dataset from data.ingestion. Please ensure T010-T013 are correctly implemented.")
        sys.exit(1)

    output_path = os.environ.get('OUTPUT_PATH', 'projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5')
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Run the ingestion pipeline to get the cleaned graphs
        # This executes T010, T011, T012, T013 logic
        graphs = process_dataset()
        
        if not graphs:
            logger.warning("No graphs returned from process_dataset. Saving empty file or exiting.")
            # Per spec, we should not save empty/fake data.
            # But if the pipeline returns empty, we log and exit.
            sys.exit(0)

        save_to_hdf5(graphs, output_path)
        
        logger.info(f"Dataset saved successfully to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save dataset: {e}")
        raise

if __name__ == "__main__":
    main()
