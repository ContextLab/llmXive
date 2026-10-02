import os
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Tree-sitter imports
try:
    from tree_sitter import Language, Parser
except ImportError:
    raise ImportError(
        "The 'tree-sitter' library is required. Install it via 'pip install tree-sitter'."
    )

# Constants
GRAPHS_DIR = Path("data/graphs")
PROCESSED_DIR = Path("data/processed")

# Initialize Tree-sitter (assuming python language file is available)
# In a real pipeline, we might need to build the language.so file or use a pre-built one.
# For this implementation, we assume a standard setup or fallback to simple parsing if tree-sitter fails.
PY_LANGUAGE_PATH = Path("code/resources/python.so") # Placeholder path
parser = None
if PY_LANGUAGE_PATH.exists():
    try:
        parser = Parser()
        parser.set_language(Language(str(PY_LANGUAGE_PATH), "python"))
    except Exception:
        parser = None

def load_ground_truth(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the ground truth CSV file.
    
    Args:
        csv_path: Path to the CSV file.
    
    Returns:
        List of task dictionaries.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {csv_path}")
    
    tasks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks

def filter_unparseable(tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separates tasks into parseable and unparseable based on status.
    
    Args:
        tasks: List of all tasks.
    
    Returns:
        Tuple of (parseable_tasks, unparseable_tasks).
    """
    parseable = []
    unparseable = []
    
    for task in tasks:
        status = task.get("status", "").lower()
        if status == "unparseable":
            unparseable.append(task)
        else:
            parseable.append(task)
    
    return parseable, unparseable

def get_lines_of_code(code: str) -> int:
    """
    Calculates the number of lines of code.
    
    Args:
        code: The source code string.
    
    Returns:
        Number of lines.
    """
    if not code:
        return 0
    return len(code.splitlines())

def get_cyclomatic_complexity(code: str) -> int:
    """
    Calculates cyclomatic complexity using a simple heuristic (if tree-sitter fails).
    Counts decision points: if, elif, for, while, and, or.
    
    Args:
        code: The source code string.
    
    Returns:
        Cyclomatic complexity score.
    """
    if not code:
        return 1
    
    # Simple heuristic count
    complexity = 1
    keywords = ['if ', 'elif ', 'for ', 'while ', 'except ', 'with ', 'and ', 'or ']
    for kw in keywords:
        complexity += code.count(kw)
    
    return complexity

def get_dependency_depth(tree: Any) -> int:
    """
    Calculates the maximum depth of the AST tree.
    
    Args:
        tree: The parsed tree-sitter tree.
    
    Returns:
        Maximum depth.
    """
    if not tree or not tree.root_node:
        return 0
    
    def calculate_node_depth(node, current_depth):
        if not node.children:
            return current_depth
        max_depth = current_depth
        for child in node.children:
            child_depth = calculate_node_depth(child, current_depth + 1)
            if child_depth > max_depth:
                max_depth = child_depth
        return max_depth
    
    return calculate_node_depth(tree.root_node, 1)

def calculate_semantic_complexity_score(code: str, tree: Any) -> float:
    """
    Calculates a semantic complexity score based on AST nodes.
    
    Args:
        code: The source code string.
        tree: The parsed tree-sitter tree.
    
    Returns:
        Semantic complexity score.
    """
    if not tree or not tree.root_node:
        return 0.0
    
    # Heuristic: Count specific node types that indicate complexity
    # e.g., FunctionDefinitions, ClassDefinitions, Complex expressions
    node_counts = {}
    for child in tree.root_node.children:
        node_type = child.type
        node_counts[node_type] = node_counts.get(node_type, 0) + 1
    
    # Weighted sum (example weights)
    weights = {
        "function_definition": 2,
        "class_definition": 3,
        "if_statement": 1,
        "for_statement": 1,
        "while_statement": 1,
        "try_statement": 2,
        "import_statement": 0.5
    }
    
    score = 0.0
    for node_type, count in node_counts.items():
        score += count * weights.get(node_type, 0.1)
    
    return score

def extract_graph_and_metrics(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts dependency graph and metrics for a single task.
    
    Args:
        task: The task dictionary.
    
    Returns:
        Dictionary containing metrics and graph, or None if parsing fails.
    """
    code = task.get("code_diff", "")
    task_id = task.get("task_id", "")
    
    if not code:
        return None
    
    metrics = {
        "task_id": task_id,
        "lines_of_code": get_lines_of_code(code),
        "cyclomatic_complexity": get_cyclomatic_complexity(code),
        "dependency_depth": 0,
        "semantic_complexity_score": 0.0,
        "graph": None
    }
    
    # Try to parse with tree-sitter
    if parser:
        try:
            tree = parser.parse(bytes(code, "utf8"))
            metrics["dependency_depth"] = get_dependency_depth(tree)
            metrics["semantic_complexity_score"] = calculate_semantic_complexity_score(code, tree)
            # Serialize graph (simplified)
            metrics["graph"] = _serialize_tree_to_dict(tree.root_node)
        except Exception as e:
            # Fallback if parsing fails
            print(f"Warning: Tree-sitter parsing failed for {task_id}: {e}")
            metrics["dependency_depth"] = 0
            metrics["semantic_complexity_score"] = 0.0
    else:
        # Fallback if parser not initialized
        print(f"Warning: Tree-sitter parser not available for {task_id}. Using fallback metrics.")
    
    return metrics

def _serialize_tree_to_dict(node: Any) -> Dict[str, Any]:
    """
    Helper to serialize a tree-sitter node to a dictionary.
    
    Args:
        node: Tree-sitter node.
    
    Returns:
        Dictionary representation.
    """
    if not node:
        return {}
    
    result = {
        "type": node.type,
        "start_point": [node.start_point.row, node.start_point.column],
        "end_point": [node.end_point.row, node.end_point.column],
        "children": []
    }
    
    for child in node.children:
        result["children"].append(_serialize_tree_to_dict(child))
    
    return result

def serialize_graph(metrics: Dict[str, Any], output_dir: Path) -> None:
    """
    Serializes the graph for a task to a JSON file.
    
    Args:
        metrics: The metrics dictionary containing the graph.
        output_dir: Directory to save the graph file.
    """
    task_id = metrics.get("task_id", "unknown")
    graph_data = metrics.get("graph")
    
    if not graph_data:
        return
    
    output_path = output_dir / f"{task_id}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)

def load_graph_metrics(graphs_dir: Path) -> List[Dict[str, Any]]:
    """
    Loads graph metrics from the graphs directory.
    
    Args:
        graphs_dir: Path to the directory containing graph JSONs.
    
    Returns:
        List of metrics dictionaries.
    """
    metrics_list = []
    if not graphs_dir.exists():
        return metrics_list
    
    for file_path in graphs_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # We need to reconstruct the metrics structure if not fully stored
                # Assuming the graph file contains the necessary info or we re-calculate
                # For this task, we assume the graph file is just the graph, 
                # and we might need to re-associate with task_id from filename.
                # However, the main flow saves metrics in a CSV. 
                # This function is for loading if we stored them separately.
                # Let's assume we stored a combined metrics file or we just read the graph.
                # For simplicity in this refactored version, we might just return the graph data
                # and let the main function handle the merging.
                metrics_list.append({"graph": data, "task_id": file_path.stem})
        except json.JSONDecodeError:
            continue
    
    return metrics_list

def main():
    """
    Main entry point for feature extraction.
    Loads ground truth, calculates metrics, and saves results.
    """
    print("Starting feature extraction...")
    
    ground_truth_path = PROCESSED_DIR / "ground_truth.csv"
    graphs_dir = GRAPHS_DIR
    features_path = PROCESSED_DIR / "features.csv"
    
    # Ensure directories exist
    graphs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load ground truth
    try:
        all_tasks = load_ground_truth(ground_truth_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # 2. Filter unparseable
    parseable_tasks, unparseable_tasks = filter_unparseable(all_tasks)
    print(f"Processing {len(parseable_tasks)} parseable tasks.")
    print(f"Skipping {len(unparseable_tasks)} unparseable tasks.")
    
    # 3. Extract metrics
    all_metrics = []
    for task in parseable_tasks:
        metrics = extract_graph_and_metrics(task)
        if metrics:
            all_metrics.append(metrics)
            # 4. Serialize graph
            serialize_graph(metrics, graphs_dir)
    
    # 5. Merge with ground truth to create features.csv
    # We need to merge metrics back into the task structure
    # Create a lookup for metrics
    metrics_lookup = {m["task_id"]: m for m in all_metrics}
    
    features_rows = []
    for task in all_tasks:
        task_id = task.get("task_id")
        metrics = metrics_lookup.get(task_id, {})
        
        row = {
            "task_id": task_id,
            "code_diff": task.get("code_diff", ""),
            "dynamic_execution_outcome": task.get("dynamic_execution_outcome", "N/A"),
            "status": task.get("status", "parsed"),
            "lines_of_code": metrics.get("lines_of_code", 0),
            "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
            "dependency_depth": metrics.get("dependency_depth", 0),
            "semantic_complexity_score": metrics.get("semantic_complexity_score", 0.0)
        }
        features_rows.append(row)
    
    # 6. Write features CSV
    with open(features_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["task_id", "code_diff", "dynamic_execution_outcome", "status", 
                      "lines_of_code", "cyclomatic_complexity", "dependency_depth", "semantic_complexity_score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features_rows)
    
    print(f"Feature extraction complete. Saved to {features_path}")

if __name__ == "__main__":
    main()