"""
Greedy Traversal Strategy Implementation.
Selects the top-k most confident edges at each step.
"""
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time
from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)

class GreedyTraversal(BaseTraversal):
    """
    Greedy Traversal Strategy.
    
    This strategy explores the graph by always selecting the top-k edges with the
    highest confidence scores at the current frontier. This aims to find the most
    promising path quickly.
    """
    
    def __init__(self, top_k: int = 3, max_iterations: int = 100):
        """
        Initialize Greedy Traversal.
        
        Args:
            top_k: Number of best edges to select at each step.
            max_iterations: Maximum number of expansion steps.
        """
        super().__init__()
        self.top_k = top_k
        self.max_iterations = max_iterations

    def _calculate_edge_confidence(self, G: nx.Graph, edge: Tuple[Any, Any], 
                                   context: str) -> float:
        """
        Calculate the confidence score for an edge.
        
        Similar to LazyTraversal, this would typically involve an LLM call.
        Here we use a heuristic based on edge attributes.
        """
        if G.has_edge(*edge):
            attrs = G.edges[edge]
            if 'confidence' in attrs:
                return attrs['confidence']
            if 'weight' in attrs:
                w = attrs['weight']
                if w > 1:
                    return min(1.0, w / 10.0)
                return w
        return 0.5

    def run(self, G: nx.Graph, question: str) -> Dict[str, Any]:
        """
        Execute the Greedy Traversal strategy.
        
        Args:
            G: The memory graph.
            question: The user question.
        
        Returns:
            Dictionary containing 'answer', 'nodes_visited', 'path', 'status'.
        """
        if not validate_graph(G):
            logger.error("Invalid graph provided to GreedyTraversal.")
            return {"answer": "", "nodes_visited": 0, "status": "error", "error": "Invalid graph"}

        start_time = time.time()
        visited_nodes: Set[Any] = set()
        nodes_visited = 0
        current_nodes: List[Any] = []
        
        # Identify start nodes
        keywords = question.split()
        start_nodes = [n for n in G.nodes() if any(kw.lower() in str(n).lower() for kw in keywords)]
        
        if not start_nodes:
            start_nodes = list(G.nodes())[:1]
            logger.warning(f"No matching start nodes found. Using fallback: {start_nodes}")

        current_nodes = start_nodes
        visited_nodes.update(current_nodes)
        nodes_visited += len(current_nodes)
        
        path = []
        found_answer = False
        answer = ""
        iterations = 0

        while current_nodes and iterations < self.max_iterations:
            iterations += 1
            candidates = [] # List of (edge, confidence)
            
            for node in current_nodes:
                neighbors = list(G.neighbors(node))
                for neighbor in neighbors:
                    if neighbor in visited_nodes:
                        continue
                    edge = (node, neighbor)
                    confidence = self._calculate_edge_confidence(G, edge, question)
                    candidates.append((edge, confidence))
            
            # Sort candidates by confidence descending and pick top_k
            candidates.sort(key=lambda x: x[1], reverse=True)
            selected_edges = candidates[:self.top_k]
            
            next_nodes = []
            for edge, conf in selected_edges:
                u, v = edge
                if v not in visited_nodes:
                    visited_nodes.add(v)
                    next_nodes.append(v)
                    nodes_visited += 1
                    path.append((u, v, conf))
                    
                    # Check for answer
                    if "answer" in str(v).lower() or "solution" in str(v).lower():
                        found_answer = True
                        answer = str(v)
                        break
            
            if found_answer:
                break
            
            current_nodes = list(set(next_nodes))

        elapsed_time = time.time() - start_time
        
        if not found_answer:
            answer = "No answer found within greedy constraints."
            logger.info(f"Greedy traversal completed without finding a confident answer. Nodes visited: {nodes_visited}")

        return {
            "answer": answer,
            "nodes_visited": nodes_visited,
            "path": path,
            "status": "success" if found_answer else "incomplete",
            "elapsed_time": elapsed_time
        }
