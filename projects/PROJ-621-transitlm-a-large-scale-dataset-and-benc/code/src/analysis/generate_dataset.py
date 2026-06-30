import json
import logging
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.lib.config import get_logger, set_seed, init_project_config
from src.lib.splitter import load_graph_from_file, load_sequences_from_file, split_dataset, save_sequences
from src.lib.text_utils import convert_gtfs_to_text_dataset
from src.contracts.models import GTFSGraph, RouteSequence

def generate_train_test_splits(
    graph_file: Path,
    sequences_file: Path,
    train_output: Path,
    test_od_output: Path,
    seed: int = 42,
    test_ratio: float = 0.2
) -> None:
    """
    Generates the final map-free dataset splits:
    1. Loads the GTFS graph and text sequences.
    2. Splits them into path-disjoint and edge-disjoint train/test sets.
    3. Writes `train_sequences.txt` containing natural language prompts.
    4. Writes `test_od_pairs.json` containing the raw Origin-Destination pairs for the test set.
    """
    logger = get_logger("generate_dataset")
    logger.info(f"Starting dataset generation with seed {seed}")
    set_seed(seed)

    # Ensure output directories exist
    train_output.parent.mkdir(parents=True, exist_ok=True)
    test_od_output.parent.mkdir(parents=True, exist_ok=True)

    # Load inputs
    logger.info(f"Loading graph from {graph_file}")
    graph = load_graph_from_file(graph_file)

    logger.info(f"Loading sequences from {sequences_file}")
    sequences = load_sequences_from_file(sequences_file)

    if not graph or not sequences:
        logger.error("Graph or sequences are empty. Cannot generate splits.")
        raise ValueError("Input data is empty.")

    # Split dataset
    logger.info(f"Splitting dataset (test ratio: {test_ratio})")
    train_seqs, test_seqs = split_dataset(sequences, graph, test_ratio=test_ratio, seed=seed)

    logger.info(f"Train size: {len(train_seqs)}, Test size: {len(test_seqs)}")

    # 1. Generate train_sequences.txt
    # Format: "Take Line X from Station A to Station B" (one per line)
    # We assume the sequence represents the path A -> ... -> B
    with open(train_output, 'w', encoding='utf-8') as f:
        for seq in train_seqs:
            if not seq.stations or len(seq.stations) < 2:
                continue
            origin = seq.stations[0]
            destination = seq.stations[-1]
            # Extract lines involved (simplified: join unique lines)
            lines = sorted(list(set(seq.lines)))
            line_str = ", ".join(lines) if lines else "various lines"
            
            # Construct the natural language prompt as per T011 spec
            prompt = f"Take {line_str} from {origin} to {destination}"
            f.write(prompt + "\n")
    
    logger.info(f"Written training sequences to {train_output}")

    # 2. Generate test_od_pairs.json
    # Format: List of {"origin": str, "destination": str, "ground_truth_line": str?}
    test_od_data = []
    for seq in test_seqs:
        if not seq.stations or len(seq.stations) < 2:
            continue
        origin = seq.stations[0]
        destination = seq.stations[-1]
        
        od_entry = {
            "origin": origin,
            "destination": destination,
            "ground_truth_sequence": seq.stations,
            "ground_truth_lines": seq.lines
        }
        test_od_data.append(od_entry)

    with open(test_od_output, 'w', encoding='utf-8') as f:
        json.dump(test_od_data, f, indent=2)
    
    logger.info(f"Written test O-D pairs to {test_od_output}")

def main() -> None:
    """
    Entry point for the dataset generation script.
    Assumes standard project paths:
      - Graph: data/processed/gtfs_graph.json
      - Sequences: data/processed/raw_sequences.json
      - Train Output: data/processed/train_sequences.txt
      - Test Output: data/processed/test_od_pairs.json
    """
    init_project_config()
    logger = get_logger("generate_dataset")
    
    # Define paths relative to project root
    # Assuming the script is run from the project root or we resolve relative to data/
    data_dir = project_root / "data" / "processed"
    
    graph_path = data_dir / "gtfs_graph.json"
    sequences_path = data_dir / "raw_sequences.json"
    train_path = data_dir / "train_sequences.txt"
    test_od_path = data_dir / "test_od_pairs.json"

    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}. Run T005 first.")
        sys.exit(1)
    
    if not sequences_path.exists():
        logger.error(f"Sequences file not found: {sequences_path}. Run T011 first.")
        sys.exit(1)

    try:
        generate_train_test_splits(
            graph_file=graph_path,
            sequences_file=sequences_path,
            train_output=train_path,
            test_od_output=test_od_path,
            seed=42
        )
        logger.info("Dataset generation completed successfully.")
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()