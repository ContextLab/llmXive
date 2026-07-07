"""
Preprocessing module for leakage-safe imputation and scaling.

Implements:
- Leakage-safe imputation (median for numeric, mode for categorical) fitted ONLY on training folds.
- Scaler wrappers (StandardScaler) that fit on training data and transform train/test consistently.
- Integration with scikit-learn Pipeline/ColumnTransformer patterns.
"""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

from code.utils import PipelineError, log_and_reraise


class LeakageSafeImputer(BaseEstimator, TransformerMixin):
    """
    Imputes missing values using median (numeric) or mode (categorical).
    
    CRITICAL: This transformer is designed to be used within a cross-validation pipeline
    where it is fitted ONLY on the training fold to prevent data leakage.
    
    Parameters
    ----------
    strategy_numeric : str, default 'median'
        Strategy for numeric columns.
    strategy_categorical : str, default 'most_frequent' (mode)
        Strategy for categorical columns.
    """
    def __init__(self, strategy_numeric='median', strategy_categorical='most_frequent'):
        self.strategy_numeric = strategy_numeric
        self.strategy_categorical = strategy_categorical
        self.imputer_numeric = None
        self.imputer_categorical = None
        self.numeric_columns_ = None
        self.categorical_columns_ = None

    def fit(self, X, y=None):
        """Fit the imputers on the training data."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        
        self.numeric_columns_ = X.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_columns_ = X.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        if self.numeric_columns_:
            self.imputer_numeric = SimpleImputer(
                strategy=self.strategy_numeric,
                keep_empty_features=False
            )
            self.imputer_numeric.fit(X[self.numeric_columns_])

        if self.categorical_columns_:
            self.imputer_categorical = SimpleImputer(
                strategy=self.strategy_categorical,
                keep_empty_features=False
            )
            self.imputer_categorical.fit(X[self.categorical_columns_])

        return self

    def transform(self, X):
        """Transform data using fitted imputers."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        
        X_transformed = X.copy()

        if self.numeric_columns_ and self.imputer_numeric:
            # Ensure columns exist even if dropped previously
            cols = [c for c in self.numeric_columns_ if c in X_transformed.columns]
            if cols:
                imputed = self.imputer_numeric.transform(X_transformed[cols])
                X_transformed[cols] = imputed

        if self.categorical_columns_ and self.imputer_categorical:
            cols = [c for c in self.categorical_columns_ if c in X_transformed.columns]
            if cols:
                imputed = self.imputer_categorical.transform(X_transformed[cols])
                X_transformed[cols] = imputed

        return X_transformed


class LeakageSafeScaler(BaseEstimator, TransformerMixin):
    """
    Standardizes features using mean and std computed ONLY on training data.
    
    Prevents leakage by ensuring fit() is only called on training folds.
    """
    def __init__(self):
        self.scaler = StandardScaler()

    def fit(self, X, y=None):
        """Fit the scaler on training data."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        # Select only numeric columns for scaling
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            # No numeric columns to scale
            return self
        self.scaler.fit(X[numeric_cols])
        self.numeric_columns_ = numeric_cols.tolist()
        return self

    def transform(self, X):
        """Transform data using fitted scaler."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        
        X_transformed = X.copy()
        
        if hasattr(self, 'numeric_columns_') and len(self.numeric_columns_) > 0:
            cols = [c for c in self.numeric_columns_ if c in X_transformed.columns]
            if cols:
                scaled = self.scaler.transform(X_transformed[cols])
                X_transformed[cols] = scaled
        
        return X_transformed


@log_and_reraise
def create_preprocessing_pipeline(numeric_features=None, categorical_features=None):
    """
    Creates a ColumnTransformer pipeline with leakage-safe imputation and scaling.
    
    Parameters
    ----------
    numeric_features : list of str, optional
        List of numeric column names. If None, auto-detected.
    categorical_features : list of str, optional
        List of categorical column names. If None, auto-detected.
        
    Returns
    -------
    ColumnTransformer
        A preprocessor configured for the specified features.
    """
    # If feature lists not provided, return a generic preprocessor that auto-detects
    # at fit time. This is useful when the exact schema isn't known until data load.
    if numeric_features is None and categorical_features is None:
        # Create a pipeline that handles both types dynamically
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', Pipeline(steps=[
                    ('imputer', LeakageSafeImputer(strategy_numeric='median')),
                    ('scaler', LeakageSafeScaler())
                ]), slice(None)), # Will be refined in fit
                ('cat', Pipeline(steps=[
                    ('imputer', LeakageSafeImputer(strategy_categorical='most_frequent'))
                ]), slice(None))
            ],
            remainder='drop',
            sparse_output=False
        )
        # Note: The above generic approach is tricky with ColumnTransformer.
        # A better approach for unknown schemas is to use a custom transformer or
        # let the caller specify types. For this implementation, we assume the caller
        # will pass specific columns if known, or we use a simpler dynamic approach:
        
        # Dynamic approach: Create a single pipeline that handles everything
        # This is less efficient but safer for unknown schemas
        return Pipeline(steps=[
            ('imputer', LeakageSafeImputer()),
            ('scaler', LeakageSafeScaler())
        ])

    steps = []
    
    if numeric_features:
        steps.append((
            'numeric',
            Pipeline(steps=[
                ('imputer', LeakageSafeImputer(strategy_numeric='median')),
                ('scaler', LeakageSafeScaler())
            ]),
            numeric_features
        ))
    
    if categorical_features:
        steps.append((
            'categorical',
            Pipeline(steps=[
                ('imputer', LeakageSafeImputer(strategy_categorical='most_frequent'))
            ]),
            categorical_features
        ))
    
    if not steps:
        raise PipelineError("No features specified for preprocessing pipeline.")
        
    return ColumnTransformer(
        transformers=steps,
        remainder='drop',
        sparse_output=False
    )


def preprocess_data(X_train, X_test, numeric_features=None, categorical_features=None):
    """
    Fit and transform training data, transform test data using the same pipeline.
    
    This function ensures that imputation and scaling parameters are learned
    ONLY from X_train to prevent data leakage.
    
    Parameters
    ----------
    X_train : pd.DataFrame or np.ndarray
        Training features.
    X_test : pd.DataFrame or np.ndarray
        Test features.
    numeric_features : list of str, optional
        List of numeric column names.
    categorical_features : list of str, optional
        List of categorical column names.
        
    Returns
    -------
    X_train_processed : pd.DataFrame or np.ndarray
        Preprocessed training features.
    X_test_processed : pd.DataFrame or np.ndarray
        Preprocessed test features.
    """
    # Convert to DataFrame if numpy array
    if not isinstance(X_train, pd.DataFrame):
        X_train = pd.DataFrame(X_train)
    if not isinstance(X_test, pd.DataFrame):
        X_test = pd.DataFrame(X_test)
        
    preprocessor = create_preprocessing_pipeline(numeric_features, categorical_features)
    
    # Fit on training data only
    if isinstance(preprocessor, Pipeline):
        # Dynamic pipeline case
        preprocessor.fit(X_train)
        X_train_processed = preprocessor.transform(X_train)
        X_test_processed = preprocessor.transform(X_test)
    else:
        # ColumnTransformer case
        X_train_processed = preprocessor.fit_transform(X_train)
        X_test_processed = preprocessor.transform(X_test)
        
    return X_train_processed, X_test_processed
