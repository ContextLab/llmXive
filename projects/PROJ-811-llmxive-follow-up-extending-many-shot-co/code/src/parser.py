"""
CoT Trace Parser for Logical Dependency Graph Construction.

Implements:
- Parsing text traces into NetworkX DAGs.
- Cycle detection (length <= 5).
- Incoming edge threshold logic (>3 edges from >10 lines prior).
- Logical Difficulty Score (max path depth).
- Validation logic for filtering invalid traces.
"""
import networkx as nx
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Regex patterns for step identification
# Matches patterns like "Step 1:", "1.", "(1)", "First:", "Second:"
STEP_PATTERNS = [
    r'(?:^|\n)\s*(?:Step\s*\d+[:\.]?\s*|\d+[\.\)]\s*|\(?\d+\)?\s*|(?:First|Second|Third|Fourth|Fifth)[:\.]?\s*)',
    r'(?:^|\n)\s*(?:Therefore|Thus|Hence|So|Conclusion)[:\.]?\s*',
    r'(?:^|\n)\s*(?:(?:Assumption|Premise|Fact)[:\.]?\s*:\s*)'
]

def split_trace_into_steps(trace_text: str) -> List[str]:
    """
    Split a CoT trace into logical steps.
    Heuristic: Split on common step markers or newlines if markers are absent.
    """
    if not trace_text or not trace_text.strip():
        return []

    # Try to find explicit step markers
    steps = []
    current_step = ""
    
    # Simple heuristic: split by newline and group if no marker found
    lines = trace_text.split('\n')
    
    current_step_lines = []
    has_marker = False
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check for step marker
        is_marker = any(re.search(p, line, re.IGNORECASE) for p in STEP_PATTERNS)
        
        if is_marker:
            if current_step_lines:
                steps.append("\n".join(current_step_lines))
            current_step_lines = [line_stripped]
            has_marker = True
        else:
            current_step_lines.append(line_stripped)
    
    if current_step_lines:
        steps.append("\n".join(current_step_lines))
    
    # Fallback: if no markers found, treat each non-empty line as a step
    if not has_marker and not steps:
        steps = [line for line in lines if line.strip()]
        
    return steps

def extract_dependencies(step_text: str, all_steps: List[str], step_index: int) -> List[int]:
    """
    Extract dependency indices from a step text.
    Looks for references to other steps (e.g., "based on step 1", "as shown in 2").
    """
    dependencies = []
    text_lower = step_text.lower()
    
    # Pattern to find references to step numbers
    # Matches "step 1", "step 2", "1", "2", etc.
    # We look for numbers that appear in context of dependency
    ref_patterns = [
        r'(?:step|based on|as shown in|referencing|from)\s*(\d+)',
        r'(?:see|cf)\s*(\d+)',
        r'(?:\(\d+\))' # (1) style references
    ]
    
    found_indices = set()
    for pattern in ref_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            try:
                ref_idx = int(match) - 1 # Assume 1-based indexing in text
                if 0 <= ref_idx < step_index and ref_idx not in found_indices:
                    found_indices.add(ref_idx)
                    dependencies.append(ref_idx)
            except ValueError:
                continue
                
    # Heuristic: If a step contains "because", "since", "due to" and mentions a number
    causal_words = ['because', 'since', 'due to', 'as a result of', 'based on']
    if any(word in text_lower for word in causal_words):
        # If no explicit number found but causal words exist, assume dependency on previous step
        if not dependencies and step_index > 0:
            dependencies.append(step_index - 1)
            
    return dependencies

def parse_trace_to_dag(trace_text: str) -> nx.DiGraph:
    """
    Parse a CoT trace into a Directed Acyclic Graph (DAG).
    """
    steps = split_trace_into_steps(trace_text)
    G = nx.DiGraph()
    
    if not steps:
        return G
        
    # Add nodes
    for i, step in enumerate(steps):
        G.add_node(i, text=step, step_number=i+1)
        
    # Add edges based on dependencies
    for i, step in enumerate(steps):
        deps = extract_dependencies(step, steps, i)
        for dep in deps:
            if dep != i: # No self-loops
                G.add_edge(dep, i)
                
    return G

def detect_cycle(G: nx.DiGraph, max_length: int = 5) -> Optional[List[int]]:
    """
    Detect cycles in the graph.
    Returns a list of node indices forming a cycle if found (length <= max_length).
    Returns None if no cycle found.
    """
    try:
        # Find all simple cycles
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            if len(cycle) <= max_length:
                return list(cycle)
        return None
    except Exception as e:
        logger.error(f"Error detecting cycles: {e}")
        return None

def check_incoming_edge_threshold(G: nx.DiGraph, steps: List[str], threshold: int = 3, line_gap: int = 10) -> Optional[Tuple[int, int]]:
    """
    Check for nodes with > threshold incoming edges from steps occurring > line_gap lines prior.
    Returns (node_index, incoming_count) if violation found, else None.
    """
    # Estimate line numbers for each step
    # This is a heuristic since we don't have exact line numbers from split
    # We assume each step is roughly 1-3 lines.
    step_line_starts = []
    current_line = 0
    for step in steps:
        step_line_starts.append(current_line)
        current_line += step.count('\n') + 1
        
    for node in G.nodes():
        incoming_edges = list(G.in_edges(node))
        if len(incoming_edges) > threshold:
            # Check the line gap for incoming edges
            violating_edges = 0
            for src, dst in incoming_edges:
                src_line = step_line_starts[src] if src < len(step_line_starts) else 0
                dst_line = step_line_starts[dst] if dst < len(step_line_starts) else 0
                if (dst_line - src_line) > line_gap:
                    violating_edges += 1
                    
            if violating_edges > threshold:
                return (node, len(incoming_edges))
                
    return None

def get_max_path_depth(G: nx.DiGraph) -> int:
    """
    Calculate the maximum path depth (longest path) in the DAG.
    This serves as the "Logical Difficulty Score".
    """
    if G.number_of_nodes() == 0:
        return 0
    if not nx.is_directed_acyclic_graph(G):
        # Should not happen if called after validation, but safe fallback
        return 0
        
    try:
        longest_path = nx.dag_longest_path(G)
        return len(longest_path)
    except nx.NetworkXUnfeasible:
        return 0

def parse_trace_to_dag_and_validate(trace_text: str) -> Tuple[nx.DiGraph, bool, Dict[str, Any]]:
    """
    Parse a trace to a DAG and validate it.
    
    Returns:
        Tuple of (DAG, is_valid, validation_details)
    """
    validation_details = {
        "is_valid": True,
        "reason": "Valid",
        "cycle_detected": False,
        "threshold_violation": False
    }
    
    if not trace_text or not trace_text.strip():
        validation_details["is_valid"] = False
        validation_details["reason"] = "Empty trace"
        return nx.DiGraph(), False, validation_details
        
    G = parse_trace_to_dag(trace_text)
    
    if G.number_of_nodes() == 0:
        validation_details["is_valid"] = False
        validation_details["reason"] = "No steps parsed"
        return G, False, validation_details
        
    # Check for cycles
    cycle = detect_cycle(G)
    if cycle:
        validation_details["is_valid"] = False
        validation_details["reason"] = f"Cycle detected: {cycle}"
        validation_details["cycle_detected"] = True
        return G, False, validation_details
        
    # Check incoming edge threshold
    # We need to reconstruct steps list for this check
    steps = split_trace_into_steps(trace_text)
    threshold_violation = check_incoming_edge_threshold(G, steps)
    if threshold_violation:
        validation_details["is_valid"] = False
        validation_details["reason"] = f"Threshold violation: Node {threshold_violation[0]} has {threshold_violation[1]} old incoming edges"
        validation_details["threshold_violation"] = True
        return G, False, validation_details
        
    return G, True, validation_details

def is_trace_valid(trace_text: str) -> bool:
    """
    Simple check if a trace is valid.
    """
    _, is_valid, _ = parse_trace_to_dag_and_validate(trace_text)
    return is_valid

def get_logical_difficulty(G: nx.DiGraph) -> int:
    """
    Get the logical difficulty score (max path depth).
    """
    return get_max_path_depth(G)

def flag_invalid_trace(trace_text: str) -> Dict[str, Any]:
    """
    Flag a trace as invalid if it contains cycles or threshold violations.
    Returns a dictionary with the flag status and reason.
    """
    _, is_valid, details = parse_trace_to_dag_and_validate(trace_text)
    return {
        "is_valid": is_valid,
        "reason": details["reason"]
    }
