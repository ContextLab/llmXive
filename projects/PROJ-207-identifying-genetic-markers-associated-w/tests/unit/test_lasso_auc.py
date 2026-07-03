"""
Unit test for LASSO AUC calculation (T025).

Tests the LASSO logistic regression AUC calculation logic as specified in US3.
This test uses synthetic data to verify the calculation pipeline without
requiring external data downloads.
"""
import pytest
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler


class LassoAUCCalculator:
    """
    Helper class to encapsulate LASSO AUC calculation logic.
    This mirrors the logic expected in code/04_ml_validation.py (T027).
    """
    
    def __init__(self, X, y, l1_ratio=1.0, n_folds=5, random_state=42):
        """
        Initialize the calculator.
        
        Args:
            X: Feature matrix (SNP data + covariates)
            y: Binary phenotype vector (CCD status)
            l1_ratio: Penalty mixing parameter (1.0 = pure LASSO)
            n_folds: Number of CV folds
            random_state: Random seed for reproducibility
        """
        self.X = X
        self.y = y
        self.l1_ratio = l1_ratio
        self.n_folds = n_folds
        self.random_state = random_state
        self.scorer = LogisticRegression(
            penalty='l1',
            solver='saga',
            l1_ratio=self.l1_ratio,
            random_state=self.random_state,
            max_iter=1000
        )
        self.cv = StratifiedKFold(
            n_splits=self.n_folds,
            shuffle=True,
            random_state=self.random_state
        )

    def calculate_cross_validated_auc(self):
        """
        Perform k-fold cross-validation and return the mean AUC.
        
        Returns:
            float: Mean AUC across all folds.
        """
        if np.sum(self.y) == 0 or np.sum(self.y) == len(self.y):
            raise ValueError("Phenotype vector must contain both classes.")
        
        if self.X.shape[0] < self.n_folds:
            raise ValueError("Sample size too small for requested number of folds.")

        aucs = []
        scaler = StandardScaler()
        
        # Fit scaler on full data to ensure consistent scaling across folds
        # In a strict production pipeline, scaler might be fit per fold, 
        # but for this unit test of the AUC logic, global scaling is acceptable
        # to isolate the AUC calculation mechanism.
        X_scaled = scaler.fit_transform(self.X)

        for train_idx, test_idx in self.cv.split(X_scaled, self.y):
            X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
            y_train, y_test = self.y[train_idx], self.y[test_idx]

            # Fit LASSO model
            model = LogisticRegression(
                penalty='l1',
                solver='saga',
                l1_ratio=self.l1_ratio,
                random_state=self.random_state,
                max_iter=1000
            )
            model.fit(X_train, y_train)

            # Predict probabilities for the positive class
            y_pred_prob = model.predict_proba(X_test)[:, 1]
            
            # Calculate AUC
            auc = roc_auc_score(y_test, y_pred_prob)
            aucs.append(auc)

        return np.mean(aucs)


def test_lasso_auc_basic_functionality():
    """Test that the calculator returns a valid float between 0 and 1."""
    # Generate synthetic data: 200 samples, 50 features
    np.random.seed(42)
    n_samples = 200
    n_features = 50
    
    X = np.random.randn(n_samples, n_features)
    # Create a signal: first 5 features are predictive
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1 > 0).astype(int)
    
    calculator = LassoAUCCalculator(X, y, n_folds=5)
    auc = calculator.calculate_cross_validated_auc()
    
    assert isinstance(auc, float), "AUC should be a float"
    assert 0.0 <= auc <= 1.0, f"AUC {auc} must be between 0 and 1"


def test_lasso_auc_perfect_separation():
    """Test behavior when data is perfectly separable (edge case)."""
    np.random.seed(42)
    n_samples = 100
    X = np.random.randn(n_samples, 10)
    # Perfect separation: y = 1 if X[:, 0] > 0
    y = (X[:, 0] > 0).astype(int)
    
    calculator = LassoAUCCalculator(X, y, n_folds=5)
    auc = calculator.calculate_cross_validated_auc()
    
    # With perfect separation, AUC should be high (close to 1.0)
    # Note: L1 penalty might shrink coefficients, but AUC should still reflect
    # the separability.
    assert auc >= 0.9, f"Perfect separation should yield high AUC, got {auc}"


def test_lasso_auc_no_signal():
    """Test that AUC is near 0.5 when there is no predictive signal."""
    np.random.seed(42)
    n_samples = 200
    X = np.random.randn(n_samples, 50)
    y = np.random.randint(0, 2, n_samples) # Random noise
    
    calculator = LassoAUCCalculator(X, y, n_folds=5)
    auc = calculator.calculate_cross_validated_auc()
    
    # With random labels, AUC should be close to 0.5
    assert 0.4 <= auc <= 0.6, f"No signal should yield AUC near 0.5, got {auc}"


def test_lasso_auc_small_sample_error():
    """Test that an error is raised if sample size is too small for folds."""
    np.random.seed(42)
    X = np.random.randn(10, 5)
    y = np.random.randint(0, 2, 10)
    
    calculator = LassoAUCCalculator(X, y, n_folds=20)
    
    with pytest.raises(ValueError, match="Sample size too small"):
        calculator.calculate_cross_validated_auc()


def test_lasso_auc_imbalanced_classes():
    """Test that the calculator handles imbalanced classes without crashing."""
    np.random.seed(42)
    n_samples = 200
    X = np.random.randn(n_samples, 10)
    # 90% class 0, 10% class 1
    y = np.array([0]*180 + [1]*20)
    
    calculator = LassoAUCCalculator(X, y, n_folds=5)
    auc = calculator.calculate_cross_validated_auc()
    
    assert isinstance(auc, float), "AUC should be a float even with imbalanced data"
    assert 0.0 <= auc <= 1.0, f"AUC {auc} must be between 0 and 1"
