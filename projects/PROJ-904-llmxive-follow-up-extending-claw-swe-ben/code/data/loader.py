"""
ClawSweBenchLoader: Streaming data fetch, hybrid IR-seeding, graph traversal, and filtering.
"""
import os
import re
import ast
import sys
import hashlib
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field

import networkx as nx
import pandas as pd
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import numpy as np

# Import from project config and models
from config import get_data_dir, get_output_dir, set_global_seeds
from models.task_instance import TaskInstance

logger = logging.getLogger(__name__)

@dataclass
class ParsedIssue:
    """Parsed issue description with extracted file paths."""
    original_text: str
    file_paths: List[str] = field(default_factory=list)
    semantic_query: Optional[str] = None

class ClawSweBenchLoader:
    """
    Loader for Claw-SWE-Bench dataset with streaming, hybrid IR-seeding,
    and graph-based context expansion.
    """

    def __init__(self, dataset_name: str = "princeton-nlp/Claw-SWE-Bench", seed: int = 42):
        """
        Initialize the loader.

        Args:
            dataset_name: HuggingFace dataset identifier.
            seed: Random seed for reproducibility.
        """
        self.dataset_name = dataset_name
        self.seed = seed
        set_global_seeds(seed)
        
        # Initialize CodeBERT model for semantic retrieval
        # Using a frozen generic model as specified
        self.semantic_model = SentenceTransformer('microsoft/codebert-base')
        
        # Common file extensions for Python projects
        self.python_extensions = {'.py', '.pyx', '.pxd'}
        
        # Regex to extract file paths from issue descriptions
        # Matches patterns like "file.py", "src/module/file.py", "./path/to/file.py"
        self.file_path_pattern = re.compile(
            r'(?:^|[\s"\'`])([a-zA-Z0-9_./\-]+\.py)(?:[\s"\'`]|$)'
        )

    def _extract_file_paths(self, description: str) -> List[str]:
        """Extract file paths from issue description text."""
        matches = self.file_path_pattern.findall(description)
        # Normalize paths (remove leading ./ if present)
        normalized = [os.path.normpath(m.lstrip('./')) for m in matches]
        return list(set(normalized))  # Deduplicate

    def _semantic_retrieve_top_k(
        self, 
        description: str, 
        all_files: List[str], 
        k: int = 5
    ) -> List[str]:
        """
        Use CodeBERT to embed the description and retrieve top-k similar files.
        
        Args:
            description: The issue description text.
            all_files: List of all available file paths in the repo.
            k: Number of files to retrieve.
            
        Returns:
            List of top-k file paths.
        """
        if not all_files:
            return []
        
        # Embed the query
        query_embedding = self.semantic_model.encode(
            description, 
            convert_to_numpy=True, 
            show_progress_bar=False
        )
        
        # Embed all file paths (using just the filename or path as proxy)
        # In a real scenario, we might embed file contents, but here we use paths
        file_embeddings = self.semantic_model.encode(
            all_files, 
            convert_to_numpy=True, 
            show_progress_bar=False
        )
        
        # Compute cosine similarities
        similarities = np.dot(file_embeddings, query_embedding) / (
            np.linalg.norm(file_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        return [all_files[i] for i in top_k_indices]

    def _get_repo_files(self, instance_data: Dict[str, Any]) -> List[str]:
        """
        Extract all file paths from the instance data.
        
        Assumes instance_data contains a 'repo_files' or similar field.
        If not available, returns an empty list (fallback to semantic-only).
        """
        # Try common keys where repo files might be stored
        for key in ['repo_files', 'files', 'file_list', 'all_files']:
            if key in instance_data and isinstance(instance_data[key], list):
                return instance_data[key]
        
        # If not found, try to parse from a text field if it exists
        if 'file_list_text' in instance_data:
            text = instance_data['file_list_text']
            return [f for f in text.split() if f.endswith('.py')]
        
        return []

    def _parse_imports(self, file_content: str) -> List[str]:
        """
        Parse import statements from Python file content.
        
        Returns a list of imported module names (simplified).
        """
        imports = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
        except SyntaxError:
            # If parsing fails, return empty list
            pass
        return imports

    def _traverse_import_graph(
        self, 
        seed_files: List[str], 
        file_contents: Dict[str, str], 
        max_depth: int = 2
    ) -> Set[str]:
        """
        Traverse the import graph starting from seed files.
        
        Args:
            seed_files: Initial set of files to start from.
            file_contents: Dict mapping file paths to their content.
            max_depth: Maximum depth of traversal.
            
        Returns:
            Set of all reachable file paths.
        """
        visited = set(seed_files)
        current_level = set(seed_files)
        
        for _ in range(max_depth):
            next_level = set()
            for file_path in current_level:
                if file_path not in file_contents:
                    continue
                
                content = file_contents[file_path]
                imports = self._parse_imports(content)
                
                for imp in imports:
                    # Try to find corresponding .py file
                    potential_paths = [
                        f"{imp}.py",
                        f"{imp}/__init__.py",
                        os.path.join(imp, "__init__.py")
                    ]
                    
                    for p in potential_paths:
                        if p in file_contents and p not in visited:
                            visited.add(p)
                            next_level.add(p)
            
            if not next_level:
                break
            current_level = next_level
        
        return visited

    def _calculate_line_count(self, file_content: str) -> int:
        """Count non-empty, non-comment lines in a file."""
        lines = file_content.split('\n')
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                count += 1
        return count

    def load_and_process_instance(
        self, 
        instance: Dict[str, Any]
    ) -> Optional[TaskInstance]:
        """
        Process a single dataset instance with hybrid IR and graph traversal.
        
        Args:
            instance: Raw dataset instance.
            
        Returns:
            TaskInstance if complexity > 500 lines, else None.
        """
        try:
            # Extract issue description
            description = instance.get('issue_description', '')
            if not description:
                logger.warning("Empty issue description, skipping instance")
                return None
            
            # Step 1: Parse issue description for file paths
            file_paths = self._extract_file_paths(description)
            
            # Step 2: If no file paths found, use semantic retrieval
            if not file_paths:
                all_files = self._get_repo_files(instance)
                if all_files:
                    file_paths = self._semantic_retrieve_top_k(
                        description, all_files, k=5
                    )
                    logger.info(f"Using semantic retrieval: {file_paths}")
                else:
                    logger.warning("No files found for semantic retrieval, skipping")
                    return None
            
            # Step 3: Get file contents (simulated from instance data)
            # In a real scenario, this would fetch from the repo
            file_contents = {}
            for fp in file_paths:
                # Try to find content in instance data
                content_key = f"content_{fp.replace('/', '_').replace('.', '_')}"
                if content_key in instance:
                    file_contents[fp] = instance[content_key]
                elif 'file_contents' in instance and fp in instance['file_contents']:
                    file_contents[fp] = instance['file_contents'][fp]
                else:
                    # Placeholder: simulate content for demo (in real run, this would fail or fetch)
                    # For the real implementation, we assume the dataset provides content
                    file_contents[fp] = instance.get('sample_content', '# Placeholder content')
            
            # Step 4: Traverse import graph
        except Exception as e:
            logger.error(f"Error processing instance: {e}", exc_info=True)
            return None
        
        try:
            expanded_files = self._traverse_import_graph(
                file_paths, file_contents, max_depth=2
            )
            
            # Step 5: Calculate total lines
            total_lines = 0
            for fp in expanded_files:
                if fp in file_contents:
                    total_lines += self._calculate_line_count(file_contents[fp])
            
            # Step 6: Filter based on complexity threshold
            if total_lines <= 500:
                logger.debug(f"Instance complexity {total_lines} <= 500, skipping")
                return None
            
            # Create TaskInstance
            task_instance = TaskInstance(
                instance_id=instance.get('instance_id', 'unknown'),
                issue_description=description,
                relevant_files=list(expanded_files),
                total_lines=total_lines,
                strategy='hybrid_ir_graph',
                model_size='1b'  # Default for baseline
            )
            
            return task_instance
            
        except Exception as e:
            logger.error(f"Error in graph traversal or line counting: {e}", exc_info=True)
            return None

def calculate_relevant_lines(
    instances: List[Dict[str, Any]], 
    loader: ClawSweBenchLoader
) -> List[Tuple[Dict[str, Any], int]]:
    """
    Calculate relevant line counts for a batch of instances.
    
    Returns list of (instance, line_count) tuples.
    """
    results = []
    for inst in instances:
        task = loader.load_and_process_instance(inst)
        if task:
            results.append((inst, task.total_lines))
    return results

def filter_dataset(
    instances: List[Dict[str, Any]], 
    min_lines: int = 500,
    loader: Optional[ClawSweBenchLoader] = None
) -> List[Dict[str, Any]]:
    """
    Filter dataset for instances with > min_lines relevant code.
    
    Args:
        instances: List of raw dataset instances.
        min_lines: Minimum line count threshold.
        loader: Optional ClawSweBenchLoader instance.
        
    Returns:
        Filtered list of instances.
    """
    if loader is None:
        loader = ClawSweBenchLoader()
    
    filtered = []
    for inst in instances:
        task = loader.load_and_process_instance(inst)
        if task and task.total_lines > min_lines:
            filtered.append(inst)
    
    logger.info(f"Filtered dataset: {len(filtered)} instances passed (> {min_lines} lines)")
    return filtered

def validate_filtered_count(
    original_count: int, 
    filtered_count: int, 
    min_lines: int
) -> bool:
    """
    Validate that filtering produced a reasonable result.
    
    Returns True if filtered count is > 0 and < original count.
    """
    if filtered_count == 0:
        logger.error(f"No instances passed filter (> {min_lines} lines)")
        return False
    if filtered_count >= original_count:
        logger.warning("All instances passed filter, expected some filtering")
        return False
    return True

def write_parquet_and_checksum(
    instances: List[Dict[str, Any]], 
    output_path: str,
    min_lines: int
) -> str:
    """
    Write filtered instances to Parquet and return checksum.
    
    Args:
        instances: List of filtered instances.
        output_path: Path to output Parquet file.
        min_lines: The filter threshold used.
        
    Returns:
        SHA256 checksum of the output file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(instances)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote {len(instances)} instances to {output_path}")
    
    # Calculate checksum
    with open(output_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    logger.info(f"Checksum for {output_path}: {checksum}")
    return checksum

def record_derivation(
    output_path: str, 
    checksum: str, 
    min_lines: int, 
    total_original: int, 
    total_filtered: int,
    state_dir: Optional[str] = None
) -> str:
    """
    Record derivation metadata in state YAML.
    
    Args:
        output_path: Path to the generated Parquet file.
        checksum: SHA256 checksum of the file.
        min_lines: Filter threshold.
        total_original: Original dataset size.
        total_filtered: Filtered dataset size.
        state_dir: Directory for state files.
        
    Returns:
        Path to the state YAML file.
    """
    if state_dir is None:
        state_dir = str(get_output_dir() / "state")
    
    os.makedirs(state_dir, exist_ok=True)
    
    state_file = Path(state_dir) / "loader_derivation.yaml"
    
    state_data = {
        "dataset": "Claw-SWE-Bench",
        "output_file": output_path,
        "checksum": checksum,
        "filter_criteria": {
            "min_lines": min_lines,
            "method": "hybrid_ir_graph_traversal"
        },
        "statistics": {
            "original_count": total_original,
            "filtered_count": total_filtered,
            "retention_rate": round(total_filtered / total_original, 4) if total_original > 0 else 0
        },
        "derivation_timestamp": str(pd.Timestamp.now())
    }
    
    with open(state_file, 'w') as f:
        # Simple YAML-like format (using json for simplicity, can be parsed as YAML)
        json.dump(state_data, f, indent=2)
    
    logger.info(f"Recorded derivation in {state_file}")
    return str(state_file)

def main():
    """
    Main entry point for the loader script.
    
    Usage:
        python code/data/loader.py --filter-min-lines 500 --output data/filtered_swe_bench.parquet
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="ClawSweBench Loader and Filter")
    parser.add_argument(
        "--filter-min-lines", 
        type=int, 
        default=500,
        help="Minimum line count for filtering (default: 500)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/filtered_swe_bench_v1.parquet",
        help="Output Parquet file path"
    )
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="princeton-nlp/Claw-SWE-Bench",
        help="HuggingFace dataset name"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting ClawSweBenchLoader with min_lines={args.filter_min_lines}")
    
    # Initialize loader
    loader = ClawSweBenchLoader(dataset_name=args.dataset, seed=args.seed)
    
    # Load dataset with streaming
    logger.info(f"Loading dataset: {args.dataset} (streaming=True)")
    try:
        dataset = load_dataset(
            args.dataset, 
            split="train", 
            streaming=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(f"Dataset fetch failed: {e}")
    
    # Convert to list (streaming allows iteration without full download)
    # For large datasets, we iterate in chunks
    instances = []
    count = 0
    for item in dataset:
        instances.append(item)
        count += 1
        if count % 1000 == 0:
            logger.info(f"Loaded {count} instances...")
    
    total_original = len(instances)
    logger.info(f"Total instances loaded: {total_original}")
    
    # Filter dataset
    filtered_instances = filter_dataset(
        instances, 
        min_lines=args.filter_min_lines, 
        loader=loader
    )
    
    # Validate
    if not validate_filtered_count(total_original, len(filtered_instances), args.filter_min_lines):
        raise RuntimeError("Filtering validation failed")
    
    # Write output
    output_path = args.output
    checksum = write_parquet_and_checksum(
        filtered_instances, 
        output_path, 
        args.filter_min_lines
    )
    
    # Record derivation
    record_derivation(
        output_path, 
        checksum, 
        args.filter_min_lines, 
        total_original, 
        len(filtered_instances)
    )
    
    logger.info(f"Loader completed successfully. Output: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
