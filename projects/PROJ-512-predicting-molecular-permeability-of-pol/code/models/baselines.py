import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, pearsonr
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem
from rdkit import DataStructs

# Import existing project modules
from models.polymer_graph import PolymerGraph
from data.utils import set_seed, ensure_seed_initialized

logger = logging.getLogger(__name__)

def smiles_to_ecfp4(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Convert a SMILES string to an ECFP4 fingerprint (bit vector).
    
    Args:
        smiles: SMILES string of the molecule.
        radius: Radius for ECFP (2 for ECFP4).
        n_bits: Number of bits in the fingerprint.
    
    Returns:
        Numpy array of bits (0 or 1).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Could not parse SMILES: {smiles}")
        return np.zeros(n_bits, dtype=np.float32)
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int32)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr.astype(np.float32)

def polymer_graph_to_fingerprint(graph: PolymerGraph, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Convert a PolymerGraph to an ECFP4 fingerprint.
    
    Args:
        graph: PolymerGraph object containing SMILES.
        radius: Radius for ECFP.
        n_bits: Number of bits.
    
    Returns:
        Numpy array of bits.
    """
    if not hasattr(graph, 'smiles') or graph.smiles is None:
        logger.error("PolymerGraph missing SMILES string")
        return np.zeros(n_bits, dtype=np.float32)
    return smiles_to_ecfp4(graph.smiles, radius, n_bits)

def prepare_features(graphs: List[PolymerGraph], use_ecfp: bool = True) -> Tuple[np.ndarray, List[float]]:
    """
    Prepare feature matrix and target vector from a list of PolymerGraphs.
    
    For Linear Regression baseline, we use standard RDKit molecular descriptors
    instead of ECFP4 fingerprints to ensure a linear model is interpretable and
    robust on small datasets.
    
    Args:
        graphs: List of PolymerGraph objects.
        use_ecfp: Ignored for LinearRegression (uses descriptors), kept for API consistency.
    
    Returns:
        Tuple of (feature_matrix, target_values).
    """
    # Common RDKit descriptors for linear models
    descriptor_names = [
        'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors', 
        'NumRotatableBonds', 'TPSA', 'NumAromaticRings', 
        'FractionCSP3', 'NumHeteroatoms', 'RingCount'
    ]
    
    X = []
    y = []
    
    for graph in graphs:
        if not hasattr(graph, 'smiles') or graph.smiles is None:
            logger.warning(f"Skipping graph with no SMILES: {graph}")
            continue
        
        mol = Chem.MolFromSmiles(graph.smiles)
        if mol is None:
            continue
        
        # Extract descriptors
        row = []
        for desc_name in descriptor_names:
            try:
                desc_func = getattr(Descriptors, desc_name)
                val = desc_func(mol)
                if val is None or np.isnan(val):
                    val = 0.0
                row.append(float(val))
            except Exception as e:
                logger.warning(f"Failed to compute {desc_name}: {e}")
                row.append(0.0)
        
        X.append(row)
        
        # Extract target (log-permeability)
        if hasattr(graph, 'log_permeability') and graph.log_permeability is not None:
            y.append(float(graph.log_permeability))
        else:
            logger.warning(f"Skipping graph with no log_permeability: {graph}")
            continue
    
    if len(X) == 0:
        raise ValueError("No valid data points found for feature preparation.")
    
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

class LinearRegressionBaseline:
    """
    Linear Regression baseline model using RDKit molecular descriptors.
    
    This model provides an interpretable baseline for permeability prediction.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.is_fitted = False
        self.feature_names = [
            'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors', 
            'NumRotatableBonds', 'TPSA', 'NumAromaticRings', 
            'FractionCSP3', 'NumHeteroatoms', 'RingCount'
        ]
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the linear regression model.
        
        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target vector (n_samples,).
        """
        if X.shape[0] == 0:
            raise ValueError("Cannot fit model with zero samples.")
        
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"Linear Regression fitted. R^2 on training: {self.model.score(X, y):.4f}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict permeability for given features.
        
        Args:
            X: Feature matrix.
        
        Returns:
            Predicted values.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            X: Feature matrix.
            y_true: True target values.
        
        Returns:
            Dictionary of metrics (R2, MAE, Pearson).
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        
        y_pred = self.predict(X)
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        pearson, _ = pearsonr(y_true, y_pred)
        
        metrics = {
            'r2': float(r2),
            'mae': float(mae),
            'pearson': float(pearson)
        }
        logger.info(f"Linear Regression Evaluation: R2={r2:.4f}, MAE={mae:.4f}, Pearson={pearson:.4f}")
        return metrics

class RandomForestBaseline:
    """
    Random Forest baseline model using ECFP4 fingerprints.
    """
    
    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = None):
        self.model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit the Random Forest model."""
        if X.shape[0] == 0:
            raise ValueError("Cannot fit model with zero samples.")
        
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"Random Forest fitted. R^2 on training: {self.model.score(X, y):.4f}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict permeability."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        
        y_pred = self.predict(X)
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        pearson, _ = pearsonr(y_true, y_pred)
        
        metrics = {
            'r2': float(r2),
            'mae': float(mae),
            'pearson': float(pearson)
        }
        logger.info(f"Random Forest Evaluation: R2={r2:.4f}, MAE={mae:.4f}, Pearson={pearson:.4f}")
        return metrics

def main():
    """
    Main entry point for testing baselines.
    
    This function demonstrates the usage of the Linear Regression baseline
    by loading a sample dataset (if available) or creating synthetic data
    for demonstration purposes only (not for production use).
    """
    set_seed(42)
    setup_logging()
    
    logger.info("Initializing Baseline Models...")
    
    # Note: In a real pipeline, data would be loaded from data/processed/polymers.h5
    # Here we just instantiate the classes to verify they work
    lr_model = LinearRegressionBaseline()
    rf_model = RandomForestBaseline(n_estimators=50)
    
    logger.info("Linear Regression and Random Forest baseline classes initialized.")
    logger.info("To run full evaluation, integrate with data loading pipeline in T024/T025.")

if __name__ == "__main__":
    main()