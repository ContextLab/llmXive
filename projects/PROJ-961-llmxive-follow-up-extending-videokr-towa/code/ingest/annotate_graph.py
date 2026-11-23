"""
Graph annotation module for VideoKR-SFT dataset.
"""
import csv
import json
import logging
import os
import sys
import time
import itertools
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_project_root, get_path, ensure_dir, get_seed
from utils.graph_utils import shortest_path_bfs, build_undirected_graph
from utils.entity_linker import create_entity_linker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_videokr_dataset(data_path: Path) -> List[Dict[str, Any]]:
    """Load VideoKR-SFT dataset from JSON file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def load_graph(graph_path: Path) -> Dict[Any, List[Any]]:
    """Load knowledge graph from JSON file."""
    with open(graph_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    edges = [(edge["source"], edge["target"]) for edge in data.get("edges", [])]
    return build_undirected_graph(edges)

def map_entities_to_nodes(text: str, linker, graph: Dict[Any, List[Any]]) -> Tuple[Optional[str], float]:
    """Map entities in text to graph nodes."""
    # Check if text already has node_id or entity_id
    if "node_id" in text or "entity_id" in text:
        # Use existing IDs
        return text.get("node_id") or text.get("entity_id"), 1.0

    results = linker.link_entities(text)
    if not results:
        return None, 0.0

    # Use the highest confidence match
    best_entity, best_node, best_confidence = max(results, key=lambda x: x[2])
    return best_node, best_confidence

def calculate_chain_length(graph: Dict[Any, List[Any]], start: Optional[str], end: Optional[str]) -> Optional[int]:
    """Calculate shortest path hops between two nodes."""
    if start is None or end is None:
        return None

    hops = shortest_path_bfs(graph, start, end)
    if hops is None:
        return None
    return len(hops) - 1

def bin_hop_length(hops: Optional[int]) -> str:
    """Bin hop length into categories."""
    if hops is None:
        return "unresolvable"
    if hops <= 2:
        return str(hops)
    return "3+"

def run_pilot_sample(dataset: List[Dict[str, Any]], pilot_size: int = 1000) -> List[Dict[str, Any]]:
    """Run pilot sampling to estimate distribution."""
    return dataset[:min(pilot_size, len(dataset))]

def oversample_dataset(pilot_data: List[Dict[str, Any]], target_bin: str, target_count: int = 50) -> List[Dict[str, Any]]:
    """Oversample rare bins to reach minimum count."""
    bin_counts = {}
    for record in pilot_data:
        bin_val = record.get("chain_bin", "unknown")
        bin_counts[bin_val] = bin_counts.get(bin_val, 0) + 1

    if bin_counts.get(target_bin, 0) >= target_count:
        return pilot_data

    # Resample from pilot to reach target
    target_records = [r for r in pilot_data if r.get("chain_bin") == target_bin]
    if not target_records:
        return pilot_data

    oversampled = target_records * (target_count // len(target_records) + 1)
    return pilot_data + oversampled[:target_count - len(target_records)]

def process_chunk(chunk: List[Dict[str, Any]], graph: Dict[Any, List[Any]], linker) -> List[Dict[str, Any]]:
    """Process a chunk of data and annotate with graph information."""
    annotated = []
    for record in chunk:
        question = record.get("question", "")
        answer = record.get("answer", "")
        correctness = record.get("correctness", False)

        entity_node_id, confidence = map_entities_to_nodes(question, linker, graph)
        chain_length = calculate_chain_length(graph, entity_node_id, entity_node_id)
        chain_bin = bin_hop_length(chain_length)

        annotated_record = {
            "id": record.get("id", ""),
            "question": question,
            "answer": answer,
            "chain_length": chain_length,
            "chain_bin": chain_bin,
            "correctness": correctness,
            "entity_node_id": entity_node_id,
            "confidence": confidence
        }
        annotated.append(annotated_record)

    return annotated

def main():
    """Main entry point for graph annotation."""
    project_root = get_project_root()
    raw_dir = get_path(project_root, "raw_data")
    processed_dir = get_path(project_root, "processed_data")

    sft_path = raw_dir / "videokr_sft.json"
    graph_path = raw_dir / "knowledge_graph.json"
    output_path = processed_dir / "annotated_videokr.csv"

    if not sft_path.exists() or not graph_path.exists():
        logger.error("Data files not found. Run download_data.py first.")
        sys.exit(1)

    ensure_dir(processed_dir)

    # Load data
    logger.info("Loading dataset and graph...")
    dataset = load_videokr_dataset(sft_path)
    graph = load_graph(graph_path)

    # Create entity linker
    linker = create_entity_linker(graph_path)

    # Pilot sampling
    logger.info("Running pilot sampling...")
    pilot_data = run_pilot_sample(dataset, pilot_size=1000)

    # Process pilot data
    logger.info("Processing pilot data...")
    annotated_pilot = process_chunk(pilot_data, graph, linker)

    # Check for rare bins and oversample if needed
    bin_counts = {}
    for record in annotated_pilot:
        bin_val = record.get("chain_bin", "unknown")
        bin_counts[bin_val] = bin_counts.get(bin_val, 0) + 1

    for bin_name, count in bin_counts.items():
        if count < 50 and bin_name != "unresolvable":
            logger.info(f"Oversampling bin {bin_name} (current: {count}, target: 50)")
            annotated_pilot = oversample_dataset(annotated_pilot, bin_name, target_count=50)

    # Process full dataset (or stream if too large)
    logger.info("Processing full dataset...")
    annotated_data = process_chunk(dataset, graph, linker)

    # Write output
    logger.info(f"Writing output to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if annotated_data:
            writer = csv.DictWriter(f, fieldnames=annotated_data[0].keys())
            writer.writeheader()
            writer.writerows(annotated_data)

    logger.info(f"Annotation complete. Output: {output_path}")

if __name__ == "__main__":
    main()