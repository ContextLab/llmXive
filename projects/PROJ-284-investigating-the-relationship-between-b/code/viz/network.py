"""
Network Diagram Generator for Brain Connectivity Analysis.

Generates publication-quality network diagrams showing:
- Module-based node coloring (Schaefer atlas communities)
- Significant edges (based on correlation results)
- Node coordinates (from atlas metadata)

Output: PNG files in figures/network_diagrams/
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
FIGURES_DIR = Path("figures/network_diagrams")
SCHAEFER_MAPPING_PATH = Path("data/analysis/schaefer_mapping.json")
CORRELATION_RESULTS_PATH = Path("data/analysis/correlations.csv")

def load_schaefer_mapping(mapping_path: Optional[Path] = None) -> Dict[int, Dict[str, Any]]:
    """
    Load Schaefer atlas module mapping.
    
    Args:
        mapping_path: Path to JSON file with node-to-module mapping.
                    If None, uses default path.
                    
    Returns:
        Dictionary mapping node_id -> {module, color, name, x, y, z}
        
    Raises:
        FileNotFoundError: If mapping file doesn't exist.
    """
    if mapping_path is None:
        mapping_path = SCHAEFER_MAPPING_PATH
        
    if not mapping_path.exists():
        logger.log("schema_missing", path=str(mapping_path))
        raise FileNotFoundError(f"Schaefer mapping not found at {mapping_path}")
        
    with open(mapping_path, 'r') as f:
        data = json.load(f)
        
    # Convert string keys to int
    mapping = {}
    for key, value in data.items():
        mapping[int(key)] = value
        
    logger.log("schema_loaded", path=str(mapping_path), nodes=len(mapping))
    return mapping

def load_correlation_results(results_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load correlation results with FDR correction.
    
    Args:
        results_path: Path to CSV with correlation results.
                    If None, uses default path.
                    
    Returns:
        DataFrame with columns: metric_name, correlation_target, r, p, q, significant
        
    Raises:
        FileNotFoundError: If results file doesn't exist.
    """
    if results_path is None:
        results_path = CORRELATION_RESULTS_PATH
        
    if not results_path.exists():
        logger.log("results_missing", path=str(results_path))
        raise FileNotFoundError(f"Correlation results not found at {results_path}")
        
    df = pd.read_csv(results_path)
    logger.log("results_loaded", path=str(results_path), rows=len(df))
    return df

def get_significant_edges(
    correlation_results: pd.DataFrame,
    metrics: List[str],
    target: str = "motor_score"
) -> Dict[str, List[Tuple[int, int, float]]]:
    """
    Extract significant edges for each metric.
    
    Args:
        correlation_results: DataFrame with correlation results.
        metrics: List of metric names to extract edges for.
        target: Target variable name (default: motor_score).
        
    Returns:
        Dictionary mapping metric_name -> list of (node1, node2, r_value)
        where r_value is the correlation coefficient.
    """
    significant_edges = {}
    
    for metric in metrics:
        # Filter for significant correlations with this metric
        metric_rows = correlation_results[
            (correlation_results['metric_name'] == metric) &
            (correlation_results['significant'] == True)
        ]
        
        edges = []
        for _, row in metric_rows.iterrows():
            # Extract node indices from metric_name format: "participation_coef_node_X"
            # or "within_module_degree_node_X"
            node_str = row['metric_name'].split('_node_')[-1] if '_node_' in row['metric_name'] else None
            
            if node_str:
                try:
                    node_id = int(node_str)
                    edges.append((node_id, node_id, row['r']))
                except ValueError:
                    continue
        
        if edges:
            significant_edges[metric] = edges
            logger.log("edges_extracted", metric=metric, count=len(edges))
    
    return significant_edges

def load_node_coordinates(mapping: Dict[int, Dict[str, Any]]) -> Dict[int, Tuple[float, float, float]]:
    """
    Extract 3D coordinates from Schaefer mapping.
    
    Args:
        mapping: Node-to-module mapping from load_schaefer_mapping.
                
    Returns:
        Dictionary mapping node_id -> (x, y, z) coordinates.
    """
    coords = {}
    for node_id, info in mapping.items():
        if 'x' in info and 'y' in info and 'z' in info:
            coords[node_id] = (info['x'], info['y'], info['z'])
    
    logger.log("coordinates_loaded", count=len(coords))
    return coords

def generate_network_diagram(
    significant_edges: Dict[str, List[Tuple[int, int, float]]],
    mapping: Dict[int, Dict[str, Any]],
    output_path: Optional[Path] = None,
    edge_threshold: float = 0.3
) -> Path:
    """
    Generate a network diagram with module coloring and significant edges.
    
    Args:
        significant_edges: Dictionary of metric -> list of edges.
        mapping: Node-to-module mapping with coordinates.
        output_path: Path to save the figure. If None, uses default.
        edge_threshold: Minimum |r| value to display edges.
        
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        output_path = FIGURES_DIR / "network_diagram.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create figure
    fig = plt.figure(figsize=(14, 12))
    ax = fig.add_subplot(111)
    
    # Get all nodes and their modules
    nodes = list(mapping.keys())
    modules = set(info.get('module', 0) for info in mapping.values())
    
    # Define module colors (distinct colors for each module)
    module_colors = plt.cm.tab10.colors
    node_colors = [module_colors[mapping[n].get('module', 0) % 10] for n in nodes]
    
    # Extract coordinates
    coords = [mapping[n].get('x', 0) for n in nodes], \
             [mapping[n].get('y', 0) for n in nodes], \
             [mapping[n].get('z', 0) for n in nodes]
    
    # Project to 2D for visualization (simple orthographic projection)
    # Rotate to view from a good angle
    theta = np.pi / 4
    x_proj = [coords[0][i] * np.cos(theta) - coords[2][i] * np.sin(theta) for i in range(len(nodes))]
    y_proj = [coords[1][i] for i in range(len(nodes))]
    
    # Plot nodes
    scatter = ax.scatter(x_proj, y_proj, c=node_colors, s=50, alpha=0.7, edgecolors='black', linewidths=0.5)
    
    # Create legend for modules
    legend_patches = []
    for mod in sorted(modules):
        legend_patches.append(
            mpatches.Patch(color=module_colors[mod % 10], label=f'Module {mod}')
        )
    ax.legend(handles=legend_patches, loc='upper right', title='Modules')
    
    # Plot edges for each metric
    for metric, edges in significant_edges.items():
        # Filter edges by threshold
        filtered_edges = [(n1, n2, r) for n1, n2, r in edges if abs(r) >= edge_threshold]
        
        if not filtered_edges:
            continue
        
        # Create line collection
        line_segments = []
        colors = []
        for n1, n2, r in filtered_edges:
            if n1 in mapping and n2 in mapping:
                # Get projected coordinates
                x1 = mapping[n1].get('x', 0) * np.cos(theta) - mapping[n1].get('z', 0) * np.sin(theta)
                y1 = mapping[n1].get('y', 0)
                x2 = mapping[n2].get('x', 0) * np.cos(theta) - mapping[n2].get('z', 0) * np.sin(theta)
                y2 = mapping[n2].get('y', 0)
                
                line_segments.append([[x1, y1], [x2, y2]])
                
                # Color based on correlation strength
                if r > 0:
                    colors.append((1, 0, 0, min(1.0, abs(r))))  # Red for positive
                else:
                    colors.append((0, 0, 1, min(1.0, abs(r))))  # Blue for negative
        
        if line_segments:
          lc = LineCollection(line_segments, colors=colors, linewidths=1.5, alpha=0.6)
          ax.add_collection(lc)
    
    # Add legend for edges
    pos_patch = mpatches.Patch(color='red', label='Positive correlation')
    neg_patch = mpatches.Patch(color='blue', label='Negative correlation')
    ax.legend(handles=[pos_patch, neg_patch], loc='lower right', title='Edge Sign')
    
    ax.set_title('Brain Network Dynamics: Significant Correlations with Motor Performance\n'
                f'(Threshold |r| >= {edge_threshold})', fontsize=14, fontweight='bold')
    ax.set_xlabel('X (projected)', fontsize=12)
    ax.set_ylabel('Y', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.log("diagram_generated", path=str(output_path), metrics=len(significant_edges))
    return output_path

def main() -> None:
    """
    Main entry point for network diagram generation.
    
    Loads correlation results, extracts significant edges,
    and generates the network diagram.
    """
    try:
        # Load data
        logger.log("network_diagram_start")
        
        # Load Schaefer mapping
        mapping = load_schaefer_mapping()
        
        # Load correlation results
        correlation_results = load_correlation_results()
        
        # Define metrics to visualize
        # These should match the metrics extracted in T021/T022
        metrics = [
            'participation_coef',
            'within_module_degree',
            'modularity',
            'global_efficiency'
        ]
        
        # Extract significant edges
        significant_edges = get_significant_edges(correlation_results, metrics)
        
        if not significant_edges:
            logger.log("no_significant_edges", message="No significant edges found to visualize")
            # Create a placeholder figure
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No significant edges found\n(r > 0.3, q < 0.05)', 
                   ha='center', va='center', fontsize=14, transform=ax.transAxes)
            ax.set_title('Network Diagram - No Significant Edges')
            FIGURES_DIR.mkdir(parents=True, exist_ok=True)
            output_path = FIGURES_DIR / "network_diagram.png"
            plt.savefig(output_path, dpi=300)
            plt.close(fig)
            logger.log("placeholder_generated", path=str(output_path))
            return
        
        # Generate diagram
        output_path = generate_network_diagram(significant_edges, mapping)
        
        logger.log("network_diagram_complete", path=str(output_path))
        print(f"Network diagram saved to: {output_path}")
        
    except FileNotFoundError as e:
        logger.log("network_diagram_failed", error=str(e))
        raise
    except Exception as e:
        logger.log("network_diagram_error", error=str(e))
        raise