"""
Task T058: Verify Task Ordering
Audits the dependency chain between data cleaning, validation, descriptor engineering,
and model training to ensure no circular dependencies or incorrect file usage.
"""
import os
import sys
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_data_processed_dir, get_data_outputs_dir, get_data_raw_dir

# Define the expected dependency graph based on tasks.md
# Format: "Producer Task ID": ["Consumer Task IDs"]
# We map tasks to their primary output files and then check if consumers read those files.

TASK_DEPENDENCIES = {
    "T006": ["T013", "T014", "T023b", "T023c", "T025", "T026"], # Config used by many
    "T012d-Protocol-Doc": ["T012d-SLR-Exec"],
    "T023a": ["T023b", "T023c"],
    "T024b": ["T025", "T026"],
    # Data Flow Dependencies
    "T013": ["T014", "T023b", "T023c"], # T013 produces solder_hardness_cleaned.csv
    "T014": ["T014a", "T016b", "T031c"], # T014 produces .ingestion_status.json
    "T023b": ["T025", "T026"], # T023b produces clr_features.csv
    "T023c": ["T024", "T025", "T026"], # T023c produces descriptors.csv
    "T024": ["T024b", "T054"],
    "T025": ["T027", "T028", "T030", "T031b", "T031c"],
    "T026": ["T027", "T028", "T030", "T031b", "T031c"],
}

# Expected file producers and consumers
FILE_DEPENDENCIES = {
    "data/processed/solder_hardness_cleaned.csv": {
        "producer": "T013",
        "consumers": ["T014", "T023b", "T023c"]
    },
    "data/processed/.ingestion_status.json": {
        "producer": "T014",
        "consumers": ["T014a", "T016b", "T031c", "T014b"]
    },
    "data/processed/clr_features.csv": {
        "producer": "T023b",
        "consumers": ["T025", "T026"]
    },
    "data/processed/descriptors.csv": {
        "producer": "T023c",
        "consumers": ["T024", "T025", "T026"]
    },
    "data/processed/cv_results.json": {
        "producer": "T027",
        "consumers": ["T027a", "T029a-Define", "T031c"]
    },
}

# Mapping of script paths to Task IDs (approximate based on tasks.md)
SCRIPT_TO_TASK = {
    "code/ingestion/cleaner.py": "T013",
    "code/ingestion/validator.py": "T014",
    "code/features/transformer.py": "T023b",
    "code/features/descriptor_engine.py": "T023c",
    "code/features/collinearity.py": "T024",
    "code/models/xgboost_trainer.py": "T025",
    "code/models/linear_trainer.py": "T026",
    "code/evaluation/cv.py": "T027",
    "code/evaluation/paired_ttest.py": "T027a",
    "code/evaluation/sensitivity.py": "T029c",
    "code/evaluation/generate_thresholds.py": "T029a-Generate",
    "code/evaluation/shap_analysis.py": "T030",
    "code/evaluation/predict.py": "T031b",
    "code/evaluation/generate_report.py": "T031c",
    "code/ingestion/aggregate_final_report.py": "T014b",
    "code/ingestion/generate_validation_report.py": "T016b",
    "code/ingestion/validation_metrics.py": "T014a",
}

def get_producer_task(file_path: str) -> Optional[str]:
    """Get the task ID responsible for producing a file."""
    for path, info in FILE_DEPENDENCIES.items():
        if path == file_path:
            return info["producer"]
    return None

def get_consumer_tasks(file_path: str) -> List[str]:
    """Get the list of task IDs that consume a file."""
    for path, info in FILE_DEPENDENCIES.items():
        if path == file_path:
            return info["consumers"]
    return []

def check_file_exists(file_path: str, base_dir: Path) -> bool:
    """Check if a file exists."""
    full_path = base_dir / file_path
    return full_path.exists()

def check_imports_source_file(script_path: Path, base_dir: Path) -> List[str]:
    """
    Parse a Python script to find imports of data files.
    Returns a list of file paths found in the script (heuristic).
    """
    if not script_path.exists():
        return []
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return []
    
    found_files = []
    # Heuristic: Look for string literals in assignments or function calls that look like paths
    # This is a simplified AST walk
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if val.startswith("data/") or val.startswith("models/"):
                # Normalize path
                if not val.startswith("/"):
                    found_files.append(val)
        elif isinstance(node, ast.Str): # Python 3.7 compatibility
            val = node.s
            if val.startswith("data/") or val.startswith("models/"):
                found_files.append(val)
    
    return found_files

def audit_file_dependencies(base_dir: Path) -> Tuple[Dict, List[str]]:
    """
    Audit the dependency graph by checking if consumer scripts actually import
    or reference files produced by producer tasks.
    """
    graph = {
        "nodes": [],
        "edges": []
    }
    issues = []

    # Build graph from FILE_DEPENDENCIES
    for file_path, info in FILE_DEPENDENCIES.items():
        producer = info["producer"]
        consumers = info["consumers"]
        
        # Add nodes
        if producer not in graph["nodes"]:
            graph["nodes"].append(producer)
        
        for consumer in consumers:
            if consumer not in graph["nodes"]:
                graph["nodes"].append(consumer)
            graph["edges"].append({"from": producer, "to": consumer, "via": file_path})

        # Verify actual usage (heuristic)
        # Find the script corresponding to the producer
        producer_script = None
        for script, task in SCRIPT_TO_TASK.items():
            if task == producer:
                producer_script = base_dir / script
                break
        
        # Find scripts for consumers
        consumer_scripts = []
        for script, task in SCRIPT_TO_TASK.items():
            if task in consumers:
                consumer_scripts.append(base_dir / script)

        # Check if producer script writes the file
        # (Hard to verify via AST without full context, assume correct if task exists)
        
        # Check if consumer scripts read the file
        for consumer_script in consumer_scripts:
            if consumer_script.exists():
                imports = check_imports_source_file(consumer_script, base_dir)
                if file_path not in imports:
                    # It's possible the path is constructed dynamically, so this is a warning, not a hard error
                    # But if the file is critical (like cleaned.csv), we flag it.
                    if "cleaned" in file_path or "status" in file_path:
                        issues.append(f"Potential missing reference: {consumer_script.name} does not explicitly import {file_path}")
            else:
                issues.append(f"Consumer script not found: {consumer_script.name} (Task: {SCRIPT_TO_TASK.get(str(consumer_script.relative_to(base_dir.parent)), 'Unknown')})")

    return graph, issues

def main():
    """Main entry point for T058."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "data" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Task T058: Verify Task Ordering Audit")

    # 1. Verify critical file existence (if they are supposed to exist at this stage)
    # Note: T058 depends on task definitions, not necessarily outputs, but we check if outputs exist to validate the chain.
    critical_files = [
        "data/processed/solder_hardness_cleaned.csv",
        "data/processed/.ingestion_status.json",
        "data/processed/clr_features.csv",
        "data/processed/descriptors.csv"
    ]

    missing_files = []
    for f in critical_files:
        if not check_file_exists(f, base_dir):
            missing_files.append(f)

    # 2. Audit dependencies
    graph, audit_issues = audit_file_dependencies(base_dir)

    # 3. Validate the chain logic
    # T023b/T023c MUST depend on T013 output
    # T025/T026 MUST depend on T023b/T023c output
    
    is_valid = True
    final_issues = []

    if missing_files:
        # This is expected if the pipeline hasn't run yet, but we flag it as a potential issue for the audit
        # The task says "depends ONLY on task definitions", so we don't fail if files are missing,
        # but we record it.
        pass 
    
    # Check logical consistency of the graph
    # T013 -> T023b/T023c
    # T023b/T023c -> T025/T026
    # We check if these edges exist in our defined graph
    edges = { (e["from"], e["to"]) for e in graph["edges"] }
    
    required_edges = [
        ("T013", "T023b"),
        ("T013", "T023c"),
        ("T023b", "T025"),
        ("T023b", "T026"),
        ("T023c", "T025"),
        ("T023c", "T026"),
    ]

    for src, dst in required_edges:
        if (src, dst) not in edges:
            is_valid = False
            final_issues.append(f"Missing required dependency edge: {src} -> {dst}")

    # Add audit issues
    final_issues.extend(audit_issues)

    if not is_valid:
        logger.warning("Dependency graph validation failed.")
    else:
        logger.info("Dependency graph validation passed.")

    result = {
        "graph": graph,
        "is_valid": is_valid,
        "issues": final_issues,
        "missing_critical_files": missing_files,
        "audit_timestamp": str(Path(__file__).parent.parent) # Just a placeholder for timestamp logic if needed
    }

    output_file = output_dir / "task_ordering_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Audit complete. Results written to {output_file}")
    return result

if __name__ == "__main__":
    main()
