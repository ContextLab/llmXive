import os
import re
import ast
import sys
import hashlib
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from dataclasses import dataclass, field

import networkx as nx
from datasets import load_dataset

from config import get_data_dir, get_output_dir, set_global_seeds
from utils.logger import setup_logger, log_error, DataLoadError

logger = setup_logger(__name__)

@dataclass
class ParsedIssue:
    """Represents a parsed issue instance from the dataset."""
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: str
    file_history: List[Dict[str, Any]]
    relevant_lines: int
    raw_data: Dict[str, Any]

class ClawSweBenchLoader:
    """Loader for the Claw-SWE-Bench dataset with streaming support."""

    DATASET_NAME = "princeton-nlp/Claw-SWE-Bench"
    
    def __init__(self, streaming: bool = True):
        self.streaming = streaming
        self.dataset = None
        self.logger = logging.getLogger(__name__)

    def load(self) -> Iterator[Dict[str, Any]]:
        """Load the dataset using streaming if enabled."""
        try:
            self.dataset = load_dataset(
                self.DATASET_NAME,
                split="train",
                streaming=self.streaming
            )
            return iter(self.dataset)
        except Exception as e:
            log_error(logger, "DataLoadError", f"Failed to load dataset: {e}")
            raise DataLoadError(f"Failed to load dataset: {e}") from e

def calculate_relevant_lines(issue: Dict[str, Any]) -> int:
    """
    Calculate the total lines of relevant file history for an issue.
    
    1. Parse Python imports to build a dependency graph using networkx.
    2. Perform BFS/DFS traversal from the issue target files.
    3. Sum the lines of all traversed files.
    """
    file_history = issue.get("file_history", [])
    if not file_history:
        return 0

    # Build dependency graph
    G = nx.DiGraph()
    file_map = {} # filename -> content/lines

    for file_entry in file_history:
        filename = file_entry.get("filename", "")
        content = file_entry.get("content", "")
        lines = len(content.splitlines()) if content else 0
        file_map[filename] = lines
        G.add_node(filename, lines=lines)

        # Parse imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_name = alias.name.split('.')[0]
                        if imported_name in file_map:
                            G.add_edge(filename, imported_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_name = node.module.split('.')[0]
                        if imported_name in file_map:
                            G.add_edge(filename, imported_name)
        except SyntaxError:
            continue

    # Identify target files (files mentioned in the issue or patch)
    # For simplicity, we assume all files in file_history are potentially relevant
    # In a more complex version, we would parse the problem statement for filenames.
    target_files = list(file_map.keys())
    if not target_files:
        return 0

    # BFS traversal to find connected components
    visited = set()
    total_lines = 0
    
    for start_node in target_files:
        if start_node not in visited:
            # BFS
            queue = [start_node]
            visited.add(start_node)
            while queue:
                current = queue.pop(0)
                if current in file_map:
                    total_lines += file_map[current]
                
                # Add neighbors (dependencies)
                for neighbor in G.neighbors(current):
                    if neighbor not in visited and neighbor in file_map:
                        visited.add(neighbor)
                        queue.append(neighbor)
                
                # Add reverse neighbors (dependents) to ensure full graph context
                for neighbor in G.predecessors(current):
                    if neighbor not in visited and neighbor in file_map:
                        visited.add(neighbor)
                        queue.append(neighbor)

    return total_lines

def filter_dataset(
    instances: Iterator[Dict[str, Any]], 
    min_lines: int = 500
) -> Iterator[Dict[str, Any]]:
    """
    Filter instances where the total lines in the traversed graph exceed min_lines.
    """
    for instance in instances:
        relevant_lines = calculate_relevant_lines(instance)
        if relevant_lines > min_lines:
            # Attach the calculated relevant lines to the instance
            instance["relevant_lines"] = relevant_lines
            yield instance

def validate_filtered_count(count: int, min_threshold: int = 50) -> None:
    """
    Validate that the filtered count meets the minimum threshold.
    Raises InsufficientContextError if below threshold.
    """
    if count < min_threshold:
        msg = f"Filtered dataset contains only {count} instances, which is below the required threshold of {min_threshold}."
        log_error(logger, "InsufficientContextError", msg)
        raise Exception(msg) # Using generic Exception as specific class not defined in imports, but error is loud.

def write_parquet_and_checksum(
    filtered_instances: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    version: str = "v1"
) -> Tuple[Path, str]:
    """
    Write the filtered dataset to a versioned parquet file and record its checksum.
    
    Args:
        filtered_instances: List of filtered instance dictionaries.
        output_dir: Directory to write the file. Defaults to get_data_dir().
        version: Version string for the filename.
        
    Returns:
        Tuple of (output_path, checksum_hex)
    """
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    if output_dir is None:
        output_dir = Path(get_data_dir())
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"filtered_swe_bench_{version}.parquet"
    output_path = output_dir / filename

    if not filtered_instances:
        log_error(logger, "DataLoadError", "Attempted to write empty filtered dataset.")
        raise DataLoadError("Cannot write empty dataset.")

    # Convert to DataFrame
    try:
        df = pd.DataFrame(filtered_instances)
    except Exception as e:
        log_error(logger, "DataLoadError", f"Failed to convert filtered instances to DataFrame: {e}")
        raise DataLoadError(f"Failed to convert data: {e}") from e

    # Write to Parquet
    try:
        df.to_parquet(output_path, index=False)
    except Exception as e:
        log_error(logger, "DataLoadError", f"Failed to write parquet file: {e}")
        raise DataLoadError(f"Failed to write parquet: {e}") from e

    # Calculate checksum
    try:
        with open(output_path, "rb") as f:
            content = f.read()
            checksum = hashlib.sha256(content).hexdigest()
    except Exception as e:
        log_error(logger, "DataLoadError", f"Failed to calculate checksum: {e}")
        raise DataLoadError(f"Failed to calculate checksum: {e}") from e

    # Record checksum in state directory
    state_dir = output_dir.parent / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    checksum_file = state_dir / f"checksums_{version}.json"
    
    checksum_data = {}
    if checksum_file.exists():
        try:
            with open(checksum_file, "r") as f:
                checksum_data = json.load(f)
        except json.JSONDecodeError:
            checksum_data = {}

    checksum_data[filename] = {
        "sha256": checksum,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size_bytes": len(content)
    }

    with open(checksum_file, "w") as f:
        json.dump(checksum_data, f, indent=2)

    logger.info(f"Successfully wrote {len(filtered_instances)} instances to {output_path}")
    logger.info(f"Checksum recorded: {checksum}")
    
    return output_path, checksum

def main():
    """
    Main entry point to demonstrate the loader, filter, and write pipeline.
    This function streams the real dataset, filters it, and writes the result.
    """
    set_global_seeds(42)
    logger.info("Starting Claw-SWE-Bench filtering and export pipeline.")

    loader = ClawSweBenchLoader(streaming=True)
    
    # Stream and filter
    logger.info("Streaming and filtering dataset (threshold > 500 lines)...")
    filtered_instances = []
    count = 0
    
    try:
        for instance in filter_dataset(loader.load(), min_lines=500):
            filtered_instances.append(instance)
            count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count} filtered instances...")
    except Exception as e:
        log_error(logger, "DataLoadError", f"Error during streaming/filtering: {e}")
        raise

    logger.info(f"Total filtered instances: {count}")
    
    # Validate count
    try:
        validate_filtered_count(count)
    except Exception as e:
        log_error(logger, "InsufficientContextError", str(e))
        raise

    # Write to parquet
    try:
        output_path, checksum = write_parquet_and_checksum(filtered_instances, version="v1")
        logger.info(f"Pipeline complete. Output: {output_path}, Checksum: {checksum}")
    except Exception as e:
        log_error(logger, "DataLoadError", f"Failed to write output: {e}")
        raise

if __name__ == "__main__":
    main()
