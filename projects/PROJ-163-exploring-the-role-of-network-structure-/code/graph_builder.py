import logging
import networkx as nx
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from scipy.sparse.csgraph import laplacian
from models import QubitDevice, GraphMetric

logger = logging.getLogger(__name__)

def build_coupling_graph(coupling_map: List[List[int]], num_qubits: int) -> nx.Graph:
    """
    Construct an undirected NetworkX graph from a coupling map.

    Args:
        coupling_map: List of [qubit_a, qubit_b] pairs representing directed edges.
        num_qubits: Total number of qubits in the device.

    Returns:
        An undirected NetworkX graph representing the connectivity.
    """
    G = nx.Graph()
    # Add all qubits as nodes, even if isolated
    G.add_nodes(range(num_qubits))
    
    # Convert directed edges to undirected edges
    for edge in coupling_map:
        if len(edge) == 2:
            u, v = edge
            G.add_edge(u, v)
    
    return G

def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest path length and graph diameter.
    
    Handles disconnected graphs by computing metrics only on the largest connected component.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary with 'avg_shortest_path' and 'diameter'.
        If the graph is disconnected, returns 0.0 for diameter and computes average
        shortest path only for the largest component.
    """
    if G.number_of_nodes() == 0:
        return {"avg_shortest_path": 0.0, "diameter": 0.0}
    
    # Check connectivity
    if not nx.is_connected(G):
        logger.warning("Graph is disconnected. Computing metrics on the largest component.")
        # Get largest connected component
        components = list(nx.connected_components(G))
        largest_component = max(components, key=len)
        G_connected = G.subgraph(largest_component)
        
        if G_connected.number_of_nodes() < 2:
            return {"avg_shortest_path": 0.0, "diameter": 0.0}
        
        avg_sp = nx.average_shortest_path_length(G_connected)
        diameter = nx.diameter(G_connected)
    else:
        if G.number_of_nodes() < 2:
            return {"avg_shortest_path": 0.0, "diameter": 0.0}
        avg_sp = nx.average_shortest_path_length(G)
        diameter = nx.diameter(G)
    
    return {"avg_shortest_path": float(avg_sp), "diameter": float(diameter)}

def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary with 'clustering_coefficient' and 'assortativity'.
    """
    if G.number_of_nodes() == 0:
        return {"clustering_coefficient": 0.0, "assortativity": 0.0}
    
    clustering = nx.clustering_coefficient(G)
    
    # Assortativity might fail for graphs with degree 0 or specific structures
    try:
        assortativity = nx.degree_assortativity(G)
    except nx.NetworkXError:
        logger.warning("Could not compute degree assortativity. Setting to 0.0.")
        assortativity = 0.0
    
    return {"clustering_coefficient": float(clustering), "assortativity": float(assortativity)}

def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, Any]:
    """
    Compute edge betweenness centrality distribution and the spectral gap of the Laplacian.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary containing:
            - 'edge_betweenness_mean': Mean of edge betweenness centrality.
            - 'edge_betweenness_std': Standard deviation of edge betweenness centrality.
            - 'spectral_gap': The difference between the two smallest eigenvalues of the 
                              Laplacian matrix (algebraic connectivity).
    """
    result = {
        "edge_betweenness_mean": 0.0,
        "edge_betweenness_std": 0.0,
        "spectral_gap": 0.0
    }
    
    # Edge Betweenness Centrality
    if G.number_of_edges() > 0:
        try:
            betweenness = nx.edge_betweenness_centrality(G)
            values = list(betweenness.values())
            result["edge_betweenness_mean"] = float(np.mean(values))
            result["edge_betweenness_std"] = float(np.std(values))
        except Exception as e:
            logger.warning(f"Error computing edge betweenness: {e}")
            result["edge_betweenness_mean"] = 0.0
            result["edge_betweenness_std"] = 0.0
    else:
        logger.info("No edges in graph. Edge betweenness set to 0.")
    
    # Spectral Gap of Laplacian
    # The Laplacian L = D - A.
    # The spectral gap (algebraic connectivity) is the second smallest eigenvalue (lambda_2).
    # If the graph is disconnected, lambda_2 = 0.
    if G.number_of_nodes() > 1:
        try:
            # Compute Laplacian matrix
            L = laplacian(G, normalized=False)
            
            # Compute eigenvalues
            eigenvalues = np.sort(np.linalg.eigvalsh(L))
            
            # Spectral gap is lambda_2 - lambda_1 (where lambda_1 is 0 for Laplacian)
            # Effectively, it's the second smallest eigenvalue.
            if len(eigenvalues) >= 2:
                spectral_gap = eigenvalues[1] - eigenvalues[0]
                # Due to numerical precision, ensure non-negative
                result["spectral_gap"] = float(max(0.0, spectral_gap))
            else:
                result["spectral_gap"] = 0.0
        except Exception as e:
            logger.warning(f"Error computing spectral gap: {e}")
            result["spectral_gap"] = 0.0
    else:
        logger.info("Graph has <= 1 node. Spectral gap set to 0.")
    
    return result

def process_device_coupling_map(device: QubitDevice) -> GraphMetric:
    """
    Process a single QubitDevice to compute all graph metrics.
    
    Args:
        device: QubitDevice object containing coupling_map and num_qubits.
        
    Returns:
        GraphMetric object with all computed values.
    """
    logger.info(f"Processing device {device.device_id}")
    
    # Build Graph
    G = build_coupling_graph(device.coupling_map, device.num_qubits)
    
    # Compute Metrics
    path_metrics = compute_shortest_path_metrics(G)
    cluster_metrics = compute_clustering_and_assortativity(G)
    edge_spectral_metrics = compute_edge_betweenness_and_spectral_gap(G)
    
    return GraphMetric(
        device_id=device.device_id,
        avg_shortest_path_length=path_metrics["avg_shortest_path"],
        diameter=path_metrics["diameter"],
        clustering_coefficient=cluster_metrics["clustering_coefficient"],
        degree_assortativity=cluster_metrics["assortativity"],
        edge_betweenness_mean=edge_spectral_metrics["edge_betweenness_mean"],
        edge_betweenness_std=edge_spectral_metrics["edge_betweenness_std"],
        spectral_gap=edge_spectral_metrics["spectral_gap"]
    )

def main():
    """
    Entry point for standalone execution to test graph metrics.
    This function loads processed calibration data, computes metrics, and saves to CSV.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting graph metrics computation.")
    
    # Load processed calibration data
    # Assuming data is in data/processed/raw_calibration.csv
    try:
        import pandas as pd
        from pathlib import Path
        
        input_path = Path("data/processed/raw_calibration.csv")
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return
        
        df = pd.read_csv(input_path)
        
        # Convert coupling_map string to list of lists if necessary
        # Assuming the column 'coupling_map' contains string representation of list of lists
        # or a JSON string.
        # We need to reconstruct QubitDevice objects or process row by row.
        
        results = []
        for idx, row in df.iterrows():
            device_id = row['device_id']
            num_qubits = int(row['num_qubits'])
            coupling_map_str = row['coupling_map']
            
            # Parse coupling map
            import json
            try:
                # Handle potential string representations
                if isinstance(coupling_map_str, str):
                    coupling_map = json.loads(coupling_map_str)
                else:
                    coupling_map = coupling_map_str
            except Exception as e:
                logger.warning(f"Failed to parse coupling map for {device_id}: {e}")
                continue
            
            # Create a temporary QubitDevice-like object
            # Since we don't have the full QubitDevice object here, we construct it minimally
            # or call the processing function directly with parsed data.
            
            # Reusing process_device_coupling_map logic but adapting for direct data
            # We'll create a minimal QubitDevice
            from models import QubitDevice
            device = QubitDevice(
                device_id=device_id,
                num_qubits=num_qubits,
                coupling_map=coupling_map,
                t1_time=0.0, # Placeholder, not used in graph builder
                t2_time=0.0,
                cx_error_rate=0.0,
                readout_error_rate=0.0,
                timestamp="2023-01-01"
            )
            
            metric = process_device_coupling_map(device)
            results.append(metric)
        
        # Save results
        output_path = Path("data/processed/graph_metrics.csv")
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert GraphMetric to dict for CSV
        data_to_save = [m.__dict__ for m in results]
        if data_to_save:
            pd.DataFrame(data_to_save).to_csv(output_path, index=False)
            logger.info(f"Saved graph metrics to {output_path}")
        else:
            logger.warning("No metrics computed. Output file not created.")
    
    except ImportError:
        logger.error("Pandas not available. Cannot run main.")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
