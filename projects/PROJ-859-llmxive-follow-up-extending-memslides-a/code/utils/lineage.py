import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime

class LineageError(Exception):
    """Custom exception for lineage generation errors."""
    pass

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the project state file which records artifact hashes and dependencies.
    """
    if not state_path.exists():
        raise LineageError(f"State file not found: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_exclusion_log(exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the exclusion log to identify traces that were excluded from processing.
    """
    if not exclusion_log_path.exists():
        # If no exclusions occurred, return empty list
        return []
    
    exclusions = []
    with open(exclusion_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    exclusions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return exclusions

def get_raw_trace_sources(data_dir: Path) -> List[str]:
    """
    Scan data/raw and data/training directories to find all source trace files.
    Returns a list of relative paths.
    """
    sources = []
    for subdir in ['raw', 'training']:
        dir_path = data_dir / subdir
        if dir_path.exists():
            for file_path in dir_path.glob('*.json'):
                rel_path = str(file_path.relative_to(data_dir))
                sources.append(rel_path)
    return sorted(sources)

def build_dag(state_data: Dict[str, Any], exclusion_log: List[Dict[str, Any]], raw_sources: List[str]) -> Dict[str, Any]:
    """
    Build a Directed Acyclic Graph (DAG) representation of data transformations.
    Nodes are artifacts, edges represent 'derived_from' relationships.
    """
    dag = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "nodes": {},
        "edges": []
    }

    # 1. Add Raw Source Nodes
    for source in raw_sources:
        node_id = f"raw/{source}"
        dag["nodes"][node_id] = {
            "id": node_id,
            "type": "raw_data",
            "path": source,
            "status": "source"
        }

    # 2. Add Excluded Trace Nodes (as leaf nodes with status 'excluded')
    for entry in exclusion_log:
        trace_id = entry.get("trace_id", "unknown")
        node_id = f"excluded/{trace_id}"
        dag["nodes"][node_id] = {
            "id": node_id,
            "type": "excluded_data",
            "trace_id": trace_id,
            "reason": entry.get("exclusion_reason", "unknown"),
            "status": "excluded"
        }
        # If we know the source file, link it
        source_file = entry.get("source_file")
        if source_file:
            parent_id = f"raw/{source_file}"
            if parent_id in dag["nodes"]:
                dag["edges"].append({
                    "from": parent_id,
                    "to": node_id,
                    "relation": "excluded_by"
                })

    # 3. Add Processed Artifact Nodes based on state file
    # We assume the state file has a structure like:
    # { "artifacts": { "path/to/file": { "hash": "...", "dependencies": [...] } } }
    artifacts = state_data.get("artifacts", {})
    
    # Map known processed paths to their dependencies
    processed_artifacts = {
        "data/processed/feature_matrix.csv": ["data/training/*.json", "data/held_out/*.json"],
        "data/processed/per_trace_scores.csv": ["data/processed/feature_matrix.csv"],
        "data/processed/rules/global_rules.json": ["data/processed/per_trace_scores.csv"],
        "data/processed/benchmark_results.json": ["data/processed/rules/global_rules.json", "data/held_out/*.json"],
        "data/processed/accuracy_deltas.csv": ["data/processed/benchmark_results.json"],
        "data/processed/statistical_analysis.json": ["data/processed/accuracy_deltas.csv", "data/processed/feature_matrix.csv"],
        "data/processed/sensitivity_sweep.csv": ["data/processed/benchmark_results.json", "data/processed/rules/global_rules.json"],
        "data/processed/exclusion_log.json": ["data/training/*.json"], # Implicit
        "data/processed/exclusion_summary.md": ["data/processed/exclusion_log.json"]
    }

    # Register all known processed artifacts
    for path, deps in processed_artifacts.items():
        node_id = path
        # Check if state file has specific hash info for this path
        state_info = artifacts.get(path, {})
        dag["nodes"][node_id] = {
            "id": node_id,
            "type": "processed_data",
            "path": path,
            "hash": state_info.get("hash", "unknown"),
            "status": "derived"
        }

        # Add edges from dependencies
        for dep_pattern in deps:
            # Simple pattern matching for dependencies
            if dep_pattern.endswith("*.json"):
                # Link to training or held_out
                base_dir = dep_pattern.split("*.")[0].replace("data/", "data/")
                if "training" in dep_pattern:
                    # Link to all training sources
                    for src in raw_sources:
                        if "training" in src:
                            dag["edges"].append({
                                "from": f"raw/{src}",
                                "to": node_id,
                                "relation": "derived_from"
                            })
                elif "held_out" in dep_pattern:
                    for src in raw_sources:
                        if "held_out" in src:
                            dag["edges"].append({
                                "from": f"raw/{src}",
                                "to": node_id,
                                "relation": "derived_from"
                            })
            elif dep_pattern.endswith("*.csv") or dep_pattern.endswith("*.json"):
                # Direct file dependency
                if dep_pattern in processed_artifacts:
                    dag["edges"].append({
                        "from": dep_pattern,
                        "to": node_id,
                        "relation": "derived_from"
                    })
            elif dep_pattern in artifacts:
                # Direct match in state file
                dag["edges"].append({
                    "from": dep_pattern,
                    "to": node_id,
                    "relation": "derived_from"
                })

    return dag

def generate_dot_file(dag: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a GraphViz DOT file from the DAG structure.
    """
    lines = [
        "digraph DataLineage {",
        "  rankdir=LR;",
        "  node [shape=box, style=filled];",
        ""
    ]

    # Define node styles based on type
    node_styles = {
        "raw_data": 'fillcolor="#90EE90"',  # Light Green
        "excluded_data": 'fillcolor="#FFB6C1", style="filled,dashed"', # Light Red
        "processed_data": 'fillcolor="#87CEEB"'  # Light Blue
    }

    for node_id, node_data in dag["nodes"].items():
        node_type = node_data.get("type", "unknown")
        style = node_styles.get(node_type, 'fillcolor="#FFFFFF"')
        label = node_id.replace("data/", "").replace("/", "_")
        lines.append(f'  "{node_id}" [label="{label}" {style}];')

    lines.append("")

    # Define edges
    for edge in dag["edges"]:
        lines.append(f'  "{edge["from"]}" -> "{edge["to"]}" [label="{edge["relation"]}"];')

    lines.append("}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def run_lineage_generation(config: Dict[str, Any]) -> Tuple[Path, Path]:
    """
    Main entry point to generate the data lineage artifacts.
    """
    project_root = Path(config.get("project_root", "."))
    state_file_path = project_root / "data" / "state.json"
    exclusion_log_path = project_root / "data" / "processed" / "exclusion_log.json"
    data_dir = project_root / "data"
    output_json_path = project_root / "data" / "processed" / "data_lineage.json"
    output_dot_path = project_root / "data" / "processed" / "data_lineage.dot"

    # Ensure output directory exists
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    # Load inputs
    try:
        state_data = load_state_file(state_file_path)
    except LineageError as e:
        # If state file is missing, we can still try to build a partial graph from raw sources
        state_data = {"artifacts": {}}
    
    exclusion_log = load_exclusion_log(exclusion_log_path)
    raw_sources = get_raw_trace_sources(data_dir)

    # Build DAG
    dag = build_dag(state_data, exclusion_log, raw_sources)

    # Save JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(dag, f, indent=2)

    # Generate DOT
    generate_dot_file(dag, output_dot_path)

    return output_json_path, output_dot_path

def main():
    """
    CLI entry point for lineage generation.
    """
    # Default config if not provided via env or args
    config = {
        "project_root": str(Path(__file__).parent.parent.parent)
    }

    try:
        json_path, dot_path = run_lineage_generation(config)
        print(f"Lineage JSON generated: {json_path}")
        print(f"Lineage DOT generated: {dot_path}")
    except Exception as e:
        print(f"Error generating lineage: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()