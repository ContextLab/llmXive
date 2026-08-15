"""
Graph Builder Module for AST-based Adapter Generation.

This module implements the construction of import graphs from Python source code
and computes centrality metrics using NetworkX. It fulfills FR-001 by extracting
structural features that capture the dependency relationships within a repository.

The module is designed to work in conjunction with ast_parser.py to provide
a comprehensive feature set for the hypernetwork adapter generation.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ImportGraphBuilder:
    """
    Builds an import graph from a directory of Python files.

    The graph nodes represent modules (files), and edges represent import relationships.
    This allows for the computation of centrality metrics that capture the structural
    importance of different modules within the codebase.
    """

    def __init__(self, root_dir: Path):
        """
        Initialize the graph builder with a root directory.

        Args:
            root_dir: Path to the root directory containing Python files.
        """
        self.root_dir = root_dir
        self.graph = nx.DiGraph()
        self._file_to_module: Dict[str, str] = {}
        self._module_to_file: Dict[str, str] = {}

    def _discover_python_files(self) -> List[Path]:
        """
        Discover all Python files in the root directory.

        Returns:
            List of Path objects for all .py files found.
        """
        python_files = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(Path(root) / file)
        return python_files

    def _get_module_name(self, file_path: Path) -> str:
        """
        Convert a file path to a module name.

        Args:
            file_path: Path to the Python file.

        Returns:
            String representation of the module name (relative to root).
        """
        try:
            rel_path = file_path.relative_to(self.root_dir)
            # Convert path separators to dots and remove .py extension
            module_name = str(rel_path).replace(os.sep, '.').replace('/', '.')
            if module_name.endswith('.py'):
                module_name = module_name[:-3]
            return module_name
        except ValueError:
            # File is outside root_dir, use absolute path as fallback
            return str(file_path)

    def _parse_imports(self, file_path: Path) -> Set[str]:
        """
        Parse a Python file and extract its import statements.

        Args:
            file_path: Path to the Python file.

        Returns:
            Set of imported module names.
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level module name
                        module_name = alias.name.split('.')[0]
                        imports.add(module_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get the top-level module name
                        module_name = node.module.split('.')[0]
                        imports.add(module_name)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")

        return imports

    def build_graph(self) -> nx.DiGraph:
        """
        Build the import graph for the entire repository.

        Returns:
            NetworkX DiGraph representing the import relationships.
        """
        logger.info(f"Building import graph for {self.root_dir}")

        python_files = self._discover_python_files()
        logger.info(f"Found {len(python_files)} Python files")

        # Create nodes for all files
        for file_path in python_files:
            module_name = self._get_module_name(file_path)
            self.graph.add_node(module_name, file_path=str(file_path))
            self._file_to_module[str(file_path)] = module_name
            self._module_to_file[module_name] = str(file_path)

        # Create edges based on imports
        for file_path in python_files:
            source_module = self._get_module_name(file_path)
            imported_modules = self._parse_imports(file_path)

            for imported_module in imported_modules:
                # Check if the imported module exists in our project
                if imported_module in self._module_to_file:
                    target_module = imported_module
                    self.graph.add_edge(source_module, target_module, type='import')
                elif imported_module in ['os', 'sys', 'pathlib', 'typing', 'json', 'logging', 'ast', 'collections', 'io', 'random', 'time', 'resource', 'hashlib', 'subprocess', 'signal', 'enum', 'dataclasses']:
                    # Standard library modules - add as external nodes
                    if imported_module not in self.graph:
                        self.graph.add_node(imported_module, type='stdlib')
                    self.graph.add_edge(source_module, imported_module, type='stdlib_import')

        logger.info(f"Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        return self.graph


def compute_centrality_metrics(graph: nx.DiGraph) -> Dict[str, Dict[str, float]]:
    """
    Compute various centrality metrics for the import graph.

    Args:
        graph: NetworkX DiGraph representing the import relationships.

    Returns:
        Dictionary mapping node names to their centrality metrics.
    """
    if graph.number_of_nodes() == 0:
        return {}

    centrality_metrics = {}

    # Compute degree centrality (in-degree and out-degree)
    in_degree_centrality = nx.in_degree_centrality(graph)
    out_degree_centrality = nx.out_degree_centrality(graph)

    # Compute betweenness centrality
    try:
        betweenness_centrality = nx.betweenness_centrality(graph)
    except Exception as e:
        logger.warning(f"Could not compute betweenness centrality: {e}")
        betweenness_centrality = {node: 0.0 for node in graph.nodes()}

    # Compute closeness centrality
    try:
        closeness_centrality = nx.closeness_centrality(graph)
    except Exception as e:
        logger.warning(f"Could not compute closeness centrality: {e}")
        closeness_centrality = {node: 0.0 for node in graph.nodes()}

    # Compute eigenvector centrality (may fail for some graphs)
    try:
        eigenvector_centrality = nx.eigenvector_centrality(graph, max_iter=1000)
    except Exception as e:
        logger.warning(f"Could not compute eigenvector centrality: {e}")
        eigenvector_centrality = {node: 0.0 for node in graph.nodes()}

    # Aggregate metrics for each node
    for node in graph.nodes():
        centrality_metrics[node] = {
            'in_degree_centrality': in_degree_centrality.get(node, 0.0),
            'out_degree_centrality': out_degree_centrality.get(node, 0.0),
            'betweenness_centrality': betweenness_centrality.get(node, 0.0),
            'closeness_centrality': closeness_centrality.get(node, 0.0),
            'eigenvector_centrality': eigenvector_centrality.get(node, 0.0)
        }

    return centrality_metrics


def extract_graph_features(centrality_metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Extract aggregate graph features from centrality metrics.

    Args:
        centrality_metrics: Dictionary of centrality metrics per node.

    Returns:
        Dictionary of aggregate graph features.
    """
    if not centrality_metrics:
        return {
            'avg_in_degree_centrality': 0.0,
            'avg_out_degree_centrality': 0.0,
            'avg_betweenness_centrality': 0.0,
            'avg_closeness_centrality': 0.0,
            'avg_eigenvector_centrality': 0.0,
            'max_in_degree_centrality': 0.0,
            'max_out_degree_centrality': 0.0,
            'max_betweenness_centrality': 0.0,
            'max_closeness_centrality': 0.0,
            'max_eigenvector_centrality': 0.0,
            'num_nodes': 0,
            'num_edges': 0
        }

    # Extract values for each metric type
    in_degree_values = [m['in_degree_centrality'] for m in centrality_metrics.values()]
    out_degree_values = [m['out_degree_centrality'] for m in centrality_metrics.values()]
    betweenness_values = [m['betweenness_centrality'] for m in centrality_metrics.values()]
    closeness_values = [m['closeness_centrality'] for m in centrality_metrics.values()]
    eigenvector_values = [m['eigenvector_centrality'] for m in centrality_metrics.values()]

    # Compute aggregate statistics
    features = {
        'avg_in_degree_centrality': sum(in_degree_values) / len(in_degree_values) if in_degree_values else 0.0,
        'avg_out_degree_centrality': sum(out_degree_values) / len(out_degree_values) if out_degree_values else 0.0,
        'avg_betweenness_centrality': sum(betweenness_values) / len(betweenness_values) if betweenness_values else 0.0,
        'avg_closeness_centrality': sum(closeness_values) / len(closeness_values) if closeness_values else 0.0,
        'avg_eigenvector_centrality': sum(eigenvector_values) / len(eigenvector_values) if eigenvector_values else 0.0,
        'max_in_degree_centrality': max(in_degree_values) if in_degree_values else 0.0,
        'max_out_degree_centrality': max(out_degree_values) if out_degree_values else 0.0,
        'max_betweenness_centrality': max(betweenness_values) if betweenness_values else 0.0,
        'max_closeness_centrality': max(closeness_values) if closeness_values else 0.0,
        'max_eigenvector_centrality': max(eigenvector_values) if eigenvector_values else 0.0,
        'num_nodes': len(centrality_metrics),
        'num_edges': 0  # Will be set separately
    }

    return features


def get_graph_feature_vector_size() -> int:
    """
    Get the size of the graph feature vector.

    Returns:
        Integer representing the number of features extracted.
    """
    # Number of features from extract_graph_features (excluding num_edges which is set separately)
    # avg_in_degree_centrality, avg_out_degree_centrality, avg_betweenness_centrality,
    # avg_closeness_centrality, avg_eigenvector_centrality,
    # max_in_degree_centrality, max_out_degree_centrality, max_betweenness_centrality,
    # max_closeness_centrality, max_eigenvector_centrality, num_nodes
    return 11


def get_aggregated_graph_features(root_dir: Path) -> Dict[str, Any]:
    """
    Build the import graph and extract aggregated features for a repository.

    Args:
        root_dir: Path to the root directory of the repository.

    Returns:
        Dictionary of aggregated graph features.
    """
    builder = ImportGraphBuilder(root_dir)
    graph = builder.build_graph()

    centrality_metrics = compute_centrality_metrics(graph)
    features = extract_graph_features(centrality_metrics)

    # Update edge count
    features['num_edges'] = graph.number_of_edges()

    return features


def main():
    """
    Main function to demonstrate graph builder functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Build import graph and compute centrality metrics')
    parser.add_argument('--repo-path', type=str, required=True, help='Path to the repository')
    parser.add_argument('--output', type=str, default=None, help='Output file for features (JSON)')

    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return 1

    print(f"Building import graph for: {repo_path}")
    features = get_aggregated_graph_features(repo_path)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            import json
            json.dump(features, f, indent=2)
        print(f"Features saved to: {output_path}")
    else:
        import json
        print(json.dumps(features, indent=2))

    return 0


if __name__ == '__main__':
    exit(main())