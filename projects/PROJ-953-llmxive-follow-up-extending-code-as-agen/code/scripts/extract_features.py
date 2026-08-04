import os
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import tree-sitter for AST parsing
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
except ImportError:
    # Graceful failure if dependencies not installed, though requirements.txt should handle this
    raise ImportError("Missing required dependency: tree_sitter and tree_sitter_python. "
                      "Please install them via 'pip install tree-sitter tree-sitter-python'.")

# Project root path assumption
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_GRAPHS_DIR = PROJECT_ROOT / "data" / "graphs"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Ensure output directories exist
DATA_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_ground_truth(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads the ground truth CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def filter_unparseable(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out tasks marked as 'Unparseable' in the dynamic_execution_outcome or a specific status flag.
    Based on T016, unparseable tasks are flagged. We assume a status column or outcome check.
    """
    filtered = []
    for task in tasks:
        outcome = task.get('dynamic_execution_outcome', '').lower()
        # If the task was marked unparseable during ingestion/baseline, skip it here
        if 'unparseable' in outcome or task.get('status', '').lower() == 'unparseable':
            continue
        filtered.append(task)
    return filtered

def get_lines_of_code(code_str: str) -> int:
    """
    Calculates lines of code (non-empty, non-comment).
    """
    if not code_str:
        return 0
    lines = code_str.split('\n')
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            count += 1
    return count

def get_cyclomatic_complexity(code_str: str) -> int:
    """
    Calculates cyclomatic complexity using tree-sitter.
    """
    if not code_str:
        return 0
    
    try:
        tree = _parse_code(code_str)
        if not tree:
            return 0
    except Exception:
        # Fallback if parsing fails, return 1 (base complexity)
        return 1

    complexity = 1
    root = tree.root_node

    # Decision points: if, for, while, except, with, and, or
    decision_keywords = {
        'if', 'for', 'while', 'except', 'with', 'assert', 'match'
    }

    for node in root.walk():
        if node.type in decision_keywords:
            complexity += 1
        # Handle logical operators 'and', 'or' if they appear as nodes
        if node.type == 'boolean_operator':
            complexity += 1
    
    return complexity

def get_dependency_depth(code_str: str) -> int:
    """
    Calculates the maximum depth of the AST, representing dependency depth.
    """
    if not code_str:
        return 0
    
    try:
        tree = _parse_code(code_str)
        if not tree:
            return 0
    except Exception:
        return 0

    def max_depth(node, current_depth=0):
        if not node.children:
            return current_depth
        max_d = current_depth
        for child in node.children:
            d = max_depth(child, current_depth + 1)
            if d > max_d:
                max_d = d
        return max_d

    return max_depth(tree.root_node)

def calculate_semantic_complexity_score(code_str: str) -> Optional[float]:
    """
    Calculates a semantic complexity score based on specific node counts.
    Returns None if specific nodes are missing (triggering fallback in T021/T022).
    """
    if not code_str:
        return None
    
    try:
        tree = _parse_code(code_str)
        if not tree:
            return None
    except Exception:
        return None

    root = tree.root_node
    
    # Count specific semantic nodes
    node_counts = {
        'function_definition': 0,
        'class_definition': 0,
        'import_statement': 0,
        'return_statement': 0
    }

    for node in root.walk():
        if node.type in node_counts:
            node_counts[node.type] += 1
    
    # Heuristic: if no functions or classes, it's a script, low semantic complexity
    # If many functions/classes, higher complexity
    score = (
        node_counts['function_definition'] * 1.5 +
        node_counts['class_definition'] * 2.0 +
        node_counts['import_statement'] * 0.5 +
        node_counts['return_statement'] * 0.2
    )
    
    # Check if we have enough semantic structure
    if node_counts['function_definition'] == 0 and node_counts['class_definition'] == 0:
        # Might be too simple to have a meaningful "semantic" score in this context
        # Return None to trigger fallback logic as per T022
        return None
        
    return score

def _parse_code(code_str: str):
    """
    Helper to parse code string into a tree-sitter tree.
    """
    # Initialize parser once (could be cached globally for performance)
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    
    code_bytes = code_str.encode('utf-8')
    tree = parser.parse(code_bytes)
    return tree

def extract_graph_and_metrics(task: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extracts the dependency graph structure and calculates metrics for a single task.
    Returns (graph_dict, metrics_dict).
    """
    code_diff = task.get('code_diff', '')
    task_id = task.get('task_id', 'unknown')
    
    # Use original code if diff is empty or invalid, but usually diff is the target
    source_code = code_diff if code_diff else task.get('original_code', '')
    
    if not source_code:
        return {}, {"error": "No code found"}

    graph_data = {
        "task_id": task_id,
        "nodes": [],
        "edges": []
    }

    try:
        tree = _parse_code(source_code)
        root = tree.root_node
    except Exception as e:
        return {}, {"error": f"Parse failed: {str(e)}"}

    # Traverse to build graph
    node_id_map = {}
    node_counter = 0

    def traverse(node, parent_id=None):
        nonlocal node_counter
        current_id = f"n{node_counter}"
        node_counter += 1
        
        node_type = node.type
        start_point = node.start_point
        end_point = node.end_point
        
        node_info = {
            "id": current_id,
            "type": node_type,
            "start": start_point,
            "end": end_point
        }
        
        graph_data["nodes"].append(node_info)
        node_id_map[node] = current_id

        if parent_id is not None:
            graph_data["edges"].append({
                "source": parent_id,
                "target": current_id,
                "type": "child_of"
            })

        for child in node.children:
            traverse(child, current_id)

    traverse(root)

    # Calculate metrics
    metrics = {
        "task_id": task_id,
        "lines_of_code": get_lines_of_code(source_code),
        "cyclomatic_complexity": get_cyclomatic_complexity(source_code),
        "dependency_depth": get_dependency_depth(source_code),
        "semantic_complexity_score": calculate_semantic_complexity_score(source_code)
    }

    return graph_data, metrics

def serialize_graph(graph_data: Dict[str, Any], task_id: str) -> str:
    """
    Serializes the dependency graph to a JSON file in data/graphs/{task_id}.json.
    Returns the path to the written file.
    """
    if not graph_data:
        return None

    # Sanitize task_id for filename
    safe_id = str(task_id).replace("/", "_").replace("\\", "_")
    output_path = DATA_GRAPHS_DIR / f"{safe_id}.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    
    return str(output_path)

def main():
    """
    Main entry point for T023: Serialize dependency graphs.
    This script loads ground_truth.csv, processes parseable tasks,
    calculates metrics, and serializes graphs to data/graphs/{task_id}.json.
    It also updates the state and prepares for features.csv generation (T024).
    """
    ground_truth_path = DATA_PROCESSED_DIR / "ground_truth.csv"
    
    if not ground_truth_path.exists():
        print(f"Error: {ground_truth_path} not found. Run T015 first.")
        sys.exit(1)

    print(f"Loading ground truth from {ground_truth_path}...")
    tasks = load_ground_truth(str(ground_truth_path))
    print(f"Loaded {len(tasks)} tasks.")

    parseable_tasks = filter_unparseable(tasks)
    print(f"Processing {len(parseable_tasks)} parseable tasks.")

    all_metrics = []
    processed_count = 0

    for task in parseable_tasks:
        task_id = task.get('task_id', 'unknown')
        try:
            graph_data, metrics = extract_graph_and_metrics(task)
            
            if graph_data:
                path = serialize_graph(graph_data, task_id)
                if path:
                    metrics['graph_path'] = path
                    processed_count += 1
                    print(f"  Serialized graph for {task_id} -> {path}")
            
            all_metrics.append(metrics)
            
        except Exception as e:
            print(f"  Error processing {task_id}: {e}")
            # Record error in metrics to ensure we don't lose the row in features.csv
            all_metrics.append({
                "task_id": task_id,
                "error": str(e),
                "lines_of_code": 0,
                "cyclomatic_complexity": 0,
                "dependency_depth": 0,
                "semantic_complexity_score": None
            })

    print(f"Successfully processed and serialized {processed_count} graphs.")
    
    # Note: T024 will handle the actual merging into features.csv,
    # but we can output a temporary CSV here for verification if needed.
    # For T023, the primary deliverable is the JSON files in data/graphs/.
    
    # Update state for T023 completion
    try:
        from scripts.update_state import update_task_status, add_artifact
        # Ensure state module is available (T005)
        update_task_status("T023", "completed")
        # Add artifact count
        add_artifact("T023", "graph_files", f"{processed_count} JSON files in data/graphs/")
    except ImportError:
        print("Warning: Could not update state (scripts/update_state.py missing).")

    return all_metrics

if __name__ == "__main__":
    main()