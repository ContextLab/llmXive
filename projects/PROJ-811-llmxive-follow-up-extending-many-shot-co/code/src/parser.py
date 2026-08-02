"""
CoT Trace Parser Module

Converts Chain-of-Thought traces into Directed Acyclic Graphs (DAGs) using NetworkX.
Implements cycle detection, logical difficulty scoring, and invalid trace flagging.
"""

import networkx as nx
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for cycle detection thresholds
MAX_CYCLE_LENGTH = 5
MAX_INCOMING_EDGES = 3


def split_trace_into_steps(trace_text: str) -> List[str]:
    """
    Split a raw CoT trace into individual logical steps.

    Handles various formats: numbered lists, bullet points, and newline-separated steps.
    Falls back to splitting by newlines if no structured format is detected.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        List of step strings.
    """
    if not trace_text or not trace_text.strip():
        return []

    lines = trace_text.strip().split('\n')
    steps = []

    # Pattern for numbered lists (1., 2., etc.) or bullet points
    step_pattern = re.compile(r'^(?:\d+\.|-|\*|•)\s*(.*)$')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = step_pattern.match(line)
        if match:
            steps.append(match.group(1).strip())
        else:
            # If line doesn't match pattern but is not empty, treat as step
            steps.append(line)

    return steps


def extract_references(step_text: str) -> List[str]:
    """
    Extract references to previous steps from a step text.

    Looks for patterns like "step 1", "previous step", "as mentioned above", etc.

    Args:
        step_text: The text of a single step.

    Returns:
        List of referenced step identifiers (as strings).
    """
    references = []

    # Pattern for explicit step references: "step 1", "Step 2", "step #3"
    step_ref_pattern = re.compile(r'step\s*(?:#\s*)?(\d+)', re.IGNORECASE)

    # Pattern for relative references
    relative_ref_pattern = re.compile(r'(?:previous|earlier|above)\s*(?:step)?', re.IGNORECASE)

    # Extract explicit step numbers
    matches = step_ref_pattern.findall(step_text)
    references.extend(matches)

    # Handle relative references by returning a special marker
    if relative_ref_pattern.search(step_text):
        # We'll resolve relative references later based on position
        references.append("PREVIOUS")

    return references


def parse_trace_to_dag(trace_text: str) -> Tuple[Optional[nx.DiGraph], List[str]]:
    """
    Parse a CoT trace into a Directed Acyclic Graph (DAG).

    Each step becomes a node, and references between steps become directed edges.
    Returns None for the graph if the trace is invalid or cannot be parsed.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        Tuple of (DAG graph or None, list of error messages).
    """
    errors = []

    if not trace_text or not trace_text.strip():
        errors.append("Empty trace provided")
        return None, errors

    steps = split_trace_into_steps(trace_text)
    if not steps:
        errors.append("No valid steps found in trace")
        return None, errors

    G = nx.DiGraph()

    # Add nodes for each step
    for i, step in enumerate(steps):
        node_id = i + 1  # 1-indexed
        G.add_node(node_id, text=step, step_index=i)

    # Add edges based on references
    for i, step in enumerate(steps):
        node_id = i + 1
        references = extract_references(step)

        for ref in references:
            if ref == "PREVIOUS":
                # Reference to immediately preceding step
                if i > 0:
                    prev_node_id = i
                    G.add_edge(prev_node_id, node_id, type="explicit")
                else:
                    errors.append(f"Step {node_id} references previous step but is first step")
            else:
                # Explicit step number reference
                try:
                    ref_id = int(ref)
                    if ref_id < 1 or ref_id > len(steps):
                        errors.append(f"Step {node_id} references non-existent step {ref_id}")
                    else:
                        G.add_edge(ref_id, node_id, type="explicit")
                except ValueError:
                    errors.append(f"Step {node_id} has invalid reference: {ref}")

    return G, errors


def detect_cycle(G: nx.DiGraph) -> Tuple[bool, List[List[int]]]:
    """
    Detect cycles in a directed graph.

    Args:
        G: A NetworkX DiGraph.

    Returns:
        Tuple of (has_cycle, list_of_cycles).
        Each cycle is represented as a list of node IDs.
    """
    if G is None or G.number_of_nodes() == 0:
        return False, []

    try:
        cycles = list(nx.simple_cycles(G))
        return len(cycles) > 0, cycles
    except Exception as e:
        logger.error(f"Error detecting cycles: {e}")
        return False, []


def get_max_path_depth(G: nx.DiGraph) -> int:
    """
    Calculate the maximum path depth (longest path) in a DAG.

    This represents the "Logical Difficulty Score" - the maximum number of
    sequential dependencies in the reasoning chain.

    Args:
        G: A NetworkX DiGraph (should be a DAG).

    Returns:
        Integer representing the maximum path depth.
    """
    if G is None or G.number_of_nodes() == 0:
        return 0

    if not nx.is_directed_acyclic_graph(G):
        # If graph has cycles, find the longest path ignoring cycle detection
        # This is a fallback for invalid graphs
        try:
            # For cyclic graphs, we can't use dag_longest_path
            # Instead, we'll find the longest simple path
            longest_path_len = 0
            for start_node in G.nodes():
                for end_node in G.nodes():
                    try:
                        path = nx.shortest_path(G, start_node, end_node)
                        if len(path) > longest_path_len:
                            longest_path_len = len(path)
                    except nx.NetworkXNoPath:
                        continue
            return longest_path_len - 1 if longest_path_len > 0 else 0
        except Exception:
            return 0

    try:
        longest_path = nx.dag_longest_path(G)
        return len(longest_path) - 1  # Depth is number of edges, not nodes
    except Exception as e:
        logger.error(f"Error calculating max path depth: {e}")
        return 0


def get_logical_difficulty(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Calculate the logical difficulty score for a trace.

    The score is primarily based on the maximum path depth (longest chain of
    dependencies), which represents the complexity of the reasoning chain.

    Args:
        G: A NetworkX DiGraph.

    Returns:
        Dictionary containing difficulty metrics.
    """
    if G is None or G.number_of_nodes() == 0:
        return {
            "depth": 0,
            "num_nodes": 0,
            "num_edges": 0,
            "is_valid": False,
            "reason": "Empty or null graph"
        }

    has_cycle, cycles = detect_cycle(G)
    max_depth = get_max_path_depth(G)

    # Count nodes with high incoming edge count
    high_indegree_nodes = [n for n in G.nodes() if G.in_degree(n) > MAX_INCOMING_EDGES]

    return {
        "depth": max_depth,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_valid": not has_cycle,
        "cycles": cycles,
        "high_indegree_nodes": high_indegree_nodes,
        "reason": "Valid" if not has_cycle and len(high_indegree_nodes) == 0 else "Invalid"
    }


def is_trace_valid(G: nx.DiGraph, max_cycle_length: int = MAX_CYCLE_LENGTH) -> Tuple[bool, List[str]]:
    """
    Check if a trace is valid according to logical dependency rules.

    A trace is invalid if:
    1. It contains cycles of length <= max_cycle_length
    2. It has nodes with more than max_incoming_edges incoming edges

    Args:
        G: A NetworkX DiGraph.
        max_cycle_length: Maximum allowed cycle length (default: 5).

    Returns:
        Tuple of (is_valid, list_of_issues).
    """
    issues = []

    if G is None or G.number_of_nodes() == 0:
        return False, ["Empty or null graph"]

    # Check for cycles
    has_cycle, cycles = detect_cycle(G)
    if has_cycle:
        for cycle in cycles:
            if len(cycle) <= max_cycle_length:
                issues.append(f"Cycle detected of length {len(cycle)}: {cycle}")

    # Check for nodes with too many incoming edges
    for node in G.nodes():
        in_degree = G.in_degree(node)
        if in_degree > MAX_INCOMING_EDGES:
            issues.append(f"Node {node} has {in_degree} incoming edges (max allowed: {MAX_INCOMING_EDGES})")

    return len(issues) == 0, issues


def flag_invalid_trace(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Flag a trace as invalid if it contains logical errors.

    This implements the flagging mechanism for invalid traces.

    Args:
        G: A NetworkX DiGraph.

    Returns:
        Dictionary with validation status and details.
    """
    is_valid, issues = is_trace_valid(G)

    has_cycle, cycles = detect_cycle(G)
    high_indegree_nodes = [n for n in G.nodes() if G.in_degree(n) > MAX_INCOMING_EDGES]

    return {
        "is_valid": is_valid,
        "has_cycle": has_cycle,
        "cycles": cycles,
        "high_indegree_nodes": high_indegree_nodes,
        "issues": issues,
        "max_cycle_length_threshold": MAX_CYCLE_LENGTH,
        "max_incoming_edges_threshold": MAX_INCOMING_EDGES
    }


class CoTParser:
    """
    Main parser class for processing CoT traces.

    Provides high-level methods for parsing traces, validating them,
    and extracting logical difficulty scores.
    """

    def __init__(self, max_cycle_length: int = MAX_CYCLE_LENGTH, max_incoming_edges: int = MAX_INCOMING_EDGES):
        """
        Initialize the CoT parser.

        Args:
            max_cycle_length: Maximum allowed cycle length.
            max_incoming_edges: Maximum allowed incoming edges per node.
        """
        self.max_cycle_length = max_cycle_length
        self.max_incoming_edges = max_incoming_edges

    def parse(self, trace_text: str) -> Dict[str, Any]:
        """
        Parse a CoT trace and return comprehensive analysis.

        Args:
            trace_text: The raw CoT trace string.

        Returns:
            Dictionary containing parsed graph, validation status, and metrics.
        """
        G, parse_errors = parse_trace_to_dag(trace_text)

        if G is None:
            return {
                "success": False,
                "graph": None,
                "parse_errors": parse_errors,
                "is_valid": False,
                "difficulty": None
            }

        validation = flag_invalid_trace(G)
        difficulty = get_logical_difficulty(G)

        return {
            "success": True,
            "graph": G,
            "parse_errors": parse_errors,
            "is_valid": validation["is_valid"],
            "validation_details": validation,
            "difficulty": difficulty
        }

    def parse_and_filter(self, trace_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a trace and return None if it's invalid.

        This is a convenience method for filtering out invalid traces.

        Args:
            trace_text: The raw CoT trace string.

        Returns:
            Dictionary with analysis if valid, None if invalid.
        """
        result = self.parse(trace_text)

        if not result["is_valid"]:
            return None

        return result

    def get_depth(self, trace_text: str) -> int:
        """
        Get the logical difficulty score (max path depth) for a trace.

        Args:
            trace_text: The raw CoT trace string.

        Returns:
            Integer depth score, or 0 if parsing fails.
        """
        result = self.parse(trace_text)

        if result["success"] and result["difficulty"]:
            return result["difficulty"]["depth"]

        return 0


# Convenience functions for direct usage

def parse_trace_to_dag_and_validate(trace_text: str) -> Tuple[Optional[nx.DiGraph], bool, List[str]]:
    """
    Parse a trace and immediately validate it.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        Tuple of (graph or None, is_valid, list_of_issues).
    """
    parser = CoTParser()
    result = parser.parse(trace_text)

    if not result["success"]:
        return None, False, result.get("parse_errors", [])

    is_valid = result["is_valid"]
    issues = result.get("validation_details", {}).get("issues", [])

    return result["graph"], is_valid, issues


def get_logical_difficulty_score(trace_text: str) -> int:
    """
    Calculate the logical difficulty score for a trace.

    Args:
        trace_text: The raw CoT trace string.

    Returns:
        Integer depth score.
    """
    return get_max_path_depth(parse_trace_to_dag(trace_text)[0]) if parse_trace_to_dag(trace_text)[0] else 0

def detect_cycle(G: nx.DiGraph) -> Tuple[bool, List[List[int]]]:
    """
    Detect cycles in a directed graph.

    Args:
        G: A NetworkX DiGraph.

    Returns:
        Tuple of (has_cycle, list_of_cycles).
        Each cycle is represented as a list of node IDs.
    """
    if G is None or G.number_of_nodes() == 0:
        return False, []

    try:
        cycles = list(nx.simple_cycles(G))
        return len(cycles) > 0, cycles
    except Exception as e:
        logger.error(f"Error detecting cycles: {e}")
        return False, []