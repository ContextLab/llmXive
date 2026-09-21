import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import networkx as nx

from config.env_config import get_processed_dir
from validation import load_validation_report
from graph_builder import build_graphs, run_sensitivity_analysis
from state_manager import register_artifact, compute_file_checksum, save_state
from logging_config import get_logger

logger = get_logger(__name__)

def save_graph_to_graphml(graph: nx.Graph, config_id: str, output_dir: Path) -> Path:
    """
    Save a single NetworkX graph to GraphML format.
    
    Args:
        graph: The NetworkX graph to save.
        config_id: The unique identifier for the configuration.
        output_dir: Directory where the file will be saved.
        
    Returns:
        Path to the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{config_id}.graphml"
    
    try:
        nx.write_graphml(graph, str(file_path))
        logger.info(f"Saved GraphML for {config_id} to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save GraphML for {config_id}: {e}")
        raise

def save_graph_to_json(graph: nx.Graph, config_id: str, output_dir: Path) -> Path:
    """
    Save a single NetworkX graph to JSON format (node-link data).
    
    Args:
        graph: The NetworkX graph to save.
        config_id: The unique identifier for the configuration.
        output_dir: Directory where the file will be saved.
        
    Returns:
        Path to the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{config_id}.json"
    
    try:
        # Convert graph to JSON-serializable format
        data = nx.node_link_data(graph)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON for {config_id} to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save JSON for {config_id}: {e}")
        raise

def save_graphs(validated_config_ids: List[str], output_dir: Path) -> Dict[str, Path]:
    """
    Save all constructed graphs for validated configurations to both GraphML and JSON formats.
    
    This function:
    1. Loads the validation report to get validated config IDs.
    2. Builds graphs for each validated configuration using the default cutoff radius.
    3. Saves each graph to both GraphML and JSON formats.
    4. Registers each output file in the state manager for provenance tracking.
    
    Args:
        validated_config_ids: List of configuration IDs that passed validation.
        output_dir: Directory where graph files will be saved.
        
    Returns:
        Dictionary mapping config_id to the path of the saved GraphML file.
    """
    if not validated_config_ids:
        logger.warning("No validated configurations found. Skipping graph saving.")
        return {}

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = {}
    
    # Build graphs for all validated configs
    # We use the default cutoff radius (2.8) for the primary graph save
    # as per the sensitivity analysis, 2.8 is the standard reference
    graphs = build_graphs(validated_config_ids, cutoff_radius=2.8)
    
    for config_id, graph in graphs.items():
        try:
            # Save to GraphML
            graphml_path = save_graph_to_graphml(graph, config_id, output_dir)
            
            # Save to JSON
            json_path = save_graph_to_json(graph, config_id, output_dir)
            
            # Register artifacts in state manager
            register_artifact(str(graphml_path), "graphml", config_id)
            register_artifact(str(json_path), "json", config_id)
            
            saved_files[config_id] = graphml_path
            
            logger.info(f"Successfully saved graphs for {config_id}")
            
        except Exception as e:
            logger.error(f"Error saving graphs for {config_id}: {e}")
            # Continue with other configs rather than failing the whole batch
            continue
    
    # Save state update
    save_state()
    
    return saved_files

def main():
    """
    Main entry point for saving constructed graphs.
    
    This function:
    1. Loads the validation report to get validated configuration IDs.
    2. Calls save_graphs to build and save graphs for all validated configs.
    3. Logs the number of successfully saved graphs.
    """
    logger.info("Starting graph saving process...")
    
    processed_dir = get_processed_dir()
    validation_report_path = processed_dir / "validation_report.json"
    graphs_dir = processed_dir / "graphs"
    
    if not validation_report_path.exists():
        logger.error(f"Validation report not found at {validation_report_path}.")
        logger.error("Please run the validation task (T007-exec) first.")
        return
    
    # Load validation report
    validation_report = load_validation_report(str(validation_report_path))
    validated_configs = validation_report.get("validated_configs", [])
    
    if not validated_configs:
        logger.warning("No validated configurations in the report. Nothing to save.")
        return
    
    logger.info(f"Found {len(validated_configs)} validated configurations.")
    
    # Save graphs
    saved_files = save_graphs(validated_configs, graphs_dir)
    
    logger.info(f"Graph saving complete. Successfully saved {len(saved_files)} graphs.")
    
    return saved_files

if __name__ == "__main__":
    main()
