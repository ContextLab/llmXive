import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_config, get_paths

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise

def serialize_graph(graph_data: Dict[str, Any], output_path: Path) -> str:
    """
    Serialize a single graph dictionary to a pickle file.
    
    Args:
        graph_data: Dictionary containing graph data (nodes, edges, metadata).
        output_path: Path to the output .pkl file.
        
    Returns:
        The SHA256 checksum of the created file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'wb') as f:
            pickle.dump(graph_data, f)
        
        checksum = calculate_checksum(output_path)
        logger.info(f"Serialized graph to {output_path} (Checksum: {checksum[:16]}...)")
        return checksum
    except Exception as e:
        logger.error(f"Failed to serialize graph to {output_path}: {e}")
        raise

def serialize_directory_graphs(
    input_dir: Path, 
    output_dir: Path, 
    file_pattern: str = "*.pkl"
) -> List[Dict[str, Any]]:
    """
    Serialize all graph files from input_dir to output_dir.
    Assumes input files are already in a serializable format (e.g., dicts from graph_builder).
    
    Args:
        input_dir: Directory containing source graph data (e.g., raw or processed dicts).
        output_dir: Directory where .pkl files will be written.
        file_pattern: Glob pattern for input files (default: *.pkl if they are pre-pickled, 
                      but here we assume we are processing dict objects loaded from memory 
                      or intermediate JSON if the pipeline was different. 
                      However, based on T012/T013, we likely have a list of graph objects.
                      This function assumes `input_dir` contains JSON representations or 
                      we are re-serializing existing pickles to a new location with checksums.
                      
                      *Correction*: The task asks to implement serialization TO data/processed/graphs.
                      If the data is already in memory (from T012), we need a driver script.
                      If the data is in a raw format, we load and serialize.
                      
                      Let's assume this function takes a list of graph objects and writes them.
                      But to fit the signature, we will assume `input_dir` contains JSON files 
                      representing the graphs (if T012/13 produced JSON) or we are re-serializing.
                      
                      *Refined Strategy*: This function will look for JSON files in `input_dir`
                      (representing the output of T012 if it saved JSON, or we assume we are 
                      processing a directory of graph dicts). 
                      Actually, T012 returns objects. T013 generates samples. 
                      The most robust interpretation: This script is a utility to take 
                      graph objects (passed via a manifest or directory of JSON) and 
                      serialize them to Pickle with checksums.
                      
                      Let's assume the input is a directory of JSON files representing graphs.
    """
    manifest = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files in input directory (assuming intermediate JSON representation)
    # Or if the input is already pickled, we just move and checksum? 
    # The task says "Implement graph serialization ... (pickle/parquet)".
    # Let's assume we are converting from the intermediate JSON format (if any) or 
    # we are re-serializing a directory of graph dicts.
    
    # Since T012 produces objects, and T013 produces samples, we likely need a script 
    # that takes the list of graphs and writes them. 
    # However, to make this a reusable utility, let's assume it processes a directory 
    # of JSON graph dumps.
    
    input_files = list(input_dir.glob("*.json"))
    if not input_files:
        # Try pickled inputs if we are just re-packaging?
        input_files = list(input_dir.glob("*.pkl"))
        
    if not input_files:
        logger.warning(f"No graph files found in {input_dir}")
        return manifest

    for file_path in input_files:
        try:
            # Load data
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    graph_data = json.load(f)
            elif file_path.suffix == '.pkl':
                with open(file_path, 'rb') as f:
                    graph_data = pickle.load(f)
            else:
                continue
            
            # Construct output path
            stem = file_path.stem
            output_path = output_dir / f"{stem}.pkl"
            
            # Serialize
            checksum = serialize_graph(graph_data, output_path)
            
            manifest.append({
                "source_file": str(file_path),
                "output_file": str(output_path),
                "checksum": checksum,
                "format": "pickle"
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise

    return manifest

def save_checksum_manifest(manifest: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the list of checksums to a JSON manifest file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved checksum manifest to {output_path}")

def main():
    """
    Main entry point for graph serialization.
    Reads graph data (assumed to be in JSON format in data/processed/graphs/raw or similar)
    and serializes them to Pickle with checksums.
    """
    config = get_config()
    paths = get_paths()
    
    # Configuration
    # Assuming intermediate JSONs are in a specific directory or we are processing the output of T012
    # Since T012 returns objects, we assume there is a script that saved them to JSON first,
    # or we are re-serializing. 
    # For this task, we assume the input is data/processed/graphs/intermediate/*.json
    input_dir = paths.get('processed_graphs', paths['data'] / 'processed' / 'graphs')
    # If there's a specific intermediate dir, use it. Otherwise, we might be reading from raw?
    # Let's assume a standard flow: raw -> json -> pkl.
    # If no intermediate exists, we might need to generate it from raw XYZ? 
    # But T012 handles XYZ -> Graph. T015 handles Graph -> Pickle.
    # We assume the Graph objects are available as JSON in the input_dir.
    
    # Fallback: if no JSONs, check if we are supposed to read from a specific intermediate location
    intermediate_dir = input_dir / "intermediate"
    if not intermediate_dir.exists():
        # Maybe the graphs are in the root of processed_graphs as JSON?
        intermediate_dir = input_dir
    
    output_dir = paths['data'] / 'processed' / 'graphs' / 'serialized'
    manifest_path = paths['data'] / 'processed' / 'graphs' / 'checksums.json'
    
    logger.info(f"Serializing graphs from {intermediate_dir} to {output_dir}")
    
    manifest = serialize_directory_graphs(intermediate_dir, output_dir)
    
    if manifest:
        save_checksum_manifest(manifest, manifest_path)
        print(f"Successfully serialized {len(manifest)} graphs.")
    else:
        logger.warning("No graphs were serialized. Check input directory.")

if __name__ == "__main__":
    main()
