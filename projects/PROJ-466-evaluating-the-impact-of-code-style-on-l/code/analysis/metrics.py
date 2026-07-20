import math
import ast
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from pathlib import Path
import csv
import json

# --- Tokenization ---
def tokenize_code(code: str) -> List[str]:
    """
    Simple tokenizer: splits on whitespace and basic punctuation.
    Handles multi-character tokens like '==', '!=', etc.
    """
    if not code or not isinstance(code, str):
        return []
    
    # Basic replacement of punctuation with spaces to isolate tokens
    # Keep alphanumeric and underscore
    tokens = []
    current_token = []
    i = 0
    while i < len(code):
        char = code[i]
        if char.isalnum() or char == '_':
            current_token.append(char)
        else:
            if current_token:
                tokens.append("".join(current_token))
                current_token = []
            
            # Handle specific multi-char operators if needed, or treat as single token
            if char not in (' ', '\t', '\n', '\r'):
                # Check for common operators
                if i + 1 < len(code):
                    next_char = code[i+1]
                    two_char = char + next_char
                    if two_char in ('==', '!=', '<=', '>=', '&&', '||', '->'):
                        tokens.append(two_char)
                        i += 1
                    else:
                        tokens.append(char)
                else:
                    tokens.append(char)
        i += 1
    
    if current_token:
        tokens.append("".join(current_token))
    
    return tokens

def calculate_ngram_entropy(tokens: List[str], n: int = 3) -> float:
    """
    Calculates the n-gram entropy of a sequence of tokens.
    H = - sum(p(x) * log2(p(x)))
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

def calculate_pairwise_ngram_entropy(samples: List[str], n: int = 3) -> float:
    """
    Calculates the average n-gram entropy across a list of code samples.
    """
    if not samples:
        return 0.0
    
    entropies = []
    for code in samples:
        if not code:
            continue
        tokens = tokenize_code(code)
        if tokens:
            entropies.append(calculate_ngram_entropy(tokens, n))
    
    if not entropies:
        return 0.0
    
    return sum(entropies) / len(entropies)

# --- AST Graphs ---
def ast_to_graph(code: str) -> Optional[Dict[str, Any]]:
    """
    Converts Python code to a simplified graph representation (adjacency list).
    Nodes are node types; edges are parent-child relationships.
    """
    if not code:
        return None
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    
    graph = {"nodes": [], "edges": []}
    node_map = {}
    
    def traverse(node, parent_id=None):
        node_id = id(node)
        node_type = node.__class__.__name__
        
        # Store node info
        node_info = {"id": node_id, "type": node_type}
        graph["nodes"].append(node_info)
        
        # Store edge
        if parent_id is not None:
            graph["edges"].append({"source": parent_id, "target": node_id})
        
        # Traverse children
        for child in ast.iter_child_nodes(node):
            traverse(child, node_id)
    
    traverse(tree)
    return graph

def calculate_ast_edit_distance(graph1: Optional[Dict[str, Any]], graph2: Optional[Dict[str, Any]]) -> float:
    """
    Calculates a simplified edit distance between two AST graphs.
    Since full tree edit distance is complex, we use a heuristic based on:
    1. Difference in node counts
    2. Difference in edge counts
    3. Difference in node type distribution
    """
    if graph1 is None and graph2 is None:
        return 0.0
    if graph1 is None or graph2 is None:
        return 1.0 # Max distance if one is invalid
    
    nodes1 = graph1.get("nodes", [])
    nodes2 = graph2.get("nodes", [])
    edges1 = graph1.get("edges", [])
    edges2 = graph2.get("edges", [])
    
    # Node count difference (normalized)
    n1, n2 = len(nodes1), len(nodes2)
    max_nodes = max(n1, n2)
    if max_nodes == 0:
        return 0.0
    
    node_diff = abs(n1 - n2) / max_nodes
    
    # Edge count difference (normalized)
    e1, e2 = len(edges1), len(edges2)
    max_edges = max(e1, e2)
    edge_diff = abs(e1 - e2) / max_edges if max_edges > 0 else 0.0
    
    # Type distribution difference
    types1 = Counter([n["type"] for n in nodes1])
    types2 = Counter([n["type"] for n in nodes2])
    
    all_types = set(types1.keys()) | set(types2.keys())
    type_diff = 0.0
    for t in all_types:
        c1 = types1.get(t, 0)
        c2 = types2.get(t, 0)
        type_diff += abs(c1 - c2)
    
    # Normalize type diff by total nodes
    type_diff = type_diff / (n1 + n2) if (n1 + n2) > 0 else 0.0
    
    # Weighted sum
    distance = 0.4 * node_diff + 0.4 * edge_diff + 0.2 * type_diff
    return distance

def calculate_pairwise_ast_distances(samples: List[str]) -> List[float]:
    """
    Calculates pairwise AST edit distances for a list of code samples.
    Returns a list of distances for all unique pairs.
    """
    graphs = []
    for code in samples:
        g = ast_to_graph(code)
        if g is not None:
            graphs.append(g)
    
    distances = []
    for i in range(len(graphs)):
        for j in range(i + 1, len(graphs)):
            dist = calculate_ast_edit_distance(graphs[i], graphs[j])
            distances.append(dist)
    
    return distances

# --- Metrics Computation ---
def compute_metrics_for_group(samples: List[str]) -> Dict[str, float]:
    """
    Computes all metrics for a group of samples.
    """
    if not samples:
        return {
            "avg_ngram_entropy": 0.0,
            "avg_ast_edit_distance": 0.0,
            "sample_count": 0
        }
    
    avg_entropy = calculate_pairwise_ngram_entropy(samples)
    pairwise_dists = calculate_pairwise_ast_distances(samples)
    avg_dist = sum(pairwise_dists) / len(pairwise_dists) if pairwise_dists else 0.0
    
    return {
        "avg_ngram_entropy": avg_entropy,
        "avg_ast_edit_distance": avg_dist,
        "sample_count": len(samples)
    }

def compute_metrics_for_valid_samples(input_path: str, output_path: str) -> None:
    """
    Reads samples_valid.csv, computes metrics per (task_id, style) group,
    and writes to metrics_valid.csv.
    
    Dependency: T017a (samples_valid.csv must exist)
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read samples
    groups = {} # key: (task_id, style), value: list of code
    
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id', '')
            style = row.get('style', '')
            code = row.get('code', '')
            
            if not code:
                continue
            
            key = (task_id, style)
            if key not in groups:
                groups[key] = []
            groups[key].append(code)
    
    # Compute metrics
    results = []
    for (task_id, style), samples in groups.items():
        metrics = compute_metrics_for_group(samples)
        results.append({
            "task_id": task_id,
            "style": style,
            "avg_ngram_entropy": metrics["avg_ngram_entropy"],
            "avg_ast_edit_distance": metrics["avg_ast_edit_distance"],
            "sample_count": metrics["sample_count"]
        })
    
    # Write results
    fieldnames = ["task_id", "style", "avg_ngram_entropy", "avg_ast_edit_distance", "sample_count"]
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logging.info(f"Metrics for valid samples written to {output_path}")

def run_metrics_pipeline(config: Dict[str, Any]) -> None:
    """
    Orchestrates the metrics computation pipeline.
    """
    # Read config for paths
    data_dir = Path(config.get('data_dir', 'data'))
    processed_dir = data_dir / 'processed'
    
    samples_valid_path = processed_dir / 'samples_valid.csv'
    metrics_valid_path = processed_dir / 'metrics_valid.csv'
    
    compute_metrics_for_valid_samples(str(samples_valid_path), str(metrics_valid_path))