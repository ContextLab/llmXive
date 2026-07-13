import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV

class NestedCVPipeline:
    def __init__(self, variance_threshold=0.01, pca_retention=0.95):
        self.variance_threshold = variance_threshold
        self.pca_retention = pca_retention
        self.pipeline = None

    def fit(self, X, y):
        from sklearn.feature_selection import VarianceThreshold
        from sklearn.decomposition import PCA
        
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('variance', VarianceThreshold(threshold=self.variance_threshold)),
            ('pca', PCA(n_components=self.pca_retention, svd_solver='full')),
            ('regressor', ElasticNetCV(cv=5, random_state=42))
        ])
        self.pipeline.fit(X, y)
        return self

    def predict(self, X):
        return self.pipeline.predict(X)

def create_pipeline(variance_threshold=0.01, pca_retention=0.95):
    """Create a new nested CV pipeline."""
    return NestedCVPipeline(variance_threshold=variance_threshold, pca_retention=pca_retention)
