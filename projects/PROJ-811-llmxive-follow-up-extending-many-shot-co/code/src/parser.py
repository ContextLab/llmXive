"""
CoT Trace Parser Module

Converts raw Chain-of-Thought text traces into NetworkX Directed Acyclic Graphs (DAGs).
Implements logical dependency extraction, cycle detection, and difficulty scoring.
"""

import networkx as nx
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for step parsing
STEP_PATTERNS = [
    r'^Step\s*(\d+)[.:]\s*(.*)$',  # "Step 1: ..." or "Step 1. ..."
    r'^(\d+)[.:]\s*(.*)$',          # "1. ..." or "1: ..."
    r'^(Step\s*\d+)[.:]\s*(.*)$',   # "Step 1: ..." without number capture group in first part
]

REFERENCE_PATTERNS = [
    r'refer to (?:Step|step) (\d+)',
    r'as in (?:Step|step) (\d+)',
    r'based on (?:Step|step) (\d+)',
    r'using (?:Step|step) (\d+)',
    r'from (?:Step|step) (\d+)',
    r'following (?:Step|step) (\d+)',
    r'after (?:Step|step) (\d+)',
    r'before (?:Step|step) (\d+)',
    r'prior to (?:Step|step) (\d+)',
    r'see (?:Step|step) (\d+)',
]

def split_trace_into_steps(trace_text: str) -> List[Tuple[int, str]]:
    """
    Split a raw CoT trace into numbered steps.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        List of tuples (step_number, step_text).
    """
    if not trace_text or not trace_text.strip():
        return []

    lines = trace_text.strip().split('\n')
    steps = []
    current_step_num = None
    current_step_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched = False
        for pattern in STEP_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Save previous step if exists
                if current_step_num is not None and current_step_text:
                    steps.append((current_step_num, ' '.join(current_step_text)))

                # Extract new step number and text
                groups = match.groups()
                if len(groups) == 2:
                    # Pattern like "Step 1: text" or "1. text"
                    first, second = groups
                    if first.isdigit():
                        current_step_num = int(first)
                        current_step_text = [second]
                    elif second.isdigit():
                        # Pattern like "Step 1: text" where first is "Step 1"
                        # Extract number from first group
                        num_match = re.search(r'\d+', first)
                        if num_match:
                            current_step_num = int(num_match.group())
                            current_step_text = [second]
                        else:
                            current_step_num = len(steps) + 1
                            current_step_text = [line]
                    else:
                        current_step_num = len(steps) + 1
                        current_step_text = [line]
                else:
                    current_step_num = len(steps) + 1
                    current_step_text = [line]

                matched = True
                break

        if not matched:
            # Continuation of current step or unnumbered line
            if current_step_num is not None:
                current_step_text.append(line)
            else:
                # First unnumbered line - treat as step 1
                if not steps:
                    current_step_num = 1
                    current_step_text = [line]

    # Don't forget the last step
    if current_step_num is not None and current_step_text:
        steps.append((current_step_num, ' '.join(current_step_text)))

    # Re-index steps to be sequential if gaps exist
    if steps:
        sequential_steps = []
        for i, (num, text) in enumerate(steps, 1):
            sequential_steps.append((i, text))
        return sequential_steps

    return steps

def extract_references(step_text: str) -> List[int]:
    """
    Extract references to other steps from a step's text.

    Args:
        step_text: The text of a single step.

    Returns:
        List of referenced step numbers.
    """
    references = []
    for pattern in REFERENCE_PATTERNS:
        matches = re.findall(pattern, step_text, re.IGNORECASE)
        for match in matches:
            try:
                ref_num = int(match)
                if ref_num not in references:
                    references.append(ref_num)
            except ValueError:
                continue
    return references

def detect_cycle(graph: nx.DiGraph) -> Optional[List[int]]:
    """
    Detect if the graph contains a cycle and return the cycle nodes if found.

    Args:
        graph: A NetworkX DiGraph.

    Returns:
        List of node IDs forming a cycle, or None if no cycle exists.
    """
    try:
        cycle = nx.find_cycle(graph)
        if cycle:
            # Extract node IDs from edge tuples
            return list(set([node for edge in cycle for node in edge]))
    except nx.NetworkXNoCycle:
        return None
    return None

def parse_trace_to_dag(trace_text: str) -> Tuple[Optional[nx.DiGraph], bool, str]:
    """
    Parse a raw CoT trace into a NetworkX DAG.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        Tuple of (DAG or None, is_valid, reason).
        - DAG: The constructed NetworkX DiGraph if valid, None otherwise.
        - is_valid: True if the trace is valid (no cycles, reasonable structure).
        - reason: Explanation of validity or failure.
    """
    if not trace_text or not trace_text.strip():
        return None, False, "Empty trace"

    try:
        steps = split_trace_into_steps(trace_text)
        if not steps:
            return None, False, "No steps found in trace"

        graph = nx.DiGraph()

        # Add nodes
        for step_num, step_text in steps:
            graph.add_node(step_num, text=step_text)

        # Add edges based on references
        for step_num, step_text in steps:
            references = extract_references(step_text)
            for ref_num in references:
                if ref_num in graph.nodes:
                    # Edge from referenced step to current step (dependency direction)
                    graph.add_edge(ref_num, step_num)
                else:
                    # Reference to non-existent step - could be invalid, but we'll note it
                    logger.warning(f"Step {step_num} references non-existent step {ref_num}")

        # Check for cycles
        cycle = detect_cycle(graph)
        if cycle:
            return None, False, f"Cycle detected: {cycle}"

        # Check for max incoming edges (heuristic for validity)
        max_incoming = 5
        for node in graph.nodes:
            in_degree = graph.in_degree(node)
            if in_degree > max_incoming:
                logger.warning(f"Step {node} has {in_degree} incoming edges, exceeds threshold {max_incoming}")
                # We don't mark as invalid for this alone, just warn

        return graph, True, "Valid DAG"

    except Exception as e:
        logger.error(f"Error parsing trace: {str(e)}")
        return None, False, f"Parse error: {str(e)}"

def get_max_path_depth(graph: nx.DiGraph) -> int:
    """
    Calculate the maximum path depth (longest path) in a DAG.

    Args:
        graph: A NetworkX DiGraph (should be acyclic).

    Returns:
        The length of the longest path in the graph (number of nodes).
    """
    if not graph or graph.number_of_nodes() == 0:
        return 0

    try:
        # Longest path in DAG
        longest_path = nx.dag_longest_path(graph)
        return len(longest_path)
    except nx.NetworkXUnbounded:
        # This shouldn't happen if graph is acyclic, but just in case
        logger.error("Graph appears to have cycles despite validation")
        return 0

def get_logical_difficulty(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Calculate logical difficulty metrics for a DAG.

    Args:
        graph: A NetworkX DiGraph.

    Returns:
        Dictionary containing difficulty metrics:
        - max_depth: Maximum path depth
        - num_nodes: Number of steps
        - num_edges: Number of dependencies
        - avg_in_degree: Average incoming edges per node
        - avg_out_degree: Average outgoing edges per node
        - is_valid: Whether the graph is a valid DAG
        - cycle_info: Any cycle information if invalid
    """
    if graph is None or graph.number_of_nodes() == 0:
        return {
            'max_depth': 0,
            'num_nodes': 0,
            'num_edges': 0,
            'avg_in_degree': 0.0,
            'avg_out_degree': 0.0,
            'is_valid': False,
            'cycle_info': 'Empty or null graph'
        }

    try:
        max_depth = get_max_path_depth(graph)
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()

        in_degrees = [d for n, d in graph.in_degree()]
        out_degrees = [d for n, d in graph.out_degree()]

        avg_in = sum(in_degrees) / num_nodes if num_nodes > 0 else 0.0
        avg_out = sum(out_degrees) / num_nodes if num_nodes > 0 else 0.0

        cycle_info = detect_cycle(graph)

        return {
            'max_depth': max_depth,
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'avg_in_degree': avg_in,
            'avg_out_degree': avg_out,
            'is_valid': cycle_info is None,
            'cycle_info': cycle_info if cycle_info else None
        }
    except Exception as e:
        logger.error(f"Error calculating difficulty: {str(e)}")
        return {
            'max_depth': 0,
            'num_nodes': 0,
            'num_edges': 0,
            'avg_in_degree': 0.0,
            'avg_out_degree': 0.0,
            'is_valid': False,
            'cycle_info': f'Error: {str(e)}'
        }

class CoTParser:
    """
    High-level parser for Chain-of-Thought traces.
    """

    def __init__(self, max_steps: int = 100, max_incoming_edges: int = 5):
        """
        Initialize the CoT parser.

        Args:
            max_steps: Maximum number of steps allowed in a trace.
            max_incoming_edges: Maximum incoming edges per node (heuristic).
        """
        self.max_steps = max_steps
        self.max_incoming_edges = max_incoming_edges
        logger.info(f"CoTParser initialized with max_steps={max_steps}, max_incoming_edges={max_incoming_edges}")

    def parse(self, trace_text: str) -> Dict[str, Any]:
        """
        Parse a single CoT trace.

        Args:
            trace_text: The raw CoT trace string.

        Returns:
            Dictionary containing:
            - success: Boolean indicating if parsing succeeded
            - dag: The parsed DAG (or None)
            - difficulty: Logical difficulty metrics
            - steps: List of (step_num, text) tuples
            - error: Error message if any
        """
        dag, is_valid, reason = parse_trace_to_dag(trace_text)

        result = {
            'success': is_valid,
            'dag': dag,
            'difficulty': get_logical_difficulty(dag) if dag else None,
            'steps': split_trace_into_steps(trace_text),
            'error': None if is_valid else reason
        }

        if dag and dag.number_of_nodes() > self.max_steps:
            result['success'] = False
            result['error'] = f"Too many steps: {dag.number_of_nodes()} > {self.max_steps}"

        return result

    def parse_batch(self, traces: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple CoT traces.

        Args:
            traces: List of raw CoT trace strings.

        Returns:
            List of parsing results.
        """
        return [self.parse(trace) for trace in traces]

    def filter_valid_traces(self, traces: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Filter and return only valid traces with their parsed results.

        Args:
            traces: List of raw CoT trace strings.

        Returns:
            List of tuples (trace_text, result_dict) for valid traces only.
        """
        valid_traces = []
        for trace in traces:
            result = self.parse(trace)
            if result['success']:
                valid_traces.append((trace, result))
        return valid_traces


# Convenience functions for direct use
def parse_trace_to_dag(trace_text: str) -> Tuple[Optional[nx.DiGraph], bool, str]:
    """
    Parse a raw CoT trace into a NetworkX DAG.
    (Wrapper for module-level function)
    """
    return parse_trace_to_dag(trace_text)

def get_logical_difficulty(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Calculate logical difficulty metrics for a DAG.
    (Wrapper for module-level function)
    """
    return get_logical_difficulty(graph)

def get_max_path_depth(graph: nx.DiGraph) -> int:
    """
    Calculate the maximum path depth (longest path) in a DAG.
    (Wrapper for module-level function)
    """
    return get_max_path_depth(graph)