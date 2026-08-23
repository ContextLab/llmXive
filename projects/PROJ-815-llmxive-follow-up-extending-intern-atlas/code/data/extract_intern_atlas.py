"""
Extraction script for the Intern-Atlas graph.

Loads the graph, enforces human-annotation constraints, filters by year,
and exports the pre-filtered node list to CSV for downstream feature computation.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import Set, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from code.utils.graph_utils import load_graph_from_gml, abort_if_llm_inferred, filter_nodes_by_year
from code.utils.logging_config import setup_logger, get_env_config
from code.utils.constants import YEAR_RANGE

logger = setup_logger(__name__)

def extract_intern_atlas(
    input_gml: str,
    output_csv: str,
    min_year: int = YEAR_RANGE[0],
    max_year: int = YEAR_RANGE[1]
) -> int:
    """
    Load the Intern-Atlas graph, enforce human-annotation constraints,
    filter nodes by year, and save the resulting node list.
    
    Args:
        input_gml: Path to the input .gml file.
        output_csv: Path to the output .csv file for filtered nodes.
        min_year: Inclusive minimum year.
        max_year: Inclusive maximum year.
        
    Returns:
        Number of nodes extracted.
        
    Raises:
        SystemExit: If LLM-inferred edges are found or file errors occur.
    """
    logger.info(f"Starting extraction from {input_gml} for years {min_year}-{max_year}")
    
    # 1. Load Graph
    try:
        G = load_graph_from_gml(input_gml)
        logger.info(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    except FileNotFoundError as e:
        logger.error(f"Input graph file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load graph: {e}")
        raise

    # 2. Enforce Human-Annotated Constraint (FR-002)
    # This will call sys.exit(1) if LLM-inferred edges are detected.
    logger.info("Checking for LLM-inferred edges...")
    abort_if_llm_inferred(G)
    logger.info("Validation passed: No LLM-inferred edges found.")

    # 3. Filter Nodes by Year
    logger.info(f"Filtering nodes by year range [{min_year}, {max_year}]...")
    valid_nodes = filter_nodes_by_year(G, min_year, max_year)
    logger.info(f"Found {len(valid_nodes)} nodes in the specified time window.")

    if len(valid_nodes) == 0:
        logger.warning("No nodes found in the specified time window. Outputting empty file.")

    # 4. Extract Node Attributes and Write CSV
    # We include all available attributes to ensure downstream tasks have data.
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    nodes_data = []
    for node_id in valid_nodes:
        data = G.nodes[node_id]
        # Ensure node_id is included explicitly
        record = {"node_id": node_id}
        record.update(data)
        nodes_data.append(record)

    # Determine fieldnames dynamically from the first record or use defaults
    if nodes_data:
        fieldnames = list(nodes_data[0].keys())
    else:
        fieldnames = ["node_id"]

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nodes_data)
        logger.info(f"Successfully wrote {len(nodes_data)} nodes to {output_csv}")
    except Exception as e:
        logger.error(f"Failed to write output CSV: {e}")
        raise

    return len(nodes_data)

def main():
    """Entry point for the extraction script."""
    config = get_env_config()
    
    # Default paths based on project structure
    input_gml = os.environ.get("DATA_PATH", "data/raw/intern_atlas.gml")
    output_csv = "data/processed/nodes_2010_2018.csv"
    
    # Allow override via command line args or env
    if len(sys.argv) > 1:
        input_gml = sys.argv[1]
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]

    try:
        count = extract_intern_atlas(input_gml, output_csv)
        print(f"Extraction complete. {count} nodes written to {output_csv}")
    except SystemExit as e:
        # Re-raise exit codes from abort_if_llm_inferred
        raise
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()