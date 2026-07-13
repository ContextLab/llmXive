import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA
import logging

from config import get_hyperparameter

class NestedCVPipeline:
    """
    Encapsulates the nested CV logic.
    - Outer loop: KFold for evaluation
    - Inner loop: ElasticNetCV (which does its own CV) + Preprocessing fitted on train fold only
    """
    def __init__(self, variance_threshold=0.01, pca_variance=0.95):
        self.variance_threshold = variance_threshold
        self.pca_variance = pca_variance
        self.logger = logging.getLogger(__name__)

    def create_pipeline(self):
        """
        Creates a sklearn Pipeline that includes:
        1. VarianceThreshold (fitted in CV fold)
        2. PCA (fitted in CV fold)
        3. ElasticNetCV (fitted in CV fold, inner CV for alpha)
        """
        # Note: ElasticNetCV performs internal CV for alpha selection.
        # To ensure strict nested CV, we wrap it so that the preprocessing
        # steps are fitted ONLY on the training split of the outer loop.
        # sklearn's Pipeline + cross_val_predict handles this correctly 
        # if the estimator (ElasticNetCV) is the last step.
        
        steps = [
            ('var_thresh', VarianceThreshold(threshold=self.variance_threshold)),
            ('pca', PCA(n_variance=self.pca_variance)),
            ('enet', ElasticNetCV(cv=5, random_state=get_hyperparameter('seed')))
        ]
        return Pipeline(steps)

def create_pipeline(variance_threshold=0.01, pca_variance=0.95):
    """
    Factory function to create the nested CV pipeline.
    T020a Implementation: Encapsulates nested CV logic.
    Accepts optional data_subset parameter? 
    The pipeline itself doesn't need the data subset; the training loop does.
    But we return the pipeline object ready to be used in cross_val_predict.
    """
    pipeline = NestedCVPipeline(variance_threshold, pca_variance)
    return pipeline.create_pipeline()