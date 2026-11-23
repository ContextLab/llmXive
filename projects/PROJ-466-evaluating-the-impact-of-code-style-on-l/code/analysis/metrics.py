import math
import ast
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx

# Imports from utils as per API surface
from utils.metrics_utils import safe_parse_ast, detect_zero_variance
from utils.logger import log_generation_error

logger = logging.getLogger(__name__)

def tokenize_code(code: str) -> List[str]:
    """Simple tokenization by splitting on whitespace and punctuation."""
    if not code or not isinstance(code, str):
        return []
    # Basic tokenization: split by whitespace and non-alphanumeric chars
    # This is a simplified approach for n-gram entropy calculation
    tokens = []
    current_token = ""
    for char in code:
        if char.isalnum() or char == '_':
            current_token += char
        else:
            if current_token:
                tokens.append(current_token)
                current_token = ""
            if not char.isspace():
                tokens.append(char)
    if current_token:
        tokens.append(current_token)
    return tokens

def calculate_ngram_entropy(tokens: List[str], n: int = 2) -> float:
    """Calculate n-gram entropy for a sequence of tokens."""
    if len(tokens) < n:
        return 0.0
    
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = tuple(tokens[i:i+n])
        ngrams.append(ngram)
    
    if not ngrams:
        return 0.0
    
    counter = Counter(ngrams)
    total = len(ngrams)
    
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_pairwise_ngram_entropy(codes: List[str], n: int = 2) -> float:
    """Calculate average pairwise n-gram entropy for a list of code samples."""
    if len(codes) < 2:
        return 0.0
    
    entropies = []
    for code in codes:
        tokens = tokenize_code(code)
        if tokens:
            entropies.append(calculate_ngram_entropy(tokens, n))
    
    if not entropies:
        return 0.0
    
    return np.mean(entropies)

def ast_to_graph(tree: ast.AST) -> nx.DiGraph:
    """Convert an AST to a NetworkX DiGraph for edit distance calculation."""
    G = nx.DiGraph()
    
    def add_nodes(node, parent_id=None):
        node_id = id(node)
        node_type = type(node).__name__
        G.add_node(node_id, type=node_type)
        
        if parent_id is not None:
            G.add_edge(parent_id, node_id)
        
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        add_nodes(item, node_id)
            elif isinstance(value, ast.AST):
                add_nodes(value, node_id)
    
    add_nodes(tree)
    return G

def calculate_ast_edit_distance(graph1: nx.DiGraph, graph2: nx.DiGraph) -> float:
    """Calculate a simplified AST edit distance between two graphs."""
    if graph1.number_of_nodes() == 0 and graph2.number_of_nodes() == 0:
        return 0.0
    
    if graph1.number_of_nodes() == 0:
        return float(graph2.number_of_nodes())
    
    if graph2.number_of_nodes() == 0:
        return float(graph1.number_of_nodes())
    
    # Simplified edit distance: symmetric difference of node types + edge structure
    nodes1 = set(node for _, data in graph1.nodes(data=True) for _ in [data.get('type', '')])
    nodes2 = set(node for _, data in graph2.nodes(data=True) for _ in [data.get('type', '')])
    
    # Count node type differences
    node_diff = len(nodes1.symmetric_difference(nodes2))
    
    # Count edge differences
    edges1 = set(graph1.edges())
    edges2 = set(graph2.edges())
    edge_diff = len(edges1.symmetric_difference(edges2))
    
    # Normalize by total size
    total_size = graph1.number_of_nodes() + graph2.number_of_nodes()
    if total_size == 0:
        return 0.0
    
    return (node_diff + edge_diff) / total_size

def calculate_pairwise_ast_distances(codes: List[str]) -> float:
    """Calculate average pairwise AST edit distance for a list of code samples."""
    graphs = []
    for code in codes:
        tree = safe_parse_ast(code)
        if tree is not None:
            graphs.append(ast_to_graph(tree))
    
    if len(graphs) < 2:
        return 0.0
    
    distances = []
    for i in range(len(graphs)):
        for j in range(i + 1, len(graphs)):
            dist = calculate_ast_edit_distance(graphs[i], graphs[j])
            distances.append(dist)
    
    if not distances:
        return 0.0
    
    return np.mean(distances)

def compute_metrics_for_group(codes: List[str]) -> Dict[str, float]:
    """Compute diversity metrics for a group of code samples."""
    if not codes:
        return {"mean_ngram_entropy": 0.0, "mean_ast_distance": 0.0, "sample_count": 0}
    
    ngram_entropy = calculate_pairwise_ngram_entropy(codes)
    ast_distance = calculate_pairwise_ast_distances(codes)
    
    return {
        "mean_ngram_entropy": ngram_entropy,
        "mean_ast_distance": ast_distance,
        "sample_count": len(codes)
    }

def compute_metrics_for_valid_samples(df: pd.DataFrame) -> pd.DataFrame:
    """Compute metrics for valid samples only, aggregated per task/style."""
    if df.empty:
        return pd.DataFrame(columns=['task_id', 'style', 'mean_ngram_entropy', 'mean_ast_distance', 'sample_count'])
    
    # Filter for valid samples
    valid_df = df[df['pass_status'] == True].copy()
    
    if valid_df.empty:
        logger.warning("No valid samples found for metrics computation")
        return pd.DataFrame(columns=['task_id', 'style', 'mean_ngram_entropy', 'mean_ast_distance', 'sample_count'])
    
    results = []
    
    # Group by task_id and style
    grouped = valid_df.groupby(['task_id', 'style'])
    
    for (task_id, style), group in grouped:
        codes = group['code'].tolist()
        metrics = compute_metrics_for_group(codes)
        
        results.append({
            'task_id': task_id,
            'style': style,
            'mean_ngram_entropy': metrics['mean_ngram_entropy'],
            'mean_ast_distance': metrics['mean_ast_distance'],
            'sample_count': metrics['sample_count']
        })
    
    return pd.DataFrame(results)

def run_metrics_pipeline(input_path: str, output_path: str, valid_only: bool = False) -> None:
    """
    Run the metrics computation pipeline.
    
    Args:
        input_path: Path to the input CSV file (samples_all.csv or samples_valid.csv)
        output_path: Path to save the output metrics CSV
        valid_only: If True, compute metrics only for valid samples (pass_status=True)
                   If False, compute metrics for all samples (ignoring pass_status)
    """
    logger.info(f"Starting metrics pipeline: {input_path} -> {output_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    if valid_only:
        # Compute metrics for valid samples only
        metrics_df = compute_metrics_for_valid_samples(df)
    else:
        # Compute metrics for ALL samples (ignoring pass_status)
        # This is the T024a requirement: "ignoring pass_status column"
        if 'pass_status' in df.columns:
            # We still group by task_id and style, but include all rows
            pass
        
        results = []
        grouped = df.groupby(['task_id', 'style'])
        
        for (task_id, style), group in grouped:
            codes = group['code'].tolist()
            metrics = compute_metrics_for_group(codes)
            
            results.append({
                'task_id': task_id,
                'style': style,
                'mean_ngram_entropy': metrics['mean_ngram_entropy'],
                'mean_ast_distance': metrics['mean_ast_distance'],
                'sample_count': metrics['sample_count']
            })
        
        metrics_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path} with {len(metrics_df)} rows")

def run_metrics_pipeline_all(input_path: str, output_path: str) -> None:
    """
    Compute metrics for ALL generated samples (T024a).
    Reads samples_all.csv, ignores pass_status, aggregates per task/style.
    """
    run_metrics_pipeline(input_path, output_path, valid_only=False)

def run_metrics_pipeline_valid(input_path: str, output_path: str) -> None:
    """
    Compute metrics for VALID samples only (T017b).
    Reads samples_valid.csv (which already has pass_status=True), aggregates per task/style.
    """
    # Since samples_valid.csv is already filtered, we can just use the standard pipeline
    # but we need to ensure we're not double-filtering if pass_status column exists
    run_metrics_pipeline(input_path, output_path, valid_only=False)