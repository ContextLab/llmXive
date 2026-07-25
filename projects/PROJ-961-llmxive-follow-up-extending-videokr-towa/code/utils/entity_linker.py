"""Entity linking module for mapping question entities to graph nodes."""
import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dir, get_config

def load_graph_from_file(graph_path: Union[str, Path]) -> Dict[str, Set[str]]:
    """Load a graph from a JSON file."""
    with open(graph_path, "r") as f:
        data = json.load(f)
        graph = {}
        for node, neighbors in data.items():
            graph[node] = set(neighbors)
        return graph

class EntityLinker:
    """Maps question entities to graph nodes using fuzzy matching."""

    def __init__(self, graph: Dict[str, Set[str]], similarity_threshold: float = 0.8):
        """Initialize the entity linker with a graph and similarity threshold."""
        self.graph = graph
        self.similarity_threshold = similarity_threshold
        self.node_names: List[str] = list(graph.keys())

    def link_entity(self, entity_text: str) -> Tuple[Optional[str], float]:
        """Link an entity text to a graph node.

        Args:
            entity_text: The entity text to link.

        Returns:
            A tuple of (node_id, confidence). If no match found, returns (None, 0.0).
        """
        entity_text_lower = entity_text.lower()
        best_match = None
        best_score = 0.0

        for node_name in self.node_names:
            node_name_lower = node_name.lower()
            score = self._calculate_similarity(entity_text_lower, node_name_lower)
            if score > best_score:
                best_score = score
                best_match = node_name

        if best_score >= self.similarity_threshold:
            return best_match, best_score
        return None, 0.0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate a simple similarity score between two strings."""
        if text1 == text2:
            return 1.0
        set1 = set(text1.split())
        set2 = set(text2.split())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

def create_entity_linker(graph_path: Union[str, Path], similarity_threshold: float = 0.8) -> EntityLinker:
    """Create an EntityLinker instance from a graph file path."""
    graph = load_graph_from_file(graph_path)
    return EntityLinker(graph, similarity_threshold)
