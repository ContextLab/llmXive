"""
Entity linking module for mapping question entities to graph nodes.
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dir, get_config


def load_graph_from_file(graph_path: Union[str, Path]) -> Dict[Any, Set[Any]]:
    """
    Load a graph from a JSON file.
    
    Args:
        graph_path (Union[str, Path]): Path to the graph file.
        
    Returns:
        Dict[Any, Set[Any]]: Adjacency list representation of the graph.
    """
    path_obj = Path(graph_path) if isinstance(graph_path, str) else graph_path
    
    with open(path_obj, 'r') as f:
        data = json.load(f)
    
    graph: Dict[Any, Set[Any]] = {}
    for node, neighbors in data.items():
        graph[node] = set(neighbors)
    
    return graph


class EntityLinker:
    """
    Entity linker for mapping question entities to graph nodes.
    """
    
    def __init__(self, graph: Dict[Any, Set[Any]], threshold: float = 0.5):
        """
        Initialize the entity linker.
        
        Args:
            graph (Dict[Any, Set[Any]]): Graph adjacency list.
            threshold (float): Confidence threshold for linking.
        """
        self.graph = graph
        self.threshold = threshold
        self.node_names = set(graph.keys())
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract potential entities from text.
        
        Args:
            text (str): Input text.
            
        Returns:
            List[str]: List of extracted entities.
        """
        # Simple entity extraction: capitalized words and proper nouns
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))
    
    def calculate_similarity(self, entity: str, node_name: str) -> float:
        """
        Calculate similarity between an entity and a node name.
        
        Args:
            entity (str): Extracted entity.
            node_name (str): Graph node name.
            
        Returns:
            float: Similarity score (0.0 to 1.0).
        """
        entity_lower = entity.lower()
        node_lower = node_name.lower()
        
        # Exact match
        if entity_lower == node_lower:
            return 1.0
        
        # Substring match
        if entity_lower in node_lower or node_lower in entity_lower:
            return 0.8
        
        # Word overlap
        entity_words = set(entity_lower.split())
        node_words = set(node_lower.split())
        
        if not entity_words or not node_words:
            return 0.0
        
        overlap = len(entity_words & node_words)
        return overlap / max(len(entity_words), len(node_words))
    
    def link_entity(self, entity: str) -> Optional[Tuple[str, float]]:
        """
        Link an entity to the best matching graph node.
        
        Args:
            entity (str): Entity to link.
            
        Returns:
            Optional[Tuple[str, float]]: Tuple of (node_id, confidence) or None.
        """
        best_match = None
        best_score = 0.0
        
        for node_name in self.node_names:
            score = self.calculate_similarity(entity, node_name)
            if score > best_score:
                best_score = score
                best_match = node_name
        
        if best_score >= self.threshold:
            return (best_match, best_score)
        
        return None
    
    def link_entities(self, text: str) -> List[Tuple[str, float]]:
        """
        Link all entities in text to graph nodes.
        
        Args:
            text (str): Input text.
            
        Returns:
            List[Tuple[str, float]]: List of (node_id, confidence) tuples.
        """
        entities = self.extract_entities(text)
        links = []
        
        for entity in entities:
            link = self.link_entity(entity)
            if link:
                links.append(link)
        
        return links


def create_entity_linker(
    graph_path: Union[str, Path],
    threshold: float = 0.5
) -> EntityLinker:
    """
    Create an entity linker from a graph file.
    
    Args:
        graph_path (Union[str, Path]): Path to the graph file.
        threshold (float): Confidence threshold.
        
    Returns:
        EntityLinker: Configured entity linker.
    """
    graph = load_graph_from_file(graph_path)
    return EntityLinker(graph, threshold)


def main() -> None:
    """Main entry point for entity linker module."""
    pass


if __name__ == "__main__":
    main()
