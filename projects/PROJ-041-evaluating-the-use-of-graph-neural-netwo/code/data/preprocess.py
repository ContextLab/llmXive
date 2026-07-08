"""
Data preprocessing module.
Implements graph construction and strict subsampling (LCC) logic.
"""
import os
import logging
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_lcc(graph: nx.Graph) -> nx.Graph:
    """
    Extract the Largest Connected Component (LCC) from a graph.
    Strict Rule: Return LCC as-is. Do not pad.
    If the graph is empty, return an empty graph.
    """
    if not graph.nodes():
        logger.warning("Input graph is empty. Returning empty graph.")
        return nx.Graph()
    
    # Find connected components
    connected_components = list(nx.connected_components(graph))
    
    if not connected_components:
        return nx.Graph()
    
    # Identify the largest component
    largest_cc = max(connected_components, key=len)
    num_nodes_lcc = len(largest_cc)
    num_nodes_total = graph.number_of_nodes()
    
    logger.info(f"Extracting LCC: {num_nodes_lcc} nodes out of {num_nodes_total} total nodes.")
    
    # Subgraph and copy to ensure we own the data
    lcc_subgraph = graph.subgraph(largest_cc).copy()
    return lcc_subgraph

def preprocess_graph(input_path: str, output_path: str):
    """
    Load a graph from a GraphML file, extract the Largest Connected Component (LCC),
    and save the result to the specified output path.
    
    Strict Rule: 
    - Extract ONLY the LCC.
    - Do NOT pad the graph if LCC < 5,000 nodes.
    - If LCC < 5,000, retain LCC as-is.
    
    Args:
        input_path (str): Path to the input GraphML file.
        output_path (str): Path to save the processed GraphML file.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a valid graph or empty.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input graph file not found: {input_path}")
    
    logger.info(f"Loading graph from: {input_path}")
    try:
        G = nx.read_graphml(input_path)
    except Exception as e:
        logger.error(f"Failed to load graph from {input_path}: {e}")
        raise ValueError(f"Invalid graph file: {e}")
    
    if G.number_of_nodes() == 0:
        logger.warning("Loaded graph is empty. Cannot process.")
        raise ValueError("Input graph is empty.")
    
    logger.info(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # Extract LCC
    lcc_graph = extract_lcc(G)
    
    lcc_nodes = lcc_graph.number_of_nodes()
    logger.info(f"Processed graph (LCC) has {lcc_nodes} nodes and {lcc_graph.number_of_edges()} edges.")
    
    if lcc_nodes == 0:
        logger.warning("LCC extraction resulted in an empty graph.")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Saving processed graph to: {output_path}")
    nx.write_graphml(lcc_graph, output_path)
    logger.info("Preprocessing complete.")

def main():
    """
    Entry point for running the preprocessing script directly.
    Expects command line arguments: <input_path> <output_path>
    """
    import sys
    if len(sys.argv) != 3:
        print("Usage: python preprocess.py <input_graph.graphml> <output_graph.graphml>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        preprocess_graph(input_file, output_file)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()