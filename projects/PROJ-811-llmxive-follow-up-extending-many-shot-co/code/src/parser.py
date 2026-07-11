"""
CoT Trace Parser Module

This module provides functionality to parse Chain-of-Thought (CoT) traces into
Directed Acyclic Graphs (DAGs) and calculate logical difficulty scores.

Key classes and functions:
- CoTParser: Main parser class for handling CoT traces
- parse_trace_to_dag: Convert a text trace to a networkx DAG
- get_logical_difficulty: Calculate max path depth as logical difficulty score
"""

import networkx as nx
import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CoTParser:
    """
    Parser for Chain-of-Thought traces.

    Converts text-based reasoning traces into DAG structures where:
    - Nodes represent reasoning steps
    - Edges represent logical dependencies between steps

    Validates DAGs for:
    - Cycles (max cycle length of 5 steps)
    - Max incoming edges (> 3 incoming edges flags as invalid)
    """

    def __init__(
        self,
        max_cycle_length: int = 5,
        max_incoming_edges: int = 3,
        step_delimiters: Optional[List[str]] = None
    ):
        """
        Initialize the CoT parser.

        Args:
            max_cycle_length: Maximum allowed cycle length before flagging (default: 5)
            max_incoming_edges: Maximum allowed incoming edges per node (default: 3)
            step_delimiters: Regex patterns to identify step boundaries
        """
        self.max_cycle_length = max_cycle_length
        self.max_incoming_edges = max_incoming_edges
        
        if step_delimiters is None:
            # Default delimiters for common CoT formats
            self.step_delimiters = [
                r'Step\s*\d+[:\s]',
                r'\d+\.\s*',
                r'First,|Second,|Third,|Finally,',
                r'^(?!.*\d+\.)',  # Fallback for non-numeric starts
            ]
        else:
            self.step_delimiters = step_delimiters

    def split_trace_into_steps(self, trace_text: str) -> List[str]:
        """
        Split a CoT trace into individual reasoning steps.

        Args:
            trace_text: The full CoT trace text

        Returns:
            List of step strings
        """
        if not trace_text or not isinstance(trace_text, str):
            return []

        # Try to split by common patterns
        steps = []
        current_step = ""
        
        # First, try explicit step markers
        step_pattern = r'(Step\s*\d+[:\s]|\d+\.\s*|First,|Second,|Third,|Finally,)'
        parts = re.split(f'({step_pattern})', trace_text, flags=re.IGNORECASE)
        
        if len(parts) > 1:
            # Reconstruct steps with their markers
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    step_text = parts[i] + parts[i + 1]
                    if step_text.strip():
                        steps.append(step_text.strip())
                elif parts[i].strip():
                    steps.append(parts[i].strip())
        else:
            # Fallback: split by newlines or simple patterns
            steps = [s.strip() for s in trace_text.split('\n') if s.strip()]

        # Clean up empty steps
        return [s for s in steps if s and len(s) > 10]

    def extract_dependencies(self, step: str, all_steps: List[str]) -> List[int]:
        """
        Extract logical dependencies from a step text.

        Looks for references to other steps (e.g., "as shown in step 2", "based on previous calculation").

        Args:
            step: The current step text
            all_steps: List of all steps for reference

        Returns:
            List of indices of dependent steps
        """
        dependencies = []
        
        # Pattern to find references like "step 2", "step #2", "previous step", etc.
        step_ref_patterns = [
            r'step\s*(\d+)',
            r'step\s*#(\d+)',
            r'previous\s*(step)?',
            r'above\s*(step)?',
            r'earlier\s*(step)?',
        ]
        
        for pattern in step_ref_patterns:
            matches = re.findall(pattern, step, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if match.isdigit():
                    step_idx = int(match) - 1  # Convert 1-based to 0-based
                    if 0 <= step_idx < len(all_steps):
                        dependencies.append(step_idx)
        
        # Handle "previous" references
        if re.search(r'previous\s*(step)?', step, re.IGNORECASE):
            dependencies.append(-1)  # Will be resolved later to current - 1
        
        return dependencies

    def resolve_dependencies(
        self,
        dependencies: List[int],
        current_step_idx: int,
        total_steps: int
    ) -> List[int]:
        """
        Resolve dependency indices to actual step indices.

        Args:
            dependencies: List of dependency indices (may include -1 for "previous")
            current_step_idx: Index of the current step
            total_steps: Total number of steps

        Returns:
            List of resolved dependency indices
        """
        resolved = []
        for dep in dependencies:
            if dep == -1:
                # "Previous" refers to the immediately preceding step
                if current_step_idx > 0:
                    resolved.append(current_step_idx - 1)
            elif 0 <= dep < total_steps and dep != current_step_idx:
                resolved.append(dep)
        
        return list(set(resolved))  # Remove duplicates

    def parse_trace_to_dag(self, trace_text: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Parse a CoT trace into a Directed Acyclic Graph (DAG).

        Args:
            trace_text: The CoT trace text

        Returns:
            Tuple of (DAG graph, metadata dict)
        """
        steps = self.split_trace_into_steps(trace_text)
        
        if not steps:
            logger.warning("No valid steps found in trace")
            return nx.DiGraph(), {'error': 'no_steps'}

        G = nx.DiGraph()
        
        # Add nodes
        for i, step in enumerate(steps):
            G.add_node(i, text=step, step_number=i + 1)

        # Add edges based on dependencies
        for i, step in enumerate(steps):
            deps = self.extract_dependencies(step, steps)
            resolved_deps = self.resolve_dependencies(deps, i, len(steps))
            
            for dep_idx in resolved_deps:
                if dep_idx != i:  # No self-loops
                    G.add_edge(dep_idx, i)

        # Validate DAG structure
        is_valid = True
        validation_errors = []
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                max_cycle_len = max(len(c) for c in cycles)
                if max_cycle_len > self.max_cycle_length:
                    is_valid = False
                    validation_errors.append(f"cycle_detected: max_length={max_cycle_len}")
        except Exception as e:
            logger.error(f"Error checking cycles: {e}")
            validation_errors.append(f"cycle_check_error: {str(e)}")

        # Check incoming edges
        for node in G.nodes():
            in_degree = G.in_degree(node)
            if in_degree > self.max_incoming_edges:
                is_valid = False
                validation_errors.append(f"excessive_incoming_edges: node={node}, count={in_degree}")

        metadata = {
            'num_steps': len(steps),
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'is_valid': is_valid,
            'validation_errors': validation_errors,
            'raw_trace_length': len(trace_text)
        }

        return G, metadata

    def is_dag_valid(
        self,
        dag: nx.DiGraph,
        trace_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a DAG for cycles and edge constraints.

        Args:
            dag: The DAG to validate
            trace_id: Optional ID for logging

        Returns:
            Tuple of (is_valid, invalid_reason or None)
        """
        if dag.number_of_nodes() == 0:
            return False, "empty_dag"

        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(dag))
            if cycles:
                max_cycle_len = max(len(c) for c in cycles)
                if max_cycle_len > self.max_cycle_length:
                    return False, f"cycle_too_long: {max_cycle_len}"
        except Exception as e:
            logger.error(f"Cycle detection error: {e}")
            return False, "cycle_detection_error"

        # Check incoming edges
        for node in dag.nodes():
            in_degree = dag.in_degree(node)
            if in_degree > self.max_incoming_edges:
                return False, f"too_many_incoming_edges: {in_degree}"

        return True, None

def parse_trace_to_dag(trace_text: str, parser: Optional[CoTParser] = None) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Convenience function to parse a trace to a DAG.

    Args:
        trace_text: The CoT trace text
        parser: Optional CoTParser instance (creates default if None)

    Returns:
        Tuple of (DAG graph, metadata)
    """
    if parser is None:
        parser = CoTParser()
    return parser.parse_trace_to_dag(trace_text)

def get_logical_difficulty(dag: nx.DiGraph) -> int:
    """
    Calculate the logical difficulty score as the maximum path depth.

    The logical difficulty score is defined as the length of the longest
    path in the DAG (number of edges in the longest path).

    Args:
        dag: The DAG representing the CoT trace

    Returns:
        Integer representing the maximum path depth
    """
    if dag.number_of_nodes() == 0:
        return 0

    # For a DAG, the longest path can be found using topological sort
    try:
        # Calculate longest path using dynamic programming on topological order
        longest_path = 0
        
        # Initialize distances
        dist = {node: 0 for node in dag.nodes()}
        
        # Process nodes in topological order
        for node in nx.topological_sort(dag):
            for predecessor in dag.predecessors(node):
                dist[node] = max(dist[node], dist[predecessor] + 1)
            longest_path = max(longest_path, dist[node])
        
        return longest_path
        
    except nx.NetworkXUnfeasible:
        # Graph has cycles, return max possible depth or 0
        logger.warning("Graph has cycles, cannot compute longest path")
        return 0

def get_max_path_depth(dag: nx.DiGraph) -> int:
    """
    Alias for get_logical_difficulty.

    Args:
        dag: The DAG

    Returns:
        Maximum path depth
    """
    return get_logical_difficulty(dag)
