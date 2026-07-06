"""
Baseline models for permeability prediction.
Implements Random Forest using ECFP4 fingerprints.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, pearsonr
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

from models.permeability_record import PermeabilityRecord
from models.polymer_graph import PolymerGraph

logger = logging.getLogger(__name__)


def smiles_to_ecfp4(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Convert a SMILES string to an ECFP4 fingerprint vector.

    Args:
        smiles: SMILES string of the molecule.
        radius: Radius for ECFP (2 for ECFP4).
        n_bits: Number of bits in the fingerprint.

    Returns:
        Numpy array of shape (n_bits,) containing the fingerprint.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def polymer_graph_to_fingerprint(graph: PolymerGraph) -> np.ndarray:
    """
    Convert a PolymerGraph to an ECFP4 fingerprint.
    
    This assumes the graph has a 'smiles' attribute or can be reconstructed
    to a SMILES string. If not, it attempts to use the node/edge features
    to reconstruct a valid RDKit molecule.
    
    For this implementation, we assume the PolymerGraph stores the canonical
    SMILES in a 'smiles' field or we derive it from the graph structure.
    If the graph is complex (polymer repeat unit), we use the stored SMILES
    if available, otherwise we raise an error.
    """
    # Attempt to retrieve SMILES from the graph
    if hasattr(graph, 'smiles') and graph.smiles:
        smiles = graph.smiles
    elif hasattr(graph, 'canonical_smiles') and graph.canonical_smiles:
        smiles = graph.canonical_smiles
    else:
        # Fallback: try to reconstruct from atom/bond lists if possible
        # This is a simplified fallback; in a full implementation, 
        # we would rebuild the RDKit molecule from the graph data.
        raise NotImplementedError(
            "PolymerGraph does not expose a SMILES string directly. "
            "Please ensure the graph object has 'smiles' or 'canonical_smiles' attribute, "
            "or implement a graph-to-mol reconstruction method."
        )
    
    return smiles_to_ecfp4(smiles)


def prepare_features(
    graphs: List[PolymerGraph],
    n_bits: int = 2048
) -> Tuple[np.ndarray, List[float]]:
    """
    Prepare feature matrix and target vector from a list of PolymerGraphs.
    
    Args:
        graphs: List of PolymerGraph objects.
        n_bits: Number of bits for ECFP4.
        
    Returns:
        Tuple of (feature_matrix, target_values)
    """
    X = []
    y = []
    
    for i, graph in enumerate(graphs):
        try:
            fp = polymer_graph_to_fingerprint(graph)
            X.append(fp)
            
            # Extract target: log-permeability
            # Assuming PermeabilityRecord is associated or graph has permeability data
            if hasattr(graph, 'permeability') and graph.permeability is not None:
                target = graph.permeability
            elif hasattr(graph, 'permeability_record') and graph.permeability_record is not None:
                target = graph.permeability_record.log_permeability
            else:
                # Try to find a 'log_permeability' attribute directly
                if hasattr(graph, 'log_permeability'):
                    target = graph.log_permeability
                else:
                    logger.warning(f"Skipping graph {i}: No permeability target found.")
                    continue
            
            y.append(target)
        except Exception as e:
            logger.warning(f"Skipping graph {i} due to error: {e}")
            continue
    
    if len(X) == 0:
        raise ValueError("No valid graphs with targets found.")
        
    return np.array(X), np.array(y)


class RandomForestBaseline:
    """
    Random Forest Regressor baseline using ECFP4 fingerprints.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=n_jobs
        )
        self.is_fitted = False
        
    def fit(self, graphs: List[PolymerGraph]) -> 'RandomForestBaseline':
        """
        Fit the Random Forest model on the provided graphs.
        
        Args:
            graphs: List of PolymerGraph objects with associated permeability targets.
            
        Returns:
            Self.
        """
        logger.info(f"Preparing features for {len(graphs)} graphs...")
        X, y = prepare_features(graphs)
        logger.info(f"Training Random Forest on {X.shape[0]} samples, {X.shape[1]} features.")
        
        self.model.fit(X, y)
        self.is_fitted = True
        return self
        
    def predict(self, graphs: List[PolymerGraph]) -> np.ndarray:
        """
        Predict permeability for a list of graphs.
        
        Args:
            graphs: List of PolymerGraph objects.
            
        Returns:
            Array of predicted log-permeability values.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted yet.")
            
        X, _ = prepare_features(graphs)
        return self.model.predict(X)
        
    def evaluate(
        self,
        graphs: List[PolymerGraph],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate the model on a set of graphs.
        
        Args:
            graphs: List of PolymerGraph objects.
            metrics: List of metric names to compute. Defaults to ['r2', 'mae', 'pearson'].
            
        Returns:
            Dictionary of metric names to values.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted yet.")
            
        X, y_true = prepare_features(graphs)
        y_pred = self.model.predict(X)
        
        if metrics is None:
            metrics = ['r2', 'mae', 'pearson']
            
        results = {}
        
        if 'r2' in metrics:
            results['r2'] = float(r2_score(y_true, y_pred))
        if 'mae' in metrics:
            results['mae'] = float(mean_absolute_error(y_true, y_pred))
        if 'pearson' in metrics:
            r, _ = pearsonr(y_true, y_pred)
            results['pearson'] = float(r)
            
        return results


def main() -> None:
    """
    Main entry point for testing the Random Forest baseline.
    This function is intended to be run as a script to verify the baseline
    works end-to-end with real data (if available in memory or loaded).
    
    For a full pipeline integration, this would be called by the trainer/evaluator.
    """
    logging.basicConfig(level=logging.INFO)
    
    # This is a placeholder for demonstration.
    # In a real scenario, we would load graphs from the processed dataset.
    # Since T014 produces `data/processed/polymers.h5`, we would load from there.
    # However, to keep this task focused on the baseline implementation,
    # we assume the caller provides the graphs.
    
    logger.info("RandomForestBaseline implementation ready.")
    logger.info("To use: Instantiate RandomForestBaseline, call fit(graphs), then evaluate(graphs).")


if __name__ == "__main__":
    main()