import re
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

logger = logging.getLogger(__name__)

def load_graph_from_file(graph_path: Optional[str] = None) -> Dict[str, Any]:
    if graph_path is None:
        graph_path = get_path("data/raw/knowledge_graph.json")
    
    if not Path(graph_path).exists():
        raise FileNotFoundError(f"Graph file not found at {graph_path}")
    
    with open(graph_path, 'r') as f:
        return json.load(f)

class EntityLinker:
    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.node_map: Dict[str, Set[str]] = {}
        self._build_index()
    
    def _build_index(self):
        nodes = self.graph.get('nodes', [])
        for node in nodes:
            node_id = node.get('id')
            entity_name = node.get('name', '').lower()
            if entity_name and node_id:
                if entity_name not in self.node_map:
                    self.node_map[entity_name] = set()
                self.node_map[entity_name].add(node_id)
    
    def link_entity(self, entity_text: str, threshold: float = 0.8) -> Tuple[Optional[str], float]:
        entity_lower = entity_text.lower().strip()
        
        # Check for exact match
        if entity_lower in self.node_map:
            return list(self.node_map[entity_lower])[0], 1.0
        
        # Fuzzy matching (simple substring check for now)
        best_match = None
        best_score = 0.0
        
        for name, node_ids in self.node_map.items():
            if entity_lower in name or name in entity_lower:
                score = len(entity_lower) / max(len(name), len(entity_lower))
                if score > best_score:
                    best_score = score
                    best_match = list(node_ids)[0]
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0.0

def create_entity_linker(graph: Optional[Dict[str, Any]] = None) -> EntityLinker:
    if graph is None:
        graph = load_graph_from_file()
    return EntityLinker(graph)

def main():
    logging.basicConfig(level=logging.INFO)
    try:
        graph = load_graph_from_file()
        linker = create_entity_linker(graph)
        
        test_entities = ["video", "action", "scene"]
        for entity in test_entities:
            node_id, confidence = linker.link_entity(entity)
            print(f"Entity: {entity} -> Node: {node_id}, Confidence: {confidence}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
