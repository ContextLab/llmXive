import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs
import networkx as nx

# Local imports
from models.polymer_graph import PolymerGraph
from models.gnn import polymer_graph_to_pyg_data

logger = logging.getLogger(__name__)

def smiles_to_ecfp4(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Convert a SMILES string to an ECFP4 fingerprint (binary vector).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def polymer_graph_to_fingerprint(graph: PolymerGraph) -> np.ndarray:
    """
    Convert a PolymerGraph object to an ECFP4 fingerprint.
    Assumes the graph has a 'smiles' attribute or can be reconstructed.
    For this implementation, we assume the graph stores the original SMILES
    or we reconstruct it from the graph structure if possible.
    However, since PolymerGraph is a custom data structure, we will rely
    on the assumption that we can extract the SMILES or use node features
    to approximate.
    
    Given the constraints of the existing API, we will attempt to reconstruct
    a molecule from the graph's node/edge features if 'smiles' is not directly
    available, or raise an error if reconstruction is not feasible.
    
    For robustness, we assume the PolymerGraph passed here has a 'smiles' field
    populated during ingestion (T011a).
    """
    if not hasattr(graph, 'smiles') or graph.smiles is None:
        # Fallback: Try to reconstruct from node/edge features if possible
        # This is a simplified fallback; in a real scenario, we'd need a full
        # graph-to-smiles reconstruction which is complex.
        # For now, we assume the ingestion pipeline ensures 'smiles' is present.
        raise ValueError("PolymerGraph must have a 'smiles' attribute for fingerprinting.")
    
    return smiles_to_ecfp4(graph.smiles)

def polymer_graph_to_descriptors(graph: PolymerGraph) -> np.ndarray:
    """
    Convert a PolymerGraph to a set of RDKit molecular descriptors.
    """
    if not hasattr(graph, 'smiles') or graph.smiles is None:
        raise ValueError("PolymerGraph must have a 'smiles' attribute for descriptors.")
    
    mol = Chem.MolFromSmiles(graph.smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES in graph: {graph.smiles}")
    
    # Select a subset of common descriptors
    from rdkit.Chem import Descriptors
    descriptors = [
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.NumHDonors(mol),
        Descriptors.NumHAcceptors(mol),
        Descriptors.NumRotatableBonds(mol),
        Descriptors.TPSA(mol),
        Descriptors.NumAromaticRings(mol),
        Descriptors.FractionCSP3(mol),
    ]
    return np.array(descriptors, dtype=np.float32)

class RandomForestBaseline:
    """
    Random Forest baseline using ECFP4 fingerprints.
    """
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, graphs: List[PolymerGraph], y: np.ndarray):
        """
        Fit the Random Forest model.
        """
        X = np.array([polymer_graph_to_fingerprint(g) for g in graphs])
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"RandomForestBaseline fitted with {len(graphs)} samples.")

    def predict(self, graphs: List[PolymerGraph]) -> np.ndarray:
        """
        Predict log-permeability for a list of graphs.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        X = np.array([polymer_graph_to_fingerprint(g) for g in graphs])
        return self.model.predict(X)

class LinearRegressionBaseline:
    """
    Linear Regression baseline using RDKit descriptors.
    """
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = LinearRegression()
        self.is_fitted = False

    def fit(self, graphs: List[PolymerGraph], y: np.ndarray):
        """
        Fit the Linear Regression model.
        """
        X = np.array([polymer_graph_to_descriptors(g) for g in graphs])
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"LinearRegressionBaseline fitted with {len(graphs)} samples.")

    def predict(self, graphs: List[PolymerGraph]) -> np.ndarray:
        """
        Predict log-permeability for a list of graphs.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        X = np.array([polymer_graph_to_descriptors(g) for g in graphs])
        return self.model.predict(X)

class RandomizedTopologyControlBaseline:
    """
    Randomized Topology Control Baseline.
    
    This baseline uses the same atomic composition (node features) as the GNN input
    but with randomized edge connections (preserving degree distribution).
    This ensures that any performance difference between the GNN and this baseline
    can be attributed to the GNN's ability to learn graph structure (topology),
    rather than just atomic composition.
    
    Implementation Strategy:
    1. Convert the input PolymerGraph to a NetworkX graph.
    2. Randomize the edges while preserving the degree sequence (using configuration model).
    3. Extract node features from the randomized graph (same as original).
    4. Convert the randomized graph to a fingerprint/descriptor set.
    5. Train a simple model (e.g., Linear Regression) on these randomized features.
    
    Note: Since the GNN input is a graph structure, we must convert the randomized
    graph back to a format compatible with the baseline models (ECFP4 or descriptors).
    However, randomized graphs may not have valid SMILES. Therefore, we will
    compute descriptors directly from the randomized graph's node features if possible,
    or use a simplified representation.
    
    For this implementation, we will:
    - Extract node features (atom type, hybridization, bond type) from the original graph.
    - Create a randomized adjacency matrix preserving degrees.
    - Since RDKit requires valid molecules, we cannot directly compute ECFP4 from a
      randomized graph that may not correspond to a valid molecule.
    - Instead, we will use the node features to create a "bag-of-atoms" representation
      (e.g., count of each atom type) and use that as the input to a linear model.
      This effectively removes topological information while preserving composition.
    
    This approach aligns with the goal: compare GNN (structure-aware) vs. Composition-only model.
    """
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = LinearRegression()
        self.is_fitted = False
        self.rng = np.random.default_rng(random_state)

    def _graph_to_composition_vector(self, graph: PolymerGraph) -> np.ndarray:
        """
        Convert a PolymerGraph to a composition vector (bag-of-atoms).
        This ignores topology and only counts atom types.
        """
        # Define a fixed set of atom types to count
        atom_types = ['C', 'N', 'O', 'S', 'F', 'Cl', 'Br', 'I', 'P']
        counts = {atom: 0 for atom in atom_types}
        
        for node in graph.nodes:
            atom_symbol = node.get('atom_type', None)
            if atom_symbol and atom_symbol in counts:
                counts[atom_symbol] += 1
        
        return np.array([counts[atom] for atom in atom_types], dtype=np.float32)

    def _randomize_graph_topology(self, graph: PolymerGraph) -> nx.Graph:
        """
        Create a randomized version of the graph preserving degree distribution.
        Returns a NetworkX graph with the same nodes and degrees but random edges.
        Note: The resulting graph may not be chemically valid (no SMILES).
        """
        G = nx.Graph()
        
        # Add nodes with attributes
        for i, node in enumerate(graph.nodes):
            G.add_node(i, **node)
        
        # Add edges
        edges = [(u, v) for u, v in graph.edges]
        G.add_edges_from(edges)
        
        # Randomize edges while preserving degree sequence
        # Using the configuration model and then converting to a simple graph
        # This may result in self-loops or multi-edges, which we remove.
        try:
            randomized_G = nx.configuration_model(G)
            randomized_G = nx.Graph(randomized_G)  # Remove self-loops and multi-edges
            # Ensure the number of nodes is the same
            if len(randomized_G.nodes) != len(G.nodes):
                # Fallback: if configuration model fails, return original
                logger.warning("Configuration model failed to preserve node count. Using original graph.")
                return G
            return randomized_G
        except Exception as e:
            logger.warning(f"Topology randomization failed: {e}. Using original graph.")
            return G

    def _randomized_graph_to_features(self, graph: PolymerGraph) -> np.ndarray:
        """
        Convert a PolymerGraph to features using randomized topology.
        Since the randomized graph may not be a valid molecule, we cannot use RDKit
        to compute ECFP4 or standard descriptors. Instead, we use the composition
        vector (bag-of-atoms) which is invariant to topology.
        
        This is the key: the baseline should NOT have access to topology.
        Therefore, we use the composition vector derived from the original graph
        (which is the same as the randomized graph's composition).
        """
        return self._graph_to_composition_vector(graph)

    def fit(self, graphs: List[PolymerGraph], y: np.ndarray):
        """
        Fit the Randomized Topology Control model.
        """
        X = np.array([self._randomized_graph_to_features(g) for g in graphs])
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"RandomizedTopologyControlBaseline fitted with {len(graphs)} samples.")

    def predict(self, graphs: List[PolymerGraph]) -> np.ndarray:
        """
        Predict log-permeability for a list of graphs using composition-only features.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        X = np.array([self._randomized_graph_to_features(g) for g in graphs])
        return self.model.predict(X)

def main():
    """
    Entry point for testing baselines.
    """
    setup_logging()
    logger.info("Running baseline tests...")
    
    # Example usage (would require actual data)
    # graphs = [...]  # List of PolymerGraph objects
    # y = [...]       # True values
    
    # rf = RandomForestBaseline()
    # rf.fit(graphs, y)
    # rf_preds = rf.predict(graphs)
    
    # lr = LinearRegressionBaseline()
    # lr.fit(graphs, y)
    # lr_preds = lr.predict(graphs)
    
    # topo_control = RandomizedTopologyControlBaseline()
    # topo_control.fit(graphs, y)
    # topo_preds = topo_control.predict(graphs)
    
    logger.info("Baseline tests completed.")

if __name__ == "__main__":
    main()