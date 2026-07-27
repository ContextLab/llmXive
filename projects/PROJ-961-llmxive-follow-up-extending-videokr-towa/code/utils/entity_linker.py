"""
Module: entity_linker

Purpose:
    Provides functionality to map entities mentioned in questions
    to nodes in the Knowledge Graph using fuzzy or embedding-based matching.

Functions:
    - load_graph_from_file: Loads the graph from a file.
    - EntityLinker: Class handling entity linking logic.
    - create_entity_linker: Factory function to create a linker.
    - main: Entry point for the script.
"""
import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

def load_graph_from_file(file_path: Path) -> Dict[str, List[str]]:
    """
    Loads the graph from a JSON file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        Dict[str, List[str]]: Adjacency list.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

class EntityLinker:
    """
    Class to handle entity linking from text to graph nodes.
    """
    def __init__(self, graph: Dict[str, List[str]]):
        """
        Initializes the linker with a graph.

        Args:
            graph (Dict[str, List[str]]): The graph adjacency list.
        """
        self.graph = graph
        self.nodes = set(graph.keys())

    def link(self, question: str) -> Tuple[Optional[str], float]:
        """
        Links entities in a question to graph nodes.

        Args:
            question (str): The question text.

        Returns:
            Tuple[Optional[str], float]: Node ID and confidence.
        """
        # Placeholder logic: simple keyword matching
        words = re.findall(r'\w+', question.lower())
        for word in words:
            if word in self.nodes:
                return word, 0.9
        return None, 0.0

def create_entity_linker(graph: Dict[str, List[str]]) -> EntityLinker:
    """
    Factory function to create an EntityLinker.

    Args:
        graph (Dict[str, List[str]]): The graph.

    Returns:
        EntityLinker: The linker instance.
    """
    return EntityLinker(graph)

def main():
    """
    Main entry point for the entity_linker script.
    """
    graph_path = get_path("knowledge_graph_filename", "data/raw/knowledge_graph.json")
    graph = load_graph_from_file(graph_path)
    linker = create_entity_linker(graph)
    test_q = "What is the capital of France?"
    node, conf = linker.link(test_q)
    print(f"Linked: {node} (Conf: {conf})")

if __name__ == "__main__":
    main()
