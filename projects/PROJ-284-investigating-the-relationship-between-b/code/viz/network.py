"""
Network diagram generator for brain connectivity analysis.

Generates publication-quality network diagrams showing:
- Nodes colored by module/community
- Edges filtered by statistical significance
- Edge width proportional to correlation strength
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# Import from project logging
from code.logging_config import get_logger

logger = get_logger(__name__)


def load_schaefer_mapping(atlas_path: Optional[str] = None) -> Dict[int, str]:
    """
    Load Schaefer atlas module/parcellation mapping.
    
    Args:
        atlas_path: Path to atlas mapping file. If None, uses default location.
        
    Returns:
        Dictionary mapping node index (int) to module name (str).
    """
    if atlas_path is None:
        # Default path relative to project root
        atlas_path = "data/processed/schaefer_400_mapping.csv"
    
    path = Path(atlas_path)
    
    if not path.exists():
        logger.log("load_schaefer_mapping_warning", 
                  message=f"Atlas mapping file not found at {atlas_path}. "
                         "Using default module assignment.")
        # Return a deterministic default mapping based on node index
        # Schaefer 400 atlas has 7 networks (Yeo 7)
        default_mapping = {}
        for i in range(400):
            # Simple round-robin assignment for visualization purposes
            network_idx = i % 7
            networks = ['Vis', 'SomMot', 'DorsAttn', 'SalVent', 'Limbic', 'Cont', 'Default']
            default_mapping[i] = networks[network_idx]
        return default_mapping
    
    try:
        df = pd.read_csv(path)
        # Expected columns: node_id, network (or similar)
        mapping = {}
        for _, row in df.iterrows():
            node_id = int(row['node_id'])
            network = str(row['network'])
            mapping[node_id] = network
        return mapping
    except Exception as e:
        logger.log("load_schaefer_mapping_error", error=str(e))
        # Fallback to default
        return {i: f"Net_{i % 7}" for i in range(400)}


def load_correlation_results(
    corr_path: str = "data/analysis/correlations.csv",
    significant_threshold: float = 0.05
) -> Tuple[pd.DataFrame, List[int]]:
    """
    Load correlation results and identify significant edges.
    
    Args:
        corr_path: Path to correlation results CSV.
        significant_threshold: FDR-corrected q-value threshold.
        
    Returns:
        Tuple of (correlation DataFrame, list of significant edge indices).
    """
    path = Path(corr_path)
    
    if not path.exists():
        logger.log("load_correlation_results_error", 
                  message=f"Correlation results file not found at {corr_path}")
        # Return empty results
        return pd.DataFrame(), []
    
    try:
        df = pd.read_csv(corr_path)
        
        # Identify significant edges (q < threshold)
        if 'q' in df.columns:
            significant_mask = df['q'] < significant_threshold
            significant_edges = df[significant_mask]
        elif 'p' in df.columns:
            # Fallback to uncorrected p if q not available
            significant_mask = df['p'] < significant_threshold
            significant_edges = df[significant_mask]
        else:
            logger.log("load_correlation_results_warning", 
                      message="No p or q column found in correlation results")
            return df, []
        
        return df, significant_edges
    except Exception as e:
        logger.log("load_correlation_results_error", error=str(e))
        return pd.DataFrame(), []


def get_significant_edges(
    correlation_df: pd.DataFrame,
    atlas_mapping: Dict[int, str],
    corr_col: str = 'r',
    q_col: str = 'q',
    threshold: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Extract significant edges with node and network information.
    
    Args:
        correlation_df: DataFrame with correlation results.
        atlas_mapping: Node to network mapping.
        corr_col: Column name for correlation coefficient.
        q_col: Column name for FDR-corrected q-value.
        threshold: Significance threshold.
        
    Returns:
        List of edge dictionaries with node indices, networks, and correlation values.
    """
    edges = []
    
    if correlation_df.empty:
        return edges
    
    # Filter significant edges
    if q_col in correlation_df.columns:
        sig_df = correlation_df[correlation_df[q_col] < threshold]
    else:
        sig_df = correlation_df  # No filtering if no q column
    
    for _, row in sig_df.iterrows():
        # Determine node indices based on data structure
        # Assuming columns like 'node_1', 'node_2' or similar
        if 'node_1' in row.index and 'node_2' in row.index:
            node_1 = int(row['node_1'])
            node_2 = int(row['node_2'])
        elif 'from_node' in row.index and 'to_node' in row.index:
            node_1 = int(row['from_node'])
            node_2 = int(row['to_node'])
        else:
            # Try to infer from column names or skip
            continue
        
        # Get network assignments
        net_1 = atlas_mapping.get(node_1, "Unknown")
        net_2 = atlas_mapping.get(node_2, "Unknown")
        
        edges.append({
            'node_1': node_1,
            'node_2': node_2,
            'network_1': net_1,
            'network_2': net_2,
            'correlation': float(row[corr_col]) if corr_col in row else 0.0,
            'q_value': float(row[q_col]) if q_col in row else 1.0
        })
    
    return edges


def generate_network_diagram(
    edges: List[Dict[str, Any]],
    atlas_mapping: Dict[int, str],
    output_path: str = "figures/network_diagram.png",
    node_size: int = 50,
    edge_width_scale: float = 5.0,
    title: str = "Significant Functional Connectivity Network"
) -> str:
    """
    Generate a network diagram visualization.
    
    Args:
        edges: List of significant edge dictionaries.
        atlas_mapping: Node to network mapping.
        output_path: Path to save the output figure.
        node_size: Size of nodes in the plot.
        edge_width_scale: Multiplier for edge width based on correlation strength.
        title: Plot title.
        
    Returns:
        Path to the saved figure.
    """
    if not edges:
        logger.log("generate_network_diagram_warning", 
                  message="No edges provided for network diagram. "
                         "Creating empty placeholder.")
        # Create a minimal placeholder figure
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, 'No Significant Edges', 
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title)
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Build NetworkX graph
    G = nx.Graph()
    
    # Collect unique nodes
    nodes = set()
    for edge in edges:
        nodes.add(edge['node_1'])
        nodes.add(edge['node_2'])
    
    # Add nodes with network attributes
    node_colors = []
    network_list = sorted(list(set(atlas_mapping.get(n, "Unknown") for n in nodes)))
    network_to_idx = {net: i for i, net in enumerate(network_list)}
    
    for node in nodes:
        G.add_node(node)
        net = atlas_mapping.get(node, "Unknown")
        node_colors.append(network_to_idx.get(net, 0))
    
    # Add edges with weight
    for edge in edges:
        weight = abs(edge['correlation'])
        G.add_edge(edge['node_1'], edge['node_2'], weight=weight)
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Draw nodes
    cmap = plt.get_cmap('tab10')
    node_color_list = [cmap(c % 10) for c in node_colors]
    
    nx.draw_networkx_nodes(
        G, pos, 
        node_color=node_color_list, 
        node_size=node_size,
        alpha=0.8
    )
    
    # Draw edges
    edge_widths = [abs(e['correlation']) * edge_width_scale for e in edges]
    edge_colors = ['red' if e['correlation'] > 0 else 'blue' for e in edges]
    
    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        edge_color=edge_colors,
        alpha=0.5
    )
    
    # Create legend
    # Node legend (networks)
    legend_handles = []
    for net in network_list:
        idx = network_to_idx[net]
        legend_handles.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=cmap(idx % 10), markersize=8,
                      label=net)
        )
    
    # Edge legend (positive/negative)
    legend_handles.append(
        plt.Line2D([0], [0], color='red', linewidth=2, label='Positive')
    )
    legend_handles.append(
        plt.Line2D([0], [0], color='blue', linewidth=2, label='Negative')
    )
    
    # Draw labels (optional, only for a subset to avoid clutter)
    # Show labels for nodes with high degree
    degrees = dict(G.degree())
    high_degree_nodes = [n for n, d in degrees.items() if d >= np.median(list(degrees.values())) + 1]
    
    if len(high_degree_nodes) <= 20:
        nx.draw_networkx_labels(G, pos, {n: str(n) for n in high_degree_nodes}, font_size=8)
    
    plt.title(title, fontsize=14, pad=20)
    plt.legend(handles=legend_handles, loc='upper right', fontsize=10)
    plt.axis('off')
    plt.tight_layout()
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.log("generate_network_diagram_success", 
              message=f"Network diagram saved to {output_path}",
              num_edges=len(edges),
              num_nodes=len(nodes))
    
    return output_path


def main(
    corr_path: str = "data/analysis/correlations.csv",
    atlas_path: Optional[str] = None,
    output_path: str = "figures/network_diagram.png",
    threshold: float = 0.05
) -> str:
    """
    Main entry point for generating network diagrams.
    
    Args:
        corr_path: Path to correlation results CSV.
        atlas_path: Path to Schaefer atlas mapping.
        output_path: Path to save the output figure.
        threshold: FDR significance threshold.
        
    Returns:
        Path to the saved figure.
    """
    logger.log("network_diagram_start", 
              message="Starting network diagram generation",
              corr_path=corr_path,
              output_path=output_path)
    
    # Load data
    atlas_mapping = load_schaefer_mapping(atlas_path)
    correlation_df, _ = load_correlation_results(corr_path, threshold)
    
    # Extract significant edges
    edges = get_significant_edges(correlation_df, atlas_mapping, threshold=threshold)
    
    # Generate diagram
    output = generate_network_diagram(edges, atlas_mapping, output_path)
    
    logger.log("network_diagram_complete", message="Network diagram generation finished")
    return output


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate network diagram from correlation results")
    parser.add_argument("--corr_path", type=str, default="data/analysis/correlations.csv",
                      help="Path to correlation results CSV")
    parser.add_argument("--atlas_path", type=str, default=None,
                      help="Path to Schaefer atlas mapping")
    parser.add_argument("--output_path", type=str, default="figures/network_diagram.png",
                      help="Output path for the figure")
    parser.add_argument("--threshold", type=float, default=0.05,
                      help="FDR significance threshold")
    
    args = parser.parse_args()
    
    result = main(
        corr_path=args.corr_path,
        atlas_path=args.atlas_path,
        output_path=args.output_path,
        threshold=args.threshold
    )
    print(f"Network diagram generated: {result}")