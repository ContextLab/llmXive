"""Pipeline factory for nested cross-validation."""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA

def create_pipeline(variance_threshold: float = 0.01, pca_retention: float = 0.95, 
                    data_subset: Optional[List[str]] = None) -> Pipeline:
    """
    Create a nested CV pipeline with Variance Thresholding and PCA.
    
    Args:
        variance_threshold: Variance threshold for feature selection.
        pca_retention: Variance retention for PCA.
        data_subset: Optional list of subject IDs to subset the data.
        
    Returns:
        A sklearn Pipeline object.
    """
    # Define the pipeline steps
    steps = [
        ('variance', VarianceThreshold(threshold=variance_threshold)),
        ('pca', PCA(n_components=pca_retention, svd_solver='full')),
        ('scaler', StandardScaler()),
        ('elasticnet', ElasticNetCV(
            l1_ratio=[0.1, 0.5, 0.9],
            alphas=[0.01, 0.1, 1.0],
            cv=5,
            max_iter=1000
        ))
    ]
    
    pipeline = Pipeline(steps)
    return pipeline

class NestedCVPipeline:
    """Wrapper for nested cross-validation."""
    
    def __init__(self, pipeline: Pipeline, n_outer_folds: int = 5):
        self.pipeline = pipeline
        self.n_outer_folds = n_outer_folds
        self.predictions = None
        self.metrics = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit the pipeline using nested CV."""
        # Outer CV loop
        outer_cv = KFold(n_splits=self.n_outer_folds, shuffle=True, random_state=42)
        
        # Get predictions for each sample using outer CV
        self.predictions = cross_val_predict(self.pipeline, X, y, cv=outer_cv)
        
        # Compute metrics
        from sklearn.metrics import r2_score, mean_squared_error
        self.metrics['r2'] = r2_score(y, self.predictions)
        self.metrics['rmse'] = mean_squared_error(y, self.predictions, squared=False)
    
    def get_predictions(self) -> np.ndarray:
        """Get outer-fold predictions."""
        return self.predictions
    
    def get_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        return self.metrics

if __name__ == "__main__":
    # Test the pipeline
    X_test = np.random.randn(100, 50)
    y_test = np.random.randn(100)
    
    pipe = create_pipeline()
    print("Pipeline created successfully")
    print(pipe)
