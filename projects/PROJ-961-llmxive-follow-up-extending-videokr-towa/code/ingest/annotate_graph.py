import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from utils.config import get_project_root, get_path, ensure_dir
from utils.graph_utils import shortest_path_bfs, build_undirected_graph
from utils.entity_linker import EntityLinker, create_entity_linker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_videokr_dataset(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load the VideoKR-SFT dataset from a JSON file.
    
    Args:
        file_path: Path to the dataset file.
        
    Returns:
        List of dataset records.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def load_graph(file_path: Path) -> Dict[str, List[str]]:
    """
    Load the knowledge graph from a JSON file.
    
    Args:
        file_path: Path to the graph file.
        
    Returns:
        Dictionary representing the graph adjacency list.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    return graph_data

def map_entities_to_nodes(
    question: str, 
    linker: EntityLinker
) -> Optional[Tuple[str, str]]:
    """
    Map entities in a question to graph nodes.
    
    Args:
        question: The question string.
        linker: The entity linker instance.
        
    Returns:
        Tuple of (start_node, end_node) or None if mapping fails.
    """
    entities = linker.extract_entities(question)
    if len(entities) < 2:
        return None
        
    start_node = linker.link(entities[0])
    end_node = linker.link(entities[1])
    
    if start_node is None or end_node is None:
        return None
        
    return start_node, end_node

def calculate_chain_length(
    start_node: str, 
    end_node: str, 
    graph: Dict[str, List[str]]
) -> Optional[int]:
    """
    Calculate the shortest path length between two nodes.
    
    Args:
        start_node: Starting node ID.
        end_node: Ending node ID.
        graph: The graph adjacency list.
        
    Returns:
        Integer hop count or None if no path exists.
    """
    distance = shortest_path_bfs(graph, start_node, end_node)
    return distance if distance is not None else None

def bin_hop_length(hop_count: int) -> str:
    """
    Bin the hop count into categorical labels.
    
    Args:
        hop_count: The integer hop count.
        
    Returns:
        Categorical string label.
    """
    if hop_count <= 0:
        return '0'
    elif hop_count == 1:
        return '1'
    elif hop_count == 2:
        return '2'
    else:
        return '3+'

def run_pilot_sample(
    dataset: List[Dict[str, Any]], 
    graph: Dict[str, List[str]], 
    linker: EntityLinker, 
    sample_size: int = 1000
) -> Dict[str, int]:
    """
    Run a pilot sample to estimate bin sizes.
    
    Args:
        dataset: The full dataset.
        graph: The knowledge graph.
        linker: The entity linker.
        sample_size: Number of samples to process.
        
    Returns:
        Dictionary of bin counts.
    """
    sample = dataset[:sample_size]
    bin_counts = Counter()
    
    for record in sample:
        entities = map_entities_to_nodes(record['question'], linker)
        if entities:
            start, end = entities
            hops = calculate_chain_length(start, end, graph)
            if hops is not None:
                bin_label = bin_hop_length(hops)
                bin_counts[bin_label] += 1
                
    return dict(bin_counts)

def oversample_dataset(
    dataset: List[Dict[str, Any]], 
    graph: Dict[str, List[str]], 
    linker: EntityLinker, 
    min_count: int = 50
) -> List[Dict[str, Any]]:
    """
    Oversample bins with fewer than min_count records.
    
    Args:
        dataset: The dataset to oversample.
        graph: The knowledge graph.
        linker: The entity linker.
        min_count: Minimum required records per bin.
        
    Returns:
        Oversampled dataset.
    """
    # Group by bin
    bin_groups: Dict[str, List[Dict[str, Any]]] = {}
    unresolvable = []
    
    for record in dataset:
        entities = map_entities_to_nodes(record['question'], linker)
        if entities:
            start, end = entities
            hops = calculate_chain_length(start, end, graph)
            if hops is not None:
                bin_label = bin_hop_length(hops)
                if bin_label not in bin_groups:
                    bin_groups[bin_label] = []
                bin_groups[bin_label].append(record)
            else:
                unresolvable.append(record)
        else:
            unresolvable.append(record)
    
    # Oversample
    result = []
    for bin_label, records in bin_groups.items():
        if len(records) < min_count:
            # Sample with replacement
            import random
            while len(records) < min_count:
                result.append(random.choice(records))
            result.extend(records)
        else:
            result.extend(records)
            
    result.extend(unresolvable)
    return result

def main() -> None:
    """Main entry point for graph annotation."""
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    ensure_dir(processed_dir)
    
    dataset_path = raw_dir / "videokr_sft.json"
    graph_path = raw_dir / "knowledge_graph.json"
    
    if not dataset_path.exists() or not graph_path.exists():
        logger.error("Required data files not found. Run download_data.py first.")
        sys.exit(1)
        
    dataset = load_videokr_dataset(dataset_path)
    graph = load_graph(graph_path)
    linker = create_entity_linker(graph)
    
    # Run pilot
    pilot_counts = run_pilot_sample(dataset, graph, linker)
    logger.info(f"Pilot bin counts: {pilot_counts}")
    
    # Process full dataset
    annotated_records = []
    unresolvable_count = 0
    
    for record in dataset:
        entities = map_entities_to_nodes(record['question'], linker)
        if entities:
            start, end = entities
            hops = calculate_chain_length(start, end, graph)
            if hops is not None:
                record['chain_length'] = hops
                record['chain_bin'] = bin_hop_length(hops)
                annotated_records.append(record)
            else:
                unresolvable_count += 1
        else:
            unresolvable_count += 1
            
    # Write output
    output_path = processed_dir / "annotated_videokr.csv"
    import csv
    if annotated_records:
        fieldnames = list(annotated_records[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotated_records)
            
    logger.info(f"Annotated {len(annotated_records)} records. Unresolvable: {unresolvable_count}")

if __name__ == "__main__":
    main()