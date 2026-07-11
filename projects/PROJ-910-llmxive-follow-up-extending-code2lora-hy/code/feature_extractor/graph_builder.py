"""
Graph Builder Module for Code2LoRA Hypernetwork.

This module computes import graph centrality metrics using networkx.
It implements FR-001: Extract static AST features including graph-based metrics.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

import networkx as nx


class ImportGraphBuilder:
    """
    Builds an import dependency graph for a given codebase directory.
    """

    def __init__(self, root_dir: Path):
        """
        Initialize the builder with the root directory of the repository.

        Args:
            root_dir: Path to the root directory containing Python files.
        """
        self.root_dir = root_dir
        self.graph = nx.DiGraph()
        self.node_files: Dict[str, str] = {}  # Maps module name to file path

    def _get_module_name(self, file_path: Path) -> str:
        """
        Convert a file path to a Python module name relative to root.

        Args:
            file_path: Absolute path to a Python file.

        Returns:
            Dot-separated module name (e.g., 'package.subpackage.module').
        """
        try:
            rel_path = file_path.relative_to(self.root_dir)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == '__init__':
                parts = parts[:-1]
            return '.'.join(parts) if parts else 'root'
        except ValueError:
            # File is outside root_dir, return absolute path hash or similar
            return str(file_path)

    def _scan_files(self) -> List[Path]:
        """
        Scan the root directory for all Python files.

        Returns:
            List of Path objects for all .py files found.
        """
        py_files = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        return py_files

    def _parse_imports(self, file_path: Path) -> Set[str]:
        """
        Parse a Python file and extract imported module names.

        Args:
            file_path: Path to the Python file.

        Returns:
            Set of imported module names (strings).
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            # Skip malformed files or encoding issues
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                elif node.level > 0:
                    # Relative import, resolve later if needed
                    # For now, we'll treat relative imports as local
                    pass
        return imports

    def build(self) -> nx.DiGraph:
        """
        Build the import dependency graph for the entire repository.

        Returns:
            A directed graph where nodes are modules and edges represent imports.
        """
        py_files = self._scan_files()

        # Add all files as nodes
        for file_path in py_files:
            module_name = self._get_module_name(file_path)
            self.graph.add_node(module_name)
            self.node_files[module_name] = str(file_path)

        # Add edges based on imports
        for file_path in py_files:
            source_module = self._get_module_name(file_path)
            imports = self._parse_imports(file_path)

            for imp in imports:
                # Check if the imported module exists in our repository
                if imp in self.node_files:
                    self.graph.add_edge(source_module, imp)
                # Note: We ignore external imports (e.g., 'os', 'sys') for now
                # as they don't contribute to internal repository structure metrics.

        return self.graph

def compute_centrality_metrics(graph: nx.DiGraph) -> Dict[str, Dict[str, float]]:
    """
    Compute centrality metrics for nodes in the import graph.

    Args:
        graph: A directed graph representing module dependencies.

    Returns:
        A dictionary mapping module names to their centrality scores.
        Keys include 'in_degree', 'out_degree', 'betweenness', 'closeness'.
    """
    if not graph.nodes():
        return {}

    metrics = {}

    # Degree centrality
    in_deg = nx.in_degree_centrality(graph)
    out_deg = nx.out_degree_centrality(graph)

    # Betweenness centrality
    try:
        betweenness = nx.betweenness_centrality(graph, normalized=True)
    except nx.NetworkXError:
        betweenness = {node: 0.0 for node in graph.nodes()}

    # Closeness centrality (only for weakly connected components if graph is disconnected)
    try:
        closeness = nx.closeness_centrality(graph, wf_improved=True)
    except nx.NetworkXError:
        closeness = {node: 0.0 for node in graph.nodes()}

    for node in graph.nodes():
        metrics[node] = {
            'in_degree': in_deg.get(node, 0.0),
            'out_degree': out_deg.get(node, 0.0),
            'betweenness': betweenness.get(node, 0.0),
            'closeness': closeness.get(node, 0.0)
        }

    return metrics

def extract_graph_features(root_dir: Path) -> Dict[str, Any]:
    """
    Extract graph-based features from a repository directory.

    This function builds the import graph, computes centrality metrics,
    and aggregates them into a feature vector.

    Args:
        root_dir: Path to the root directory of the repository.

    Returns:
        Dictionary containing graph features:
        - 'num_nodes': Total number of modules
        - 'num_edges': Total number of import relationships
        - 'avg_in_degree': Average in-degree centrality
        - 'avg_out_degree': Average out-degree centrality
        - 'max_betweenness': Maximum betweenness centrality
        - 'max_closeness': Maximum closeness centrality
        - 'centrality_scores': Per-node centrality metrics
    """
    builder = ImportGraphBuilder(root_dir)
    graph = builder.build()

    if not graph.nodes():
        return {
            'num_nodes': 0,
            'num_edges': 0,
            'avg_in_degree': 0.0,
            'avg_out_degree': 0.0,
            'max_betweenness': 0.0,
            'max_closeness': 0.0,
            'centrality_scores': {}
        }

    centrality_metrics = compute_centrality_metrics(graph)

    in_degrees = [m['in_degree'] for m in centrality_metrics.values()]
    out_degrees = [m['out_degree'] for m in centrality_metrics.values()]
    betweens = [m['betweenness'] for m in centrality_metrics.values()]
    closenesses = [m['closeness'] for m in centrality_metrics.values()]

    return {
        'num_nodes': graph.number_of_nodes(),
        'num_edges': graph.number_of_edges(),
        'avg_in_degree': sum(in_degrees) / len(in_degrees) if in_degrees else 0.0,
        'avg_out_degree': sum(out_degrees) / len(out_degrees) if out_degrees else 0.0,
        'max_betweenness': max(betweens) if betweens else 0.0,
        'max_closeness': max(closenesses) if closenesses else 0.0,
        'centrality_scores': centrality_metrics
    }

def get_graph_feature_vector_size() -> int:
    """
    Return the size of the fixed-size feature vector extracted from graph metrics.

    This corresponds to the number of aggregated metrics returned by
    extract_graph_features (excluding the per-node centrality_scores dict).

    Returns:
        Integer representing the number of scalar graph features.
    """
    # num_nodes, num_edges, avg_in_degree, avg_out_degree, max_betweenness, max_closeness
    return 6

def get_aggregated_graph_features(root_dir: Path) -> List[float]:
    """
    Extract a fixed-size vector of aggregated graph features.

    Args:
        root_dir: Path to the root directory of the repository.

    Returns:
        List of float values representing graph features in a fixed order.
    """
    features = extract_graph_features(root_dir)
    return [
        features['num_nodes'],
        features['num_edges'],
        features['avg_in_degree'],
        features['avg_out_degree'],
        features['max_betweenness'],
        features['max_closeness']
    ]