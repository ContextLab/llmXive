import math
import ast
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from pathlib import Path

import pandas as pd
import networkx as nx
from difflib import SequenceMatcher

# Re-exporting existing names for compatibility
__all__ = [
    "tokenize_code",
    "calculate_ngram_entropy",
    "calculate_pairwise_ngram_entropy",
    "ast_to_graph",
    "calculate_ast_edit_distance",
    "calculate_pairwise_ast_distances",
    "compute_metrics_for_group",
    "compute_metrics_for_valid_samples",
    "run_metrics_pipeline"
]

logger = logging.getLogger(__name__)

def tokenize_code(code: str) -> List[str]:
    """
    Simple tokenizer that splits code by whitespace and punctuation.
    Returns a list of tokens.
    """
    if not code or not isinstance(code, str):
        return []
    # Basic tokenization: split by whitespace, keep punctuation attached to words or separate
    # For entropy calculation, simple whitespace splitting is often sufficient
    return code.split()

def calculate_ngram_entropy(tokens: List[str], n: int = 2) -> float:
    """
    Calculate n-gram entropy for a list of tokens.
    H = -sum(p(x) * log2(p(x)))
    """
    if not tokens or len(tokens) < n:
        return 0.0

    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = tuple(tokens[i:i+n])
        ngrams.append(ngram)

    if not ngrams:
        return 0.0

    counts = Counter(ngrams)
    total = len(ngrams)
    entropy = 0.0

    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy

def calculate_pairwise_ngram_entropy(samples: List[str], n: int = 2) -> float:
    """
    Calculate average n-gram entropy across multiple samples.
    """
    if not samples:
        return 0.0

    total_entropy = 0.0
    count = 0

    for sample in samples:
        tokens = tokenize_code(sample)
        entropy = calculate_ngram_entropy(tokens, n)
        total_entropy += entropy
        count += 1

    return total_entropy / count if count > 0 else 0.0

def ast_to_graph(node: ast.AST) -> nx.DiGraph:
    """
    Convert an AST node to a NetworkX DiGraph for edit distance calculation.
    Nodes are labeled with node type and optional key attributes.
    Edges represent parent-child relationships.
    """
    G = nx.DiGraph()
    
    def _add_node(n, parent=None, edge_label=None):
        node_id = id(n)
        # Create a unique identifier for this node instance
        node_label = f"{n.__class__.__name__}"
        if hasattr(n, 'name') and n.name:
            node_label += f":{n.name}"
        elif hasattr(n, 'arg') and n.arg:
            node_label += f":{n.arg}"
        
        G.add_node(node_id, label=node_label)
        
        if parent is not None:
            G.add_edge(parent, node_id, label=edge_label)
        
        for field, value in ast.iter_fields(n):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        _add_node(item, node_id, field)
            elif isinstance(value, ast.AST):
                _add_node(value, node_id, field)
    
    try:
        _add_node(node)
    except Exception as e:
        logger.warning(f"Failed to convert AST to graph: {e}")
        # Return a minimal graph if conversion fails
        G.add_node(0, label="Error")
    
    return G

def calculate_ast_edit_distance(graph1: nx.DiGraph, graph2: nx.DiGraph) -> float:
    """
    Calculate a simplified AST edit distance between two graphs.
    Uses a heuristic based on node similarity and structure matching.
    Note: Full Zhang-Shasha is complex; this uses a normalized similarity metric.
    """
    if graph1.number_of_nodes() == 0 and graph2.number_of_nodes() == 0:
        return 0.0
    
    if graph1.number_of_nodes() == 0 or graph2.number_of_nodes() == 0:
        return max(graph1.number_of_nodes(), graph2.number_of_nodes())

    # Normalize by total nodes
    max_nodes = max(graph1.number_of_nodes(), graph2.number_of_nodes())
    min_nodes = min(graph1.number_of_nodes(), graph2.number_of_nodes())
    
    # Count matching node labels
    labels1 = [d['label'] for _, d in graph1.nodes(data=True)]
    labels2 = [d['label'] for _, d in graph2.nodes(data=True)]
    
    # Simple similarity: intersection over union of labels
    set1 = Counter(labels1)
    set2 = Counter(labels2)
    
    intersection = sum((set1 & set2).values())
    union = sum((set1 | set2).values())
    
    if union == 0:
        return 0.0
    
    similarity = intersection / union
    
    # Edit distance heuristic: (1 - similarity) * max_nodes
    distance = (1 - similarity) * max_nodes
    
    return distance

def calculate_pairwise_ast_distances(samples: List[str]) -> float:
    """
    Calculate average pairwise AST edit distance for a list of code samples.
    """
    if len(samples) < 2:
        return 0.0

    graphs = []
    for sample in samples:
        try:
            tree = ast.parse(sample)
            graph = ast_to_graph(tree)
            graphs.append(graph)
        except SyntaxError as e:
            logger.warning(f"Syntax error in sample: {e}")
            continue
        except Exception as e:
            logger.warning(f"Error parsing AST: {e}")
            continue

    if len(graphs) < 2:
        return 0.0

    total_distance = 0.0
    count = 0

    for i in range(len(graphs)):
        for j in range(i + 1, len(graphs)):
            dist = calculate_ast_edit_distance(graphs[i], graphs[j])
            total_distance += dist
            count += 1

    return total_distance / count if count > 0 else 0.0

def compute_metrics_for_group(samples: List[str]) -> Dict[str, float]:
    """
    Compute all metrics for a group of samples.
    Returns a dictionary with entropy and AST distance.
    """
    if not samples:
        return {
            "ngram_entropy": 0.0,
            "ast_edit_distance": 0.0
        }

    entropy = calculate_pairwise_ngram_entropy(samples)
    ast_dist = calculate_pairwise_ast_distances(samples)

    return {
        "ngram_entropy": entropy,
        "ast_edit_distance": ast_dist
    }

def compute_metrics_for_valid_samples(input_path: str, output_path: str) -> None:
    """
    T025 Implementation: Compute metrics for VALID samples only.
    Reads from data/processed/samples_valid.csv and writes to data/processed/metrics_valid.csv.
    
    This function:
    1. Loads valid samples from the CSV produced by T017b.
    2. Groups samples by task_id and style.
    3. Computes pairwise n-gram entropy and AST edit distance for each group.
    4. Writes the results to the output CSV.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading valid samples from {input_path}")
    
    # Read valid samples
    df = pd.read_csv(input_file)
    
    if df.empty:
        logger.warning("No valid samples found in input file. Creating empty output.")
        df_metrics = pd.DataFrame(columns=["task_id", "style", "ngram_entropy", "ast_edit_distance", "sample_count"])
        df_metrics.to_csv(output_file, index=False)
        return

    # Group by task_id and style
    groups = df.groupby(["task_id", "style"])
    
    results = []
    
    for (task_id, style), group_df in groups:
        samples = group_df["code"].dropna().tolist()
        
        if not samples:
            logger.warning(f"No samples found for task {task_id}, style {style}")
            continue
        
        metrics = compute_metrics_for_group(samples)
        
        results.append({
            "task_id": task_id,
            "style": style,
            "ngram_entropy": metrics["ngram_entropy"],
            "ast_edit_distance": metrics["ast_edit_distance"],
            "sample_count": len(samples)
        })
        
        logger.debug(f"Computed metrics for task {task_id}, style {style}: "
                     f"entropy={metrics['ngram_entropy']:.4f}, "
                     f"ast_dist={metrics['ast_edit_distance']:.4f}")
    
    # Create output DataFrame
    df_metrics = pd.DataFrame(results)
    
    if df_metrics.empty:
        logger.warning("No metrics computed. Creating empty output.")
        df_metrics = pd.DataFrame(columns=["task_id", "style", "ngram_entropy", "ast_edit_distance", "sample_count"])
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df_metrics.to_csv(output_file, index=False)
    
    logger.info(f"Metrics for valid samples saved to {output_path}")
    logger.info(f"Total groups processed: {len(df_metrics)}")

def run_metrics_pipeline() -> None:
    """
    Main entry point for the metrics pipeline.
    Executes T025: Compute metrics for valid samples.
    """
    input_path = "data/processed/samples_valid.csv"
    output_path = "data/processed/metrics_valid.csv"
    
    try:
        compute_metrics_for_valid_samples(input_path, output_path)
    except FileNotFoundError as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        raise