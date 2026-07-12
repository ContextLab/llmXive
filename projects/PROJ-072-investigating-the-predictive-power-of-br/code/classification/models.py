import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClassificationModels:
    """
    Container for classification models and stability selection logic.
    Implements the Meinshausen & Bühlmann stability selection algorithm manually.
    """
    
    def __init__(self, n_subsamples=100, sample_fraction=0.5, penalty_threshold=0.6, random_state=42):
        """
        Initialize Stability Selection parameters.
        
        Args:
            n_subsamples: Number of subsamples to draw (L)
            sample_fraction: Fraction of samples to use in each subsample (pi)
            penalty_threshold: Minimum selection frequency to retain a feature (tau)
            random_state: Random seed for reproducibility
        """
        self.n_subsamples = n_subsamples
        self.sample_fraction = sample_fraction
        self.penalty_threshold = penalty_threshold
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)

    def _create_subsample(self, X, y):
        """Create a random subsample of the data."""
        n_samples = X.shape[0]
        n_subsample = int(n_samples * self.sample_fraction)
        indices = self.rng.choice(n_samples, size=n_subsample, replace=False)
        return X[indices], y[indices]

    def _fit_l1_model(self, X_sub, y_sub):
        """
        Fit a Logistic Regression with L1 penalty on the subsample.
        Uses a fixed C value for stability; can be tuned if needed.
        """
        # Use a relatively strong regularization to induce sparsity
        # C is inverse of regularization strength; smaller C = stronger regularization
        model = LogisticRegression(
            penalty='l1',
            solver='liblinear',
            C=0.1, 
            random_state=self.random_state,
            max_iter=1000
        )
        model.fit(X_sub, y_sub)
        return model

    def run_stability_selection(self, X, y):
        """
        Run the Stability Selection algorithm.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (n_samples,)
            
        Returns:
            selected_indices: List of feature indices selected with frequency > threshold
            selection_frequencies: Array of selection frequencies for all features
        """
        n_features = X.shape[1]
        selection_counts = np.zeros(n_features)
        
        logger.info(f"Starting Stability Selection: {self.n_subsamples} subsamples, "
                    f"sample fraction={self.sample_fraction}, threshold={self.penalty_threshold}")
        
        for i in range(self.n_subsamples):
            X_sub, y_sub = self._create_subsample(X, y)
            model = self._fit_l1_model(X_sub, y_sub)
            
            # Get non-zero coefficients (features selected by L1)
            # Note: LogisticRegression.coef_ shape is (1, n_features) for binary classification
            coefs = model.coef_[0]
            selected = np.where(np.abs(coefs) > 1e-6)[0]
            
            # Increment counts for selected features
            selection_counts[selected] += 1
            
            if (i + 1) % 10 == 0:
                logger.debug(f"Completed {i+1}/{self.n_subsamples} subsamples")

        # Calculate frequencies
        selection_frequencies = selection_counts / self.n_subsamples
        
        # Identify stable features
        stable_mask = selection_frequencies >= self.penalty_threshold
        selected_indices = np.where(stable_mask)[0]
        
        logger.info(f"Stability Selection complete. "
                    f"Selected {len(selected_indices)} features out of {n_features} "
                    f"(threshold: {self.penalty_threshold*100}% retention)")
        
        return selected_indices, selection_frequencies

    def save_stable_features(self, selected_indices, output_path):
        """
        Save selected feature indices to a CSV file.
        
        Args:
            selected_indices: Array of selected feature indices
            output_path: Path to save the CSV file
        """
        df = pd.DataFrame({
            'feature_index': selected_indices,
            'selected': [True] * len(selected_indices)
        })
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(selected_indices)} stable features to {output_path}")

def y_proba_available(model, X):
    """
    Get predicted probabilities from a fitted model.
    
    Args:
        model: Fitted sklearn model
        X: Feature matrix
        
    Returns:
        Probability of class 1 for each sample
    """
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(X)[:, 1]
    else:
        raise AttributeError("Model does not support predict_proba")

def run_classification_pipeline(X, y, stability_selection=True):
    """
    Run the full classification pipeline including optional stability selection.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels
        stability_selection: Whether to run stability selection first
        
    Returns:
        dict: Results dictionary containing model, metrics, and stable features
    """
    results = {}
    
    # Run stability selection if requested
    if stability_selection:
        selector = ClassificationModels()
        stable_indices, freqs = selector.run_stability_selection(X, y)
        
        # Save stable features
        output_path = Path('data/processed/stable_features.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        selector.save_stable_features(stable_indices, output_path)
        
        results['stable_indices'] = stable_indices
        results['selection_frequencies'] = freqs
        
        # Use only stable features for final model if any were found
        if len(stable_indices) > 0:
            X_stable = X[:, stable_indices]
            logger.info(f"Training final model on {len(stable_indices)} stable features")
        else:
            logger.warning("No stable features found, using all features")
            X_stable = X
    else:
        X_stable = X
        
    # Train a final model on selected features
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(penalty='l2', C=1.0, max_iter=1000))
    ])
    
    pipeline.fit(X_stable, y)
    results['model'] = pipeline
    
    # Calculate metrics
    y_pred = pipeline.predict(X_stable)
    y_proba = pipeline.predict_proba(X_stable)[:, 1]
    
    results['accuracy'] = accuracy_score(y, y_pred)
    results['precision'] = precision_score(y, y_pred, zero_division=0)
    results['recall'] = recall_score(y, y_pred, zero_division=0)
    results['auc_roc'] = roc_auc_score(y, y_proba)
    
    return results

def main():
    """
    Main entry point for running stability selection and classification.
    Loads features from data/processed/features.csv and runs the pipeline.
    """
    logger.info("Starting Stability Selection and Classification Pipeline")
    
    # Load features
    features_path = Path('data/processed/features.csv')
    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}")
        logger.error("Please run the feature extraction pipeline first (US2)")
        sys.exit(1)
    
    df = pd.read_csv(features_path)
    
    # Separate features and labels
    # Assuming the last column is the label (adjust if schema differs)
    if 'label' not in df.columns:
        logger.error("No 'label' column found in features file")
        sys.exit(1)
        
    y = df['label'].values
    X = df.drop(columns=['label']).values
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
    
    # Run pipeline
    results = run_classification_pipeline(X, y, stability_selection=True)
    
    # Log results
    logger.info(f"Classification Accuracy: {results['accuracy']:.4f}")
    logger.info(f"Precision: {results['precision']:.4f}")
    logger.info(f"Recall: {results['recall']:.4f}")
    logger.info(f"AUC-ROC: {results['auc_roc']:.4f}")
    logger.info(f"Stable features saved to: data/processed/stable_features.csv")
    
    # Save model
    model_path = Path('data/processed/classification_model.joblib')
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(results['model'], model_path)
    logger.info(f"Model saved to: {model_path}")
    
    return results

if __name__ == "__main__":
    main()
