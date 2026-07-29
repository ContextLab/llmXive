import csv
import json
import logging
import os
import sys
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, set_seed
from utils.graph_utils import build_undirected_graph, shortest_path_bfs
from utils.entity_linker import create_entity_linker, load_graph_from_file

logger = logging.getLogger(__name__)

def load_videokr_dataset() -> List[Dict[str, Any]]:
    path = get_path("data/raw/videokr_sft.csv")
    if not path.exists():
        raise FileNotFoundError(f"VideoKR-SFT dataset not found at {path}")
    
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_graph() -> Dict[str, Any]:
    return load_graph_from_file()

def map_entities_to_nodes(data: List[Dict], linker) -> List[Dict]:
    for row in data:
        question = row.get('question', '')
        # Extract entities from question (simplified: assume entity is the first word or keyword)
        # In a real implementation, this would use NLP
        entities = question.split()[:3] # Simple tokenization
        
        best_node = None
        best_confidence = 0.0
        
        for entity in entities:
            node_id, confidence = linker.link_entity(entity)
            if confidence > best_confidence:
                best_node = node_id
                best_confidence = confidence
        
        row['entity_node_id'] = best_node
        row['confidence'] = best_confidence
        
        if best_confidence < 0.5:
            row['entity_node_id'] = 'unmapped'
        
    return data

def calculate_chain_length(graph: Dict[str, Any], data: List[Dict]) -> List[Dict]:
    nodes = {n['id']: n for n in graph.get('nodes', [])}
    edges = graph.get('edges', [])
    
    graph_adj = build_undirected_graph(edges)
    
    for row in data:
        node_id = row.get('entity_node_id')
        if node_id == 'unmapped' or node_id is None:
            row['chain_length'] = None
            row['chain_bin'] = 'unresolvable'
            continue
        
        # Find a target node (simplified: assume target is a specific node or random)
        # In reality, this would be defined by the question-answer pair
        target_node = list(nodes.keys())[0] if nodes else None
        
        if target_node is None:
            row['chain_length'] = None
            row['chain_bin'] = 'unresolvable'
            continue
        
        path = shortest_path_bfs(graph_adj, node_id, target_node)
        if path:
            hops = len(path) - 1
            row['chain_length'] = hops
            if hops == 1:
                row['chain_bin'] = '1'
            elif hops == 2:
                row['chain_bin'] = '2'
            else:
                row['chain_bin'] = '3+'
        else:
            row['chain_length'] = None
            row['chain_bin'] = 'unresolvable'
    
    return data

def bin_hop_length(hop: int) -> str:
    if hop == 1:
        return '1'
    elif hop == 2:
        return '2'
    else:
        return '3+'

def run_pilot_sample(data: List[Dict], pilot_size: int = 1000) -> List[Dict]:
    return data[:pilot_size]

def oversample_dataset(data: List[Dict], target_bin: str, target_count: int) -> List[Dict]:
    # Simple oversampling: duplicate rows to reach target count
    bin_rows = [r for r in data if r.get('chain_bin') == target_bin]
    if not bin_rows:
        return data
    
    while len(bin_rows) < target_count:
        bin_rows.extend(bin_rows)
    
    return data + bin_rows[:target_count - len([r for r in data if r.get('chain_bin') == target_bin])]

def process_chunk(data_chunk: List[Dict], linker, graph) -> List[Dict]:
    linked = map_entities_to_nodes(data_chunk, linker)
    annotated = calculate_chain_length(graph, linked)
    return annotated

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    set_seed(42)
    
    try:
        logger.info("Loading VideoKR-SFT dataset...")
        data = load_videokr_dataset()
        logger.info(f"Loaded {len(data)} records.")
        
        logger.info("Loading knowledge graph...")
        graph = load_graph()
        logger.info(f"Loaded graph with {len(graph.get('nodes', []))} nodes.")
        
        logger.info("Creating entity linker...")
        linker = create_entity_linker(graph)
        
        # Pilot phase
        logger.info("Running pilot phase...")
        pilot_data = run_pilot_sample(data, 1000)
        
        # Process pilot
        pilot_data = map_entities_to_nodes(pilot_data, linker)
        pilot_data = calculate_chain_length(graph, pilot_data)
        
        # Check distribution
        bin_counts = {}
        for row in pilot_data:
            b = row.get('chain_bin', 'unknown')
            bin_counts[b] = bin_counts.get(b, 0) + 1
        
        logger.info(f"Pilot bin distribution: {bin_counts}")
        
        # Check if oversampling needed
        for bin_name, count in bin_counts.items():
            if count < 50 and bin_name != 'unresolvable':
                logger.info(f"Oversampling needed for bin: {bin_name}")
                # In a real implementation, we would oversample here
        
        # Process full dataset (chunked)
        logger.info("Processing full dataset...")
        processed_data = []
        chunk_size = 1000
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            processed_chunk = process_chunk(chunk, linker, graph)
            processed_data.extend(processed_chunk)
            logger.info(f"Processed chunk {i//chunk_size + 1}")
        
        # Filter out unresolvable
        final_data = [r for r in processed_data if r.get('chain_bin') != 'unresolvable']
        logger.info(f"Final data size: {len(final_data)}")
        
        # Write output
        output_path = get_path("data/processed/annotated_videokr.csv")
        ensure_dir(output_path)
        
        fieldnames = ['id', 'question', 'answer', 'entity_node_id', 'confidence', 'chain_length', 'chain_bin', 'correctness']
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(final_data)
        
        logger.info(f"Output written to {output_path}")
        
    except Exception as e:
        logger.error(f"Error in annotate_graph main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
