"""
Data loader module for llmXive project.
Handles fetching, parsing, and noise injection for the LoCoMo benchmark.
Implements streaming support for large datasets to comply with RAM limits.
"""
import os
import json
import logging
import hashlib
import random
import csv
from typing import List, Dict, Any, Optional, Iterator, Tuple
from pathlib import Path

import networkx as nx
import spacy
from datasets import load_dataset, Dataset
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = "data/raw"
INTERMEDIATE_DATA_DIR = "data/intermediate"
PROCESSED_DATA_DIR = "data/processed"
GRAPHS_DIR = "data/processed/graphs"
STREAMING_THRESHOLD_GB = 6.0
STREAMING_THRESHOLD_BYTES = STREAMING_THRESHOLD_GB * 1024**3

# Estimated size per row in bytes (conservative estimate for text data)
ESTIMATED_ROW_SIZE_BYTES = 2048

def ensure_output_dirs():
    """Create necessary output directories if they don't exist."""
    dirs = [RAW_DATA_DIR, INTERMEDIATE_DATA_DIR, PROCESSED_DATA_DIR, GRAPHS_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info(f"Ensured output directories exist: {dirs}")

def fetch_locomo_dataset(subset: str = "test", streaming: bool = False) -> Iterator[Dict[str, Any]]:
    """
    Fetch the LoCoMo benchmark dataset from HuggingFace.

    Args:
        subset: The split to load (default: "test")
        streaming: If True, stream the dataset instead of loading fully into memory.

    Returns:
        An iterator of dataset rows (dicts).

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    # Canonical dataset ID for LoCoMo benchmark
    dataset_id = "locomo/locomo-benchmark"

    logger.info(f"Fetching dataset: {dataset_id}, split: {subset}, streaming: {streaming}")

    try:
        if streaming:
            # Stream the dataset to avoid memory issues
            ds = load_dataset(dataset_id, split=subset, streaming=True)
            # Return an iterator that yields rows
            return iter(ds)
        else:
            # Estimate total size to decide if streaming is needed
            # We attempt to load a small sample first to estimate size if possible
            # For now, we assume if we are in streaming mode, we stream.
            # If not, we try to load. If it fails due to memory, the caller should retry with streaming=True.
            ds = load_dataset(dataset_id, split=subset)
            # Convert to iterator for consistent processing
            return iter(ds)
    except Exception as e:
        # T035 Compliance: Fail loudly, do not fallback to synthetic data
        logger.error(f"Failed to fetch dataset '{dataset_id}': {e}")
        raise RuntimeError(f"Cannot proceed without real data. Fetch failed: {e}")

def save_raw_data(tasks: List[Dict[str, Any]], output_path: str = None):
    """
    Save raw tasks to a CSV file.

    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output CSV file.
    """
    if output_path is None:
        output_path = os.path.join(RAW_DATA_DIR, "locomo.csv")

    ensure_output_dirs()

    if not tasks:
        logger.warning("No tasks to save.")
        return

    fieldnames = ["task_id", "question", "context", "answer"]
    # Ensure we have the keys, even if missing in some rows
    # We assume the dataset provides these columns. If not, we handle gracefully.
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for task in tasks:
            # Map dataset columns to expected CSV columns if necessary
            # Assuming dataset has 'question', 'context', 'answer' and an ID
            row = {
                "task_id": task.get("id", "unknown"),
                "question": task.get("question", ""),
                "context": task.get("context", ""),
                "answer": task.get("answer", "")
            }
            writer.writerow(row)

    logger.info(f"Saved {len(tasks)} raw tasks to {output_path}")

def build_memory_graph(context: str, task_id: str) -> Dict[str, Any]:
    """
    Parse a context string into a directed graph using NER/Rule-Based extraction.
    Uses spaCy to identify subject-verb-object triples.

    Args:
        context: The context string to parse.
        task_id: The ID of the task (for logging/debugging).

    Returns:
        A JSON-serializable graph structure:
        {
            "task_id": str,
            "edges": [
                {"source": str, "target": str, "relation_string": str}
            ]
        }
    """
    # Load spaCy model (lazy loading to avoid overhead if not used)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.error("spaCy 'en_core_web_sm' model not found. Run: python -m spacy download en_core_web_sm")
        raise

    doc = nlp(context)
    edges = []
    node_set = set()

    # Simple triple extraction: Subject -> Verb -> Object
    # We iterate over sentences to improve accuracy
    for sentence in doc.sents:
        for token in sentence:
            if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                subj = token.text
                verb = token.head.text
                # Look for direct object
                for child in token.head.children:
                    if child.dep_ in ("dobj", "attr", "oprd"):
                        obj = child.text
                        # Create a unique node ID or use text
                        source_node = subj.lower().strip()
                        target_node = obj.lower().strip()
                        relation = f"{subj} {verb} {obj}".lower().strip()

                        if source_node and target_node and source_node != target_node:
                            edges.append({
                                "source": source_node,
                                "target": target_node,
                                "relation_string": relation
                            })
                            node_set.add(source_node)
                            node_set.add(target_node)

    # Fallback if no triples found: create a single node graph or empty graph
    if not edges and node_set:
        # Create self-loops or just list nodes if necessary, but spec says edges
        pass

    return {
        "task_id": task_id,
        "edges": edges
    }

def inject_noise(graph: Dict[str, Any], ratio: float = 0.1, seed: int = 42) -> Dict[str, Any]:
    """
    Add a proportion of random distractor edges to the original graph.

    Args:
        graph: The input graph dict with "task_id" and "edges".
        ratio: The proportion of random edges to add relative to original edges.
        seed: Random seed for reproducibility.

    Returns:
        A new graph dict with added edges.
    """
    random.seed(seed)
    edges = graph.get("edges", [])
    task_id = graph.get("task_id")

    if not edges:
        return graph

    # Identify existing edges to avoid duplicates
    existing_pairs = {(e["source"], e["target"]) for e in edges}
    nodes = set()
    for e in edges:
        nodes.add(e["source"])
        nodes.add(e["target"])

    # Calculate number of edges to add
    num_to_add = int(len(edges) * ratio)
    new_edges = []

    attempts = 0
    max_attempts = num_to_add * 100  # Prevent infinite loops if graph is dense
    while len(new_edges) < num_to_add and attempts < max_attempts:
        attempts += 1
        if len(nodes) < 2:
            break

        source = random.choice(list(nodes))
        target = random.choice(list(nodes))

        # Avoid self-loops and existing edges
        if source != target and (source, target) not in existing_pairs:
            # Generate a random relation string
            relation = f"random_relation_{attempts}"
            new_edges.append({
                "source": source,
                "target": target,
                "relation_string": relation
            })
            existing_pairs.add((source, target))

    # Combine original and new edges
    all_edges = edges + new_edges

    return {
        "task_id": task_id,
        "edges": all_edges
    }

def generate_noisy_graphs(graphs: List[Dict[str, Any]], ratio: float = 0.1, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate noisy versions of a list of graphs.

    Args:
        graphs: List of input graphs.
        ratio: Noise ratio.
        seed: Random seed.

    Returns:
        List of noisy graphs.
    """
    noisy_graphs = []
    for g in graphs:
        noisy_g = inject_noise(g, ratio=ratio, seed=seed)
        noisy_graphs.append(noisy_g)
    return noisy_graphs

def save_noisy_graphs(graphs: List[Dict[str, Any]], output_path: str = None):
    """
    Save noisy graphs to a JSON file.

    Args:
        graphs: List of graph dictionaries.
        output_path: Path to the output JSON file.
    """
    if output_path is None:
        output_path = os.path.join(GRAPHS_DIR, "graph_noise_42.json")

    ensure_output_dirs()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graphs, f, indent=2)

    logger.info(f"Saved {len(graphs)} noisy graphs to {output_path}")

def load_noisy_graphs(input_path: str = None) -> List[Dict[str, Any]]:
    """
    Load noisy graphs from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of graph dictionaries.
    """
    if input_path is None:
        input_path = os.path.join(GRAPHS_DIR, "graph_noise_42.json")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Noisy graph file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_in_chunks(
    dataset_iterator: Iterator[Dict[str, Any]],
    chunk_size: int = 100,
    process_func: callable = None,
    output_callback: callable = None
) -> Iterator[Dict[str, Any]]:
    """
    Process dataset items in configurable chunks to manage memory.

    Args:
        dataset_iterator: An iterator over dataset items.
        chunk_size: Number of items to process at once.
        process_func: Function to apply to each chunk. If None, identity is used.
        output_callback: Optional callback to handle output of each chunk.

    Yields:
        Processed chunks (or individual items if no chunking logic is applied).
    """
    if process_func is None:
        process_func = lambda x: x

    chunk = []
    for item in tqdm(dataset_iterator, desc="Processing in chunks"):
        chunk.append(item)
        if len(chunk) >= chunk_size:
            processed_chunk = process_func(chunk)
            if output_callback:
                output_callback(processed_chunk)
            yield processed_chunk
            chunk = []

    # Process remaining items
    if chunk:
        processed_chunk = process_func(chunk)
        if output_callback:
            output_callback(processed_chunk)
        yield processed_chunk

def main():
    """
    Main entry point for data loading and graph generation.
    Supports streaming mode for large datasets.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Load LoCoMo dataset and generate graphs.")
    parser.add_argument("--download", action="store_true", help="Download raw dataset.")
    parser.add_argument("--generate-graphs", action="store_true", help="Build memory graphs from raw data.")
    parser.add_argument("--inject-noise", action="store_true", help="Inject noise into graphs.")
    parser.add_argument("--streaming", action="store_true", help="Enable streaming mode for large datasets.")
    parser.add_argument("--subset", type=str, default="test", help="Dataset split to load.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for noise injection.")
    parser.add_argument("--noise-ratio", type=float, default=0.1, help="Ratio of noise edges to add.")

    args = parser.parse_args()

    ensure_output_dirs()

    # 1. Download raw data
    if args.download:
        logger.info("Starting download...")
        # Determine if streaming is needed based on estimated size or explicit flag
        # For this implementation, we respect the --streaming flag
        # In a real scenario, we might estimate size first
        ds_iter = fetch_locomo_dataset(subset=args.subset, streaming=args.streaming)

        # Collect all items if not streaming, or process in chunks if streaming
        # For simplicity in this script, we collect all to save to CSV first.
        # If streaming is True and the dataset is huge, we should stream to disk directly.
        # However, saving to CSV requires knowing all rows or appending.
        # We'll append in chunks if streaming.
        raw_tasks = []
        if args.streaming:
            # Stream and save in chunks
            def save_chunk(chunk):
                save_raw_data(chunk) # This appends or overwrites? Let's make it append for chunks
                # Actually, save_raw_data currently overwrites. We need an append version or handle chunks differently.
                # For this task, we will collect a reasonable number in memory if possible,
                # or implement a chunked writer.
                # To keep it simple and robust for the "streaming" requirement:
                # We will process in chunks and write to a file incrementally.
                pass

            # Let's implement a streaming save directly
            output_path = os.path.join(RAW_DATA_DIR, "locomo.csv")
            ensure_output_dirs()
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["task_id", "question", "context", "answer"], extrasaction='ignore')
                writer.writeheader()
                count = 0
                for item in ds_iter:
                    row = {
                        "task_id": item.get("id", "unknown"),
                        "question": item.get("question", ""),
                        "context": item.get("context", ""),
                        "answer": item.get("answer", "")
                    }
                    writer.writerow(row)
                    count += 1
                    if count % 1000 == 0:
                        logger.info(f"Streamed {count} rows...")
            logger.info(f"Streamed {count} rows to {output_path}")
        else:
            # Load all into memory (may fail if too large)
            raw_tasks = list(ds_iter)
            save_raw_data(raw_tasks)

    # 2. Build Graphs
    if args.generate_graphs:
        logger.info("Building memory graphs...")
        # Load raw data
        raw_path = os.path.join(RAW_DATA_DIR, "locomo.csv")
        if not os.path.exists(raw_path):
            logger.error(f"Raw data not found at {raw_path}. Run with --download first.")
            return

        # Read CSV
        tasks = []
        with open(raw_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tasks.append(row)

        graphs = []
        # Process in chunks to manage memory
        def build_graph_chunk(chunk):
            chunk_graphs = []
            for task in chunk:
                graph = build_memory_graph(task["context"], task["task_id"])
                chunk_graphs.append(graph)
            return chunk_graphs

        # If the list is huge, we should stream the CSV too, but for now we assume CSV fits or is manageable.
        # We'll just iterate.
        for i in range(0, len(tasks), 100):
            chunk = tasks[i:i+100]
            chunk_graphs = build_graph_chunk(chunk)
            graphs.extend(chunk_graphs)

        # Save raw graphs
        output_path = os.path.join(INTERMEDIATE_DATA_DIR, "graphs_raw.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graphs, f, indent=2)
        logger.info(f"Saved {len(graphs)} raw graphs to {output_path}")

    # 3. Inject Noise
    if args.inject_noise:
        logger.info("Injecting noise into graphs...")
        raw_graphs_path = os.path.join(INTERMEDIATE_DATA_DIR, "graphs_raw.json")
        if not os.path.exists(raw_graphs_path):
            logger.error(f"Raw graphs not found at {raw_graphs_path}. Run with --generate-graphs first.")
            return

        with open(raw_graphs_path, "r", encoding="utf-8") as f:
            graphs = json.load(f)

        noisy_graphs = generate_noisy_graphs(graphs, ratio=args.noise_ratio, seed=args.seed)
        save_noisy_graphs(noisy_graphs)

if __name__ == "__main__":
    main()
