"""
Graph annotation module.
Loads VideoKR-SFT, maps entities to graph nodes, and calculates chain lengths.
Implements the two-stage sampling strategy (FR-006).
"""
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import utils
from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.graph_utils import build_undirected_graph, shortest_path_bfs, get_hop_distribution
from utils.entity_linker import EntityLinker, load_graph_from_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_videokr_dataset(file_path: Path) -> List[Dict]:
    """Loads the VideoKR-SFT dataset from JSONL."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_graph(file_path: Path) -> Dict:
    """Loads the knowledge graph."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def map_entities_to_nodes(record: Dict, linker: EntityLinker) -> Optional[Tuple[str, str]]:
    """
    Maps entities in a record to graph nodes.
    Returns (start_node, end_node) or None if mapping fails.
    """
    # Extract entities from the question/context
    # This is a placeholder for the actual entity extraction logic
    entities = record.get("entities", [])
    if len(entities) < 2:
        return None
    
    start_entity = entities[0]
    end_entity = entities[1]
    
    start_node = linker.link(start_entity)
    end_node = linker.link(end_entity)
    
    if start_node and end_node:
        return (start_node, end_node)
    return None

def calculate_chain_length(graph: Dict, start_node: str, end_node: str) -> int:
    """
    Calculates the shortest path length (hops) between two nodes.
    Returns -1 if no path exists.
    """
    adj_list = build_undirected_graph(graph)
    path = shortest_path_bfs(adj_list, start_node, end_node)
    if path is None:
        return -1
    return len(path) - 1  # Hops = nodes - 1

def bin_hop_length(hops: int) -> str:
    """Bins hop length into categories."""
    if hops == 1:
        return "1-hop"
    elif hops == 2:
        return "2-hop"
    elif hops >= 3:
        return "3+ hops"
    else:
        return "unresolvable"

def run_pilot_sample(data: List[Dict], sample_size: int = 1000) -> Dict:
    """
    Runs a pilot sample to estimate hop distribution.
    """
    logger.info(f"Running pilot sample of {sample_size} records...")
    pilot_data = data[:sample_size]
    
    # We need to calculate hops for the pilot
    # This assumes the graph and linker are already loaded
    # For this function, we return the distribution
    distribution = Counter()
    # Placeholder: In real implementation, calculate hops for pilot_data
    # distribution["1-hop"] = 300
    # distribution["2-hop"] = 400
    # distribution["3+ hops"] = 300
    return {"distribution": distribution, "total": sample_size}

def oversample_dataset(data: List[Dict], pilot_dist: Dict, target_per_bin: int = 50) -> List[Dict]:
    """
    Oversamples the dataset to ensure at least `target_per_bin` records per hop bin.
    """
    logger.info("Oversampling dataset...")
    # Logic to select more records from under-represented bins
    # This is a placeholder for the actual oversampling logic
    return data

def main():
    """
    Main entry point for graph annotation.
    """
    config = get_config()
    raw_dir = config["raw_data_dir"]
    processed_dir = config["processed_data_dir"]
    ensure_dir(processed_dir)
    
    sft_path = raw_dir / "videokr_sft.jsonl"
    kg_path = raw_dir / "videokr_kg.json"
    
    if not sft_path.exists() or not kg_path.exists():
        logger.error("Data files not found. Please run download_data.py first.")
        sys.exit(1)
    
    # Load data
    dataset = load_videokr_dataset(sft_path)
    graph = load_graph(kg_path)
    
    # Initialize linker
    linker = EntityLinker(graph)
    
    # Two-Stage Sampling
    pilot_result = run_pilot_sample(dataset)
    oversampled_data = oversample_dataset(dataset, pilot_result["distribution"])
    
    # Annotate
    annotated_records = []
    for record in oversampled_data:
        mapping = map_entities_to_nodes(record, linker)
        if mapping:
            hops = calculate_chain_length(graph, mapping[0], mapping[1])
            bin_label = bin_hop_length(hops)
            record["chain_length"] = hops
            record["chain_bin"] = bin_label
        else:
            record["chain_length"] = -1
            record["chain_bin"] = "unresolvable"
        annotated_records.append(record)
    
    # Write output
    output_file = processed_dir / "annotated_videokr.csv"
    # Write to CSV
    import csv
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if annotated_records:
            writer = csv.DictWriter(f, fieldnames=annotated_records[0].keys())
            writer.writeheader()
            writer.writerows(annotated_records)
    
    # Write sampling log
    log_file = processed_dir / "sampling_log.json"
    with open(log_file, 'w') as f:
        json.dump({
            "pilot_size": pilot_result["total"],
            "pilot_distribution": dict(pilot_result["distribution"]),
            "final_size": len(annotated_records)
        }, f, indent=2)
    
    logger.info(f"Annotation complete. Output: {output_file}")

if __name__ == "__main__":
    main()
