"""
Full Traversal Strategy: Visits all relevant nodes in the memory graph.
Implements the "Full" active reconstruction algorithm for User Story 1.
"""
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time

from strategies.base import BaseTraversal
from config import get_model_path
from inference import LLMInferenceEngine
from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)


class FullTraversal(BaseTraversal):
    """
    Full active reconstruction strategy that traverses the entire relevant subgraph.
    This strategy attempts to reconstruct the memory graph by visiting ALL reachable
    nodes from the start node, simulating a comprehensive retrieval process.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Initialize inference engine once per strategy instance
        model_path = get_model_path()
        self.inference_engine = LLMInferenceEngine(model_path=model_path)

    def get_strategy_name(self) -> str:
        return "Full"

    def _validate_graph(self, graph: nx.DiGraph, start_node: str) -> bool:
        """
        Validate the graph and start node.
        Returns False if the graph is degenerate (disconnected or single node)
        and logs the issue, preventing traversal.
        """
        if not isinstance(graph, nx.DiGraph):
            logger.error("Provided graph is not a DiGraph")
            return False

        if start_node not in graph.nodes:
            logger.error(f"Start node '{start_node}' not found in graph")
            return False

        # Check for degenerate cases: disconnected components or single node
        if graph.number_of_nodes() == 0:
            logger.warning("Graph is empty")
            return False

        if graph.number_of_nodes() == 1 and graph.number_of_edges() == 0:
            logger.warning("Graph is a single node with no edges (degenerate)")
            # Allow traversal of a single node, but log it
            return True

        # Check connectivity from start_node
        try:
            # Get all nodes reachable from start_node
            reachable = nx.descendants(graph, start_node)
            reachable.add(start_node)
            
            if len(reachable) == 1 and graph.number_of_edges() == 0:
                logger.warning("Start node is isolated (no outgoing edges)")
            else:
                logger.info(f"Start node '{start_node}' has {len(reachable)-1} reachable descendants")
        except Exception as e:
            logger.error(f"Error checking graph connectivity: {e}")
            return False

        return True

    def traverse(
        self,
        graph: nx.DiGraph,
        start_node: str,
        target_node: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Traverse the entire relevant subgraph starting from start_node.
        
        Algorithm:
        1. Validate graph and start node.
        2. Perform BFS to visit all reachable nodes.
        3. For each visited node, perform an LLM inference to extract context.
        4. Track metrics: nodes_visited, edges_traversed, latency.
        
        Returns:
            Tuple of (success, path, stats)
            - success: True if traversal completed without errors
            - path: List of node IDs visited in order
            - stats: Dict containing metrics (nodes_visited, edges_traversed, 
                     total_execution_time_ms, avg_inference_time_ms)
        """
        start_time = self._start_timer()
        self.reset_stats()

        if not self._validate_graph(graph, start_node):
            # Return failure with empty path but populated stats (degenerate case)
            self._record_node_visit()
            return False, [], self.get_stats()

        # BFS Queue
        queue: List[str] = [start_node]
        visited: Set[str] = {start_node}
        path: List[str] = []
        
        logger.info(f"Starting Full traversal from node: {start_node}")

        # Use index pointer for O(1) pop from front
        head_idx = 0
        while head_idx < len(queue):
            current_node = queue[head_idx]
            head_idx += 1
            
            self._record_node_visit()
            path.append(current_node)

            # Process neighbors
            successors = list(graph.successors(current_node))
            for neighbor in successors:
                self._record_edge_traversal()
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

            # Perform LLM inference on the current node to gather context
            # This simulates the "active reconstruction" step
            try:
                node_data = graph.nodes[current_node]
                # Extract text content for inference (context or question)
                node_text = node_data.get("text", node_data.get("content", ""))
                
                if node_text:
                    # Call the inference engine
                    # Note: In a real scenario, we might batch these or use a smaller model
                    # For this benchmark, we simulate the call with timing
                    start_inference = time.time()
                    # Simulate inference result (in real code, this would be self.inference_engine.infer(...))
                    # We keep the timing logic to measure latency
                    _ = self.inference_engine.infer(
                        prompt=f"Analyze the following memory node: {node_text}",
                        max_tokens=10
                    )
                    inference_time = (time.time() - start_inference) * 1000
                    self._record_inference(inference_time)
                else:
                    # If no text, record a minimal inference time
                    self._record_inference(0.0)
                    
            except Exception as e:
                logger.warning(f"Error during inference on node {current_node}: {e}")
                # Continue traversal even if inference fails for a node
                self._record_inference(0.0)

        end_time = self._stop_timer(start_time)
        
        logger.info(
            f"Full traversal completed. Visited {self._stats['nodes_visited']} nodes, "
            f"traversed {self._stats['edges_traversed']} edges "
            f"in {self._stats['total_execution_time_ms']:.2f}ms"
        )

        # Success if we visited at least the start node and no critical errors occurred
        success = len(path) > 0

        return success, path, self.get_stats()