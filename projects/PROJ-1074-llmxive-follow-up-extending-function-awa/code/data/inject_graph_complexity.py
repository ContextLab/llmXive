import json
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from project utils
from utils.common import (
    get_logger,
    PipelineError,
    ensure_dir,
    read_json,
    write_json,
)
from data.validate_dependencies import detect_cycle, topological_sort

logger = get_logger(__name__)

def inject_branching(graph: Dict[str, List[str]], steps: List[str]) -> Dict[str, List[str]]:
    """
    Inject branching (fan-out) into a dependency graph.
    
    Finds leaf nodes or intermediate nodes and adds edges to create
    multiple dependencies for a single step, simulating non-linear logic.
    
    Args:
        graph: Adjacency list {node: [dependencies]}
        steps: List of all valid step names (e.g., ["step_1", "step_2"])
    
    Returns:
        Modified graph with branching injected.
    """
    if not graph:
        return graph
    
    modified_graph = {k: list(v) for k, v in graph.items()}
    
    # Identify nodes that can be targets for branching
    # We look for nodes that have at least one dependency but are not the final node
    # or nodes that are currently leaves (no dependents) to make them depend on multiple sources
    
    all_nodes = set(modified_graph.keys())
    all_deps = set()
    for deps in modified_graph.values():
        all_deps.update(deps)
    
    # Nodes that are dependencies (sources)
    source_candidates = list(all_deps)
    # Nodes that are not sinks (have dependencies)
    intermediate_candidates = [n for n in all_nodes if modified_graph.get(n, [])]
    
    if not source_candidates or not intermediate_candidates:
        return modified_graph
    
    # Inject branching: Make an intermediate node depend on an extra source
    # Select a random intermediate node (deterministic for reproducibility if needed, 
    # but here we just pick the first available for simplicity in logic)
    target_node = intermediate_candidates[0]
    
    # Find a source that is NOT already a dependency of target_node
    current_deps = set(modified_graph[target_node])
    extra_deps = [s for s in source_candidates if s not in current_deps]
    
    if extra_deps:
        # Add one extra dependency to create a merge/branch point
        # We pick the first available to ensure determinism in this simple implementation
        # In a more complex version, we might randomize or pick based on depth
        extra_dep = extra_deps[0]
        modified_graph[target_node].append(extra_dep)
        logger.debug(f"Injected branching: {target_node} now depends on {extra_dep} in addition to existing.")
    
    return modified_graph

def inject_merging(graph: Dict[str, List[str]], steps: List[str]) -> Dict[str, List[str]]:
    """
    Inject merging (fan-in) into a dependency graph.
    
    Creates a new node or modifies an existing one to depend on multiple 
    independent branches, ensuring the graph is not purely linear.
    
    Args:
        graph: Adjacency list {node: [dependencies]}
        steps: List of all valid step names
    
    Returns:
        Modified graph with merging injected.
    """
    if not graph:
        return graph
    
    modified_graph = {k: list(v) for k, v in graph.items()}
    
    # Identify independent branches (nodes with no incoming edges from each other)
    all_nodes = set(modified_graph.keys())
    incoming = {n: set() for n in all_nodes}
    for node, deps in modified_graph.items():
        for dep in deps:
            if dep in incoming:
                incoming[dep].add(node)
    
    # Find nodes with no incoming edges (roots)
    roots = [n for n, deps in incoming.items() if not deps]
    
    if len(roots) < 2:
        # If we don't have enough roots, we create a virtual merge point
        # by making a leaf depend on two existing nodes that are far apart in the chain
        # For simplicity, we just ensure the last node depends on at least two previous nodes
        sorted_nodes = topological_sort(modified_graph)
        if len(sorted_nodes) >= 3:
            # Make the last node depend on the first two nodes
            last_node = sorted_nodes[-1]
            first_node = sorted_nodes[0]
            second_node = sorted_nodes[1]
            
            if first_node not in modified_graph[last_node]:
                modified_graph[last_node].append(first_node)
            if second_node not in modified_graph[last_node]:
                modified_graph[last_node].append(second_node)
            logger.debug(f"Injected merging: {last_node} now depends on {first_node} and {second_node}.")
    else:
        # If we have multiple roots, we can create a new node that depends on two roots
        # Or modify an existing leaf to depend on two roots
        # Simple strategy: find a leaf and make it depend on two roots
        leaves = [n for n in all_nodes if n not in [d for deps in modified_graph.values() for d in deps]]
        if leaves:
            leaf = leaves[0]
            # Ensure leaf depends on at least two roots
            current_deps = set(modified_graph.get(leaf, []))
            roots_to_add = [r for r in roots if r not in current_deps][:2]
            
            for r in roots_to_add:
                if r not in modified_graph[leaf]:
                    modified_graph[leaf].append(r)
            logger.debug(f"Injected merging: {leaf} now depends on roots {roots_to_add}.")
    
    return modified_graph

def validate_complexity(graph: Dict[str, List[str]], steps: List[str]) -> Tuple[bool, str]:
    """
    Validates that the graph has non-linear properties (branching or merging).
    
    A linear graph has max in-degree <= 1 and max out-degree <= 1 (for the chain).
    We check for in-degree > 1 (merging) or out-degree > 1 (branching).
    """
    in_degree = {n: 0 for n in graph}
    out_degree = {n: len(deps) for n, deps in graph.items()}
    
    for deps in graph.values():
        for d in deps:
            if d in in_degree:
                in_degree[d] += 1
    
    max_in = max(in_degree.values()) if in_degree else 0
    max_out = max(out_degree.values()) if out_degree else 0
    
    if max_in > 1:
        return True, f"Merging detected: max in-degree = {max_in}"
    if max_out > 1:
        return True, f"Branching detected: max out-degree = {max_out}"
    
    return False, "Graph is linear (no branching or merging detected)"

def process_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single example from the intermediate steps file.
    
    Args:
        example: Dict containing 'steps', 'dependency_graph', etc.
    
    Returns:
        Updated example with complexity injected.
    """
    steps = example.get("steps", [])
    graph = example.get("dependency_graph", {})
    
    if not graph:
        # If no graph, create a simple one or skip
        logger.warning(f"Skipping example with no dependency graph: {example.get('id', 'unknown')}")
        return example
    
    # Try to inject branching first
    modified_graph = inject_branching(graph, steps)
    
    # Then try to inject merging
    modified_graph = inject_merging(modified_graph, steps)
    
    # Validate the result
    has_complexity, msg = validate_complexity(modified_graph, steps)
    
    if not has_complexity:
        # If we couldn't inject complexity, we might need to skip or log
        # For this task, we assume the injection logic above is sufficient for most cases
        # If it fails, we still return the graph but log a warning
        logger.warning(f"Could not inject complexity for example {example.get('id', 'unknown')}: {msg}")
    
    # Ensure no cycles were introduced
    if detect_cycle(modified_graph):
        logger.error(f"Cycle detected after complexity injection for example {example.get('id', 'unknown')}. Reverting.")
        # Revert to original if cycle introduced (should not happen with our logic)
        modified_graph = graph
    
    # Update the example
    example["dependency_graph"] = modified_graph
    example["complexity_injected"] = True
    example["complexity_message"] = msg
    
    return example

def main():
    """
    Main entry point for injecting graph complexity.
    
    Reads intermediate steps from data/processed/intermediate_steps.jsonl
    and dependency graphs from data/processed/dependency_graphs.json
    (Note: The task description says it requires output of T014/T015. 
     T014 outputs intermediate_steps.jsonl. T015 outputs dependency_graphs.json.
     However, the convert_to_pseudo_code.py likely outputs both in a combined structure 
     or the dependency_graphs.json is a separate file. 
     Looking at the task T015: "output data/processed/dependency_graphs.json".
     Looking at T014: "output intermediate artifacts to data/processed/intermediate_steps.jsonl".
     
     We assume the dependency graph is embedded in the intermediate_steps.jsonl 
     OR we load the separate dependency_graphs.json and merge.
     
     Given the flow, it's most likely that the intermediate_steps.jsonl contains the graph
     per example, or we need to correlate. 
     
     Let's assume the intermediate_steps.jsonl has the graph per record.
     If not, we might need to load the separate file.
     
     Based on T015 description: "output data/processed/dependency_graphs.json".
     This suggests a separate file. However, T016 says "requires output of T014/T015".
     
     Strategy:
     1. Load intermediate_steps.jsonl (from T014)
     2. If the graph is not inside each record, load dependency_graphs.json (from T015)
        and merge by ID.
     3. Inject complexity.
     4. Write to complexity_injected_graphs.json.
    """
    parser = argparse.ArgumentParser(description="Inject graph complexity into synthetic dataset")
    parser.add_argument("--input-steps", type=str, default="data/processed/intermediate_steps.jsonl",
                        help="Path to intermediate steps JSONL")
    parser.add_argument("--input-graphs", type=str, default="data/processed/dependency_graphs.json",
                        help="Path to dependency graphs JSON (if separate)")
    parser.add_argument("--output", type=str, default="data/processed/complexity_injected_graphs.json",
                        help="Path to output file")
    args = parser.parse_args()
    
    input_steps_path = Path(args.input_steps)
    input_graphs_path = Path(args.input_graphs)
    output_path = Path(args.output)
    
    ensure_dir(output_path.parent)
    
    if not input_steps_path.exists():
        raise FileNotFoundError(f"Input steps file not found: {input_steps_path}")
    
    # Load intermediate steps
    examples = []
    with open(input_steps_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    logger.info(f"Loaded {len(examples)} examples from {input_steps_path}")
    
    # Check if graphs are already in the examples
    # If not, try to load from the separate file
    graphs_map = {}
    if input_graphs_path.exists():
        with open(input_graphs_path, "r", encoding="utf-8") as f:
            graphs_data = json.load(f)
            # Assume graphs_data is a dict or list of dicts with 'id' and 'graph'
            if isinstance(graphs_data, dict):
                graphs_map = graphs_data
            elif isinstance(graphs_data, list):
                for g in graphs_data:
                    if "id" in g:
                        graphs_map[g["id"]] = g.get("graph", {})
    
    processed_examples = []
    complexity_stats = {
        "total": 0,
        "injected": 0,
        "skipped": 0,
        "errors": 0
    }
    
    for example in examples:
        example_id = example.get("id", "unknown")
        complexity_stats["total"] += 1
        
        # Get graph from example or from map
        graph = example.get("dependency_graph", {})
        if not graph and example_id in graphs_map:
            graph = graphs_map[example_id]
            example["dependency_graph"] = graph
        
        if not graph:
            logger.warning(f"No graph found for example {example_id}. Skipping.")
            complexity_stats["skipped"] += 1
            processed_examples.append(example)
            continue
        
        try:
            processed = process_example(example)
            processed_examples.append(processed)
            complexity_stats["injected"] += 1
        except Exception as e:
            logger.error(f"Error processing example {example_id}: {e}")
            complexity_stats["errors"] += 1
            # Still add the example but mark as failed
            example["complexity_injected"] = False
            example["complexity_error"] = str(e)
            processed_examples.append(example)
    
    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_examples, f, indent=2)
    
    logger.info(f"Processed {complexity_stats['total']} examples. Injected: {complexity_stats['injected']}, Skipped: {complexity_stats['skipped']}, Errors: {complexity_stats['errors']}")
    logger.info(f"Output written to {output_path}")
    
    # Also write stats to a separate file for reporting
    stats_path = output_path.parent / "complexity_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(complexity_stats, f, indent=2)
    logger.info(f"Stats written to {stats_path}")

if __name__ == "__main__":
    main()