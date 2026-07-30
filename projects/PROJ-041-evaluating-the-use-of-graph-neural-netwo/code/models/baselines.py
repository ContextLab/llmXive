"""
Baseline models for comparison with GNN approaches.
Includes Random Forest and XGBoost implementations.
"""
import os
import logging
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

logger = logging.getLogger(__name__)


class FeatureEngineeredBaseline:
    """
    Wrapper for feature-engineered baseline models (RF, XGBoost).
    Uses structural graph features as input.
    """

    def __init__(
        self,
        model_type: str = 'rf',
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42
    ):
        """
        Initialize baseline model.

        Args:
            model_type: 'rf' for Random Forest, 'xgb' for XGBoost.
            n_estimators: Number of trees.
            max_depth: Maximum tree depth.
            random_state: Random seed.
        """
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None

    def _create_model(self):
        """Create the underlying model based on type."""
        if self.model_type == 'rf':
            return RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                n_jobs=-1
            )
        elif self.model_type == 'xgb':
            return xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                n_jobs=-1,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[list] = None):
        """
        Train the baseline model.

        Args:
            X: Feature matrix (nodes x features).
            y: Target labels.
            feature_names: Optional list of feature names.
        """
        self.feature_names = feature_names
        X_scaled = self.scaler.fit_transform(X)
        self.model = self._create_model()
        self.model.fit(X_scaled, y)
        logger.info(f"Trained {self.model_type} model with {X.shape[0]} samples")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if self.model is None:
            raise RuntimeError("Model not trained yet")

        if self.model_type == 'rf':
          importances = self.model.feature_importances_
        elif self.model_type == 'xgb':
          importances = self.model.feature_importances_
        else:
          raise ValueError(f"Importance not implemented for {self.model_type}")

        if self.feature_names:
            return dict(zip(self.feature_names, importances))
        else:
            return {f"feature_{i}": imp for i, imp in enumerate(importances)}


def extract_structural_features(G) -> tuple:
    """
    Extract structural features from a NetworkX graph.

    Args:
        G: NetworkX graph object.

    Returns:
        Tuple of (feature_matrix, feature_names).
    """
    import networkx as nx
    import numpy as np

    nodes = list(G.nodes())
    n_nodes = len(nodes)

    # Compute various structural features
    degrees = np.array([d for _, d in G.degree()]).reshape(-1, 1)
    in_degrees = np.array([d for _, d in G.in_degree()]).reshape(-1, 1)
    out_degrees = np.array([d for _, d in G.out_degree()]).reshape(-1, 1)

    # Betweenness centrality (sampled for large graphs)
    if n_nodes > 1000:
        betweenness = nx.betweenness_centrality(G, k=min(100, n_nodes))
    else:
        betweenness = nx.betweenness_centrality(G)
    betweenness = np.array([betweenness.get(n, 0) for n in nodes]).reshape(-1, 1)

    # Clustering coefficient (for undirected view)
    G_undirected = G.to_undirected()
    clustering = nx.clustering(G_undirected)
    clustering = np.array([clustering.get(n, 0) for n in nodes]).reshape(-1, 1)

    # Eigenvector centrality (sampled)
    if n_nodes > 1000:
        try:
            eigenvector = nx.eigenvector_centrality(G, max_iter=100)
        except:
            eigenvector = {n: 0 for n in nodes}
    else:
        try:
            eigenvector = nx.eigenvector_centrality(G)
        except:
            eigenvector = {n: 0 for n in nodes}
    eigenvector = np.array([eigenvector.get(n, 0) for n in nodes]).reshape(-1, 1)

    # Combine features
    X = np.hstack([degrees, in_degrees, out_degrees, betweenness, clustering, eigenvector])
    feature_names = ['degree', 'in_degree', 'out_degree', 'betweenness', 'clustering', 'eigenvector']

    return X, feature_names


def main():
    """Example usage of baseline models."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Baselines module loaded successfully")

    # Example: Create a Random Forest model
    rf = FeatureEngineeredBaseline(model_type='rf', n_estimators=100)
    logger.info(f"Created RF model: {rf}")


if __name__ == "__main__":
    main()
