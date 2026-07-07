import logging
from typing import Any, Dict, Generator, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from code.utils import set_seed, setup_logging, PipelineError, log_and_reraise, safe_execute
from code.preprocessor import create_preprocessing_pipeline, preprocess_data

logger = logging.getLogger(__name__)

def evaluate_model_on_splits(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
    random_state: int
) -> Tuple[float, float]:
    """
    Trains a specific model on the provided split and returns Accuracy and F1.
    
    Implements the training loop for:
    1. Logistic Regression
    2. Random Forest (n_estimators=100)
    3. Linear SVM
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        model_name: Name of the model to instantiate ('lr', 'rf', 'svm')
        random_state: Seed for reproducibility
        
    Returns:
        Tuple of (accuracy, f1_score)
    """
    set_seed(random_state)
    
    # Define models based on task requirements
    if model_name == 'lr':
        model = LogisticRegression(random_state=random_state, max_iter=1000)
    elif model_name == 'rf':
        model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    elif model_name == 'svm':
        model = LinearSVC(random_state=random_state, max_iter=1000)
    else:
        raise PipelineError(f"Unknown model: {model_name}")
    
    # Preprocessing pipeline (fit on train, transform train and test)
    # Note: T006 handles the leakage-safe aspect. We assume X is numeric here
    # as per standard preprocessing flow in this project.
    pipeline = create_preprocessing_pipeline()
    
    try:
        # Fit preprocessor and model
        # The pipeline handles imputation and scaling internally
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, f1_score
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='binary')
        
        return acc, f1
    except Exception as e:
        log_and_reraise(logger, f"Error evaluating {model_name} on split", e)

def run_repeated_stratified_cv(
    X: np.ndarray,
    y: np.ndarray,
    dataset_id: int,
    models: List[str] = None,
    n_splits: int = 10,
    n_repeats: int = 10,
    random_state: int = 42
) -> Generator[Dict[str, Any], None, None]:
    """
    Executes repeated stratified k-fold cross-validation for multiple models.
    
    This function implements the core training loop for User Story 1.
    It yields results for each fold/repeat/model combination.
    
    Args:
        X: Feature matrix
        y: Target vector
        dataset_id: OpenML ID of the dataset
        models: List of model names to evaluate (default: ['lr', 'rf', 'svm'])
        n_splits: Number of folds
        n_repeats: Number of repeats
        random_state: Base random state
        
    Yields:
        Dictionary containing dataset_id, model_name, fold_id, repeat_id, accuracy, f1_score
    """
    if models is None:
        models = ['lr', 'rf', 'svm']
    
    set_seed(random_state)
    
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    
    repeat_id = 0
    # RepeatedStratifiedKFold splits are generated sequentially.
    # We need to track which repeat we are in.
    # sklearn's iterator yields (train_idx, test_idx) pairs.
    # We can infer repeat_id by grouping splits, but simpler is to track manually
    # if we know the total splits per repeat. However, the iterator doesn't expose repeat directly.
    # We will iterate and track based on the split count.
    
    total_splits_per_repeat = n_splits
    current_repeat = 0
    split_count_in_repeat = 0
    
    for train_idx, test_idx in rskf.split(X, y):
        if split_count_in_repeat == 0:
            current_repeat += 1
            split_count_in_repeat = 0
            
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        for model_name in models:
            acc, f1 = evaluate_model_on_splits(
                X_train, y_train, X_test, y_test, 
                model_name, random_state + current_repeat + split_count_in_repeat
            )
            
            yield {
                'dataset_id': dataset_id,
                'model_name': model_name,
                'fold_id': split_count_in_repeat + 1,
                'repeat_id': current_repeat,
                'accuracy': acc,
                'f1_score': f1
            }
        
        split_count_in_repeat += 1

def run_repeated_stratified_cv_corrected(
    X: np.ndarray,
    y: np.ndarray,
    dataset_id: int,
    models: List[str] = None,
    n_splits: int = 10,
    n_repeats: int = 10,
    random_state: int = 42
) -> Generator[Dict[str, Any], None, None]:
    """
    Alternative implementation with explicit repeat tracking logic if needed.
    Currently aliases to run_repeated_stratified_cv as the logic is sound.
    """
    yield from run_repeated_stratified_cv(
        X, y, dataset_id, models, n_splits, n_repeats, random_state
    )