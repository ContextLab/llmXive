import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import networkx as nx
from models.atomic_config import AtomicConfiguration
from logging_config import get_logger
from config.env_config import get_processed_dir

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    config_id: str
    is_valid: bool
    reason: Optional[str] = None
    flags: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

@dataclass
class ValidationReport:
    validated_configs: List[str] = field(default_factory=list)
    excluded_configs: List[str] = field(default_factory=list)
    convergence_flags: Dict[str, str] = field(default_factory=dict)
    component_warnings: List[Dict[str, Any]] = field(default_factory=list)

def validate_graph_connectivity(graph: nx.Graph, config_id: str) -> Tuple[bool, List[str]]:
    """
    Validates that the graph derived from an atomic configuration is connected.
    
    Args:
        graph: The networkx graph representing atomic bonds.
        config_id: The identifier for the configuration.
        
    Returns:
        Tuple of (is_connected, list_of_warnings)
    """
    warnings = []
    is_connected = nx.is_connected(graph)
    
    if not is_connected:
        num_components = nx.number_connected_components(graph)
        component_sizes = sorted([len(c) for c in nx.connected_components(graph)], reverse=True)
        
        warning_msg = (
            f"Configuration {config_id} has {num_components} disconnected components. "
            f"Largest component size: {component_sizes[0]}, "
            f"Smallest component size: {component_sizes[-1]}. "
            f"Total nodes: {graph.number_of_nodes()}."
        )
        warnings.append(warning_msg)
        logger.warning(warning_msg)
        
        # Log details about the components for debugging
        logger.debug(f"Component sizes for {config_id}: {component_sizes}")
        
    return is_connected, warnings

def validate_configuration(config: AtomicConfiguration, graph: nx.Graph) -> ValidationResult:
    """
    Performs validation checks on a single configuration and its graph.
    
    Args:
        config: The atomic configuration object.
        graph: The graph representation of the configuration.
        
    Returns:
        ValidationResult object containing validation status and details.
    """
    result = ValidationResult(config_id=config.id, is_valid=True)
    
    # Check system size (>= 1000 atoms)
    if len(config.coordinates) < 1000:
        result.flags["size"] = "P preliminary - Unverified Convergence"
        # We retain it for descriptive stats but flag it
        result.warnings.append(
            f"Configuration {config.id} has {len(config.coordinates)} atoms (< 1000). "
            "Flagged as preliminary."
        )
    
    # Check graph connectivity (US-1, Scenario 3)
    is_connected, connectivity_warnings = validate_graph_connectivity(graph, config.id)
    result.warnings.extend(connectivity_warnings)
    
    if not is_connected:
        result.is_valid = False
        result.reason = "Disconnected components detected"
        result.flags["connectivity"] = "DISCONNECTED"
    
    return result

def run_validation_on_configs(
    configs: List[AtomicConfiguration], 
    graphs: Dict[str, nx.Graph]
) -> ValidationReport:
    """
    Runs validation on a list of configurations using their corresponding graphs.
    
    Args:
        configs: List of AtomicConfiguration objects.
        graphs: Dictionary mapping config_id to networkx Graph.
        
    Returns:
        ValidationReport containing aggregated results.
    """
    report = ValidationReport()
    
    for config in configs:
        if config.id not in graphs:
            logger.error(f"Graph not found for config {config.id}, skipping validation.")
            report.excluded_configs.append(config.id)
            continue
        
        graph = graphs[config.id]
        result = validate_configuration(config, graph)
        
        if result.is_valid:
            report.validated_configs.append(config.id)
            # Merge flags
            report.convergence_flags[config.id] = result.flags.get("size", "OK")
        else:
            # If disconnected, we might still want to flag it but exclude from main analysis
            # depending on strictness. For now, we exclude disconnected ones from 'validated'.
            report.excluded_configs.append(config.id)
            report.convergence_flags[config.id] = result.reason
        
        # Record warnings specifically about components
        if result.flags.get("connectivity") == "DISCONNECTED":
            report.component_warnings.append({
                "config_id": config.id,
                "message": result.reason,
                "details": result.warnings
            })
    
    return report

def save_validation_report(report: ValidationReport, output_path: Optional[Path] = None) -> Path:
    """
    Saves the validation report to a JSON file.
    
    Args:
        report: The ValidationReport object to save.
        output_path: Optional path to save the report. Defaults to data/processed/validation_report.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        processed_dir = get_processed_dir()
        output_path = processed_dir / "validation_report.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "validated_configs": report.validated_configs,
        "excluded_configs": report.excluded_configs,
        "convergence_flags": report.convergence_flags,
        "component_warnings": report.component_warnings
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path

def load_validation_report(file_path: Path) -> ValidationReport:
    """
    Loads a validation report from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        ValidationReport object.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return ValidationReport(
        validated_configs=data.get("validated_configs", []),
        excluded_configs=data.get("excluded_configs", []),
        convergence_flags=data.get("convergence_flags", {}),
        component_warnings=data.get("component_warnings", [])
    )

def check_validation_logic() -> bool:
    """
    Basic sanity check that the validation logic functions are callable.
    
    Returns:
        True if logic is intact, False otherwise.
    """
    try:
        # Mock test data
        from models.atomic_config import AtomicConfiguration
        import numpy as np
        
        # Create a small mock config
        mock_coords = np.random.rand(100, 3)
        mock_config = AtomicConfiguration(
            id="test_001",
            element="Si",
            coordinates=mock_coords,
            box=np.eye(3) * 10
        )
        
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from(range(100))
        G.add_edges_from([(i, i+1) for i in range(0, 50)]) # First component
        G.add_edges_from([(i, i+1) for i in range(51, 99)]) # Second component
        # Node 50 is isolated or part of a gap
        
        is_conn, warns = validate_graph_connectivity(G, "test_001")
        if is_conn:
            logger.error("Mock disconnected graph was incorrectly identified as connected.")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Validation logic check failed: {e}")
        return False

def main():
    """
    Main entry point for running validation if executed as a script.
    This function assumes configs and graphs are already loaded or passed via arguments.
    For now, it serves as a placeholder for the execution flow.
    """
    logger.info("Validation module loaded. Use run_validation_on_configs with data.")
    if not check_validation_logic():
        logger.error("Validation logic check failed.")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())