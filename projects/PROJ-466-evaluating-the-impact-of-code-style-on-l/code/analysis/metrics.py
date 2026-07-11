import math
import ast
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from pathlib import Path

from utils.logger import log_generation_error
from utils.metrics_utils import safe_parse_ast, detect_zero_variance

logger = logging.getLogger(__name__)

def tokenize_code(code: str) -> List[str]:
    """
    Tokenize code into a list of tokens.
    Simple whitespace and punctuation tokenization.
    """
    if not code or not isinstance(code, str):
        return []
    
    # Basic tokenization: split by whitespace and keep punctuation
    tokens = []
    current_token = ""
    for char in code:
        if char.isspace():
            if current_token:
                tokens.append(current_token)
                current_token = ""
            tokens.append(char)
        elif char in "()[]{}.,;:+-*/%=<>!&|^~":
            if current_token:
                tokens.append(current_token)
                current_token = ""
            tokens.append(char)
        else:
            current_token += char
    
    if current_token:
        tokens.append(current_token)
    
    return [t for t in tokens if not t.isspace() or t == '\n']

def calculate_ngram_entropy(tokens: List[str], n: int = 2) -> float:
    """
    Calculate n-gram entropy for a list of tokens.
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
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_pairwise_ngram_entropy(samples: List[str], n: int = 2) -> float:
    """
    Calculate average n-gram entropy across all samples.
    """
    if not samples:
        return 0.0
    
    entropies = []
    for sample in samples:
        tokens = tokenize_code(sample)
        if tokens:
            entropy = calculate_ngram_entropy(tokens, n)
            entropies.append(entropy)
    
    if not entropies:
        return 0.0
    
    return sum(entropies) / len(entropies)

def ast_to_graph(tree: ast.AST) -> Dict[int, Dict[str, Any]]:
    """
    Convert an AST tree to a graph representation.
    Returns a dictionary of nodes where key is node id and value is node info.
    """
    nodes = {}
    node_id = 0
    
    def _process_node(node: ast.AST, parent_id: Optional[int] = None) -> int:
        nonlocal node_id
        current_id = node_id
        node_id += 1
        
        node_info = {
            'type': type(node).__name__,
            'children': [],
            'parent': parent_id
        }
        
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        child_id = _process_node(item, current_id)
                        node_info['children'].append(child_id)
            elif isinstance(value, ast.AST):
                child_id = _process_node(value, current_id)
                node_info['children'].append(child_id)
        
        nodes[current_id] = node_info
        return current_id
    
    if tree:
        _process_node(tree)
    
    return nodes

def calculate_ast_edit_distance(graph1: Dict[int, Dict[str, Any]], graph2: Dict[int, Dict[str, Any]]) -> int:
    """
    Calculate a simplified AST edit distance between two graph representations.
    Uses a basic node count difference and structural similarity heuristic.
    """
    if not graph1 and not graph2:
        return 0
    if not graph1:
        return len(graph2)
    if not graph2:
        return len(graph1)
    
    # Simple heuristic: count node type differences
    types1 = Counter(node['type'] for node in graph1.values())
    types2 = Counter(node['type'] for node in graph2.values())
    
    all_types = set(types1.keys()) | set(types2.keys())
    distance = 0
    
    for t in all_types:
        distance += abs(types1.get(t, 0) - types2.get(t, 0))
    
    # Add structural difference based on children count
    for node_id, node in graph1.items():
        if node_id in graph2:
            children_diff = abs(len(node['children']) - len(graph2[node_id]['children']))
            distance += children_diff
    
    return distance

def calculate_pairwise_ast_distances(samples: List[str]) -> List[Tuple[int, int, float]]:
    """
    Calculate pairwise AST edit distances for all samples.
    Returns list of (index1, index2, distance) tuples.
    """
    if len(samples) < 2:
        return []
    
    graphs = []
    for i, sample in enumerate(samples):
        try:
            tree = safe_parse_ast(sample)
            if tree:
                graph = ast_to_graph(tree)
                graphs.append((i, graph))
            else:
                graphs.append((i, None))
        except Exception as e:
            logger.warning(f"Failed to parse AST for sample {i}: {e}")
            graphs.append((i, None))
    
    distances = []
    for i in range(len(graphs)):
        for j in range(i + 1, len(graphs)):
            idx1, graph1 = graphs[i]
            idx2, graph2 = graphs[j]
            
            if graph1 is None or graph2 is None:
                # Cannot compute distance if one graph is missing
                continue
            
            dist = calculate_ast_edit_distance(graph1, graph2)
            distances.append((idx1, idx2, dist))
    
    return distances

def compute_metrics_for_group(task_id: str, style: str, samples: List[str]) -> Dict[str, Any]:
    """
    Compute all metrics for a group of samples (same task and style).
    Returns a dictionary with metrics.
    """
    if not samples:
        return {
            'task_id': task_id,
            'style': style,
            'n_samples': 0,
            'avg_ngram_entropy': 0.0,
            'avg_ast_distance': 0.0,
            'has_variance': False
        }
    
    # Calculate n-gram entropy
    avg_ngram_entropy = calculate_pairwise_ngram_entropy(samples)
    
    # Calculate AST distances
    ast_distances = calculate_pairwise_ast_distances(samples)
    
    if ast_distances:
        avg_ast_distance = sum(d[2] for d in ast_distances) / len(ast_distances)
    else:
        avg_ast_distance = 0.0
    
    # Check for zero variance
    # Variance exists if we have at least 2 samples and they are not all identical
    has_variance = False
    if len(samples) >= 2:
        # Check if all samples are identical
        unique_samples = set(samples)
        if len(unique_samples) > 1:
            has_variance = True
        else:
            # All samples are identical - zero variance
            has_variance = False
            logger.warning(f"Zero Variance detected for task {task_id}, style {style}: all samples are identical")
    elif len(samples) == 1:
        # Single sample - cannot compute pairwise metrics, but technically no variance
        has_variance = False
        logger.warning(f"Zero Variance detected for task {task_id}, style {style}: only one sample")
    
    return {
        'task_id': task_id,
        'style': style,
        'n_samples': len(samples),
        'avg_ngram_entropy': avg_ngram_entropy,
        'avg_ast_distance': avg_ast_distance,
        'has_variance': has_variance,
        'n_pairs': len(ast_distances)
    }