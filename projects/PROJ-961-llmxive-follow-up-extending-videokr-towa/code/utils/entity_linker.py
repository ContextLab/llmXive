import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

def load_graph_from_file(file_path: Path) -> Dict[str, List[str]]:
    """
    Load a graph from a JSON file.
    
    Args:
        file_path: Path to the graph file.
        
    Returns:
        Graph adjacency list.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class EntityLinker:
    """
    Entity linker for mapping question entities to graph nodes.
    """
    
    def __init__(self, graph: Dict[str, List[str]]) -> None:
        """
        Initialize the entity linker.
        
        Args:
            graph: The knowledge graph.
        """
        self.graph = graph
        self.nodes = set(graph.keys())
        
    def extract_entities(self, question: str) -> List[str]:
        """
        Extract entities from a question.
        
        Args:
            question: The question string.
            
        Returns:
            List of extracted entities.
        """
        # Placeholder for entity extraction logic
        # In a real implementation, this would use NLP
        words = re.findall(r'\w+', question.lower())
        return list(set(words))[:2]
        
    def link(self, entity: str) -> Optional[str]:
        """
        Link an entity to a graph node.
        
        Args:
            entity: The entity string.
            
        Returns:
            Linked node ID or None.
        """
        # Placeholder for linking logic
        # In a real implementation, this would use embeddings
        if entity in self.nodes:
            return entity
        # Fuzzy match
        for node in self.nodes:
            if entity in node.lower():
                return node
        return None

def create_entity_linker(graph: Dict[str, List[str]]) -> EntityLinker:
    """
    Create an entity linker instance.
    
    Args:
        graph: The knowledge graph.
        
    Returns:
        EntityLinker instance.
    """
    return EntityLinker(graph)