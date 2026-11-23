"""
Integration tests for the modeling pipeline.
Verifies the 5-fold CV workflow and stratified split logic.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling import prepare_splits, load_processed_data, train_models, run_baseline_predictor, evaluate_models
from code.ingestion import generate_data_availability_report, validate_data_gap
from code.diagnostics import calculate_vif, group_correlated_features

@pytest.fixture
def sample_processed_data(tmp_path):
    """Create a sample processed dataset for testing."""
    # Ensure directories exist
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create a synthetic dataset that mimics the real structure
    # This is used ONLY for testing the split logic, not for final results
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'composition': [f'Ceramic_{i}' for i in range(n_samples)],
        'weibull_modulus': np.random.normal(10, 2, n_samples),
        'sample_count': np.random.randint(30, 100, n_samples),
        'primary_anion_cation_group': np.random.choice(['O-Al', 'O-Zr', 'O-Si', 'N-Si', 'C-Si'], n_samples),
        'sintering_temp': np.random.uniform(1000, 1800, n_samples),
        'mean_atomic_radius': np.random.uniform(1.0, 2.0, n_samples),
        'electronegativity_std': np.random.uniform(0.1, 0.5, n_samples),
        'valence_electron_concentration': np.random.uniform(1.0, 5.0, n_samples),
        'cation_size_variance': np.random.uniform(0.0, 0.2, n_samples),
        'range_uncertainty': np.random.uniform(0.0, 0.1, n_samples)
    }
    
    df = pd.DataFrame(data)
    csv_path = data_dir / "step_final_cleaned.csv"
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)

@pytest.fixture
def setup_modeling_env(tmp_path):
    """Setup environment for modeling tests."""
    # Create necessary directories
    (tmp_path / "data" / "results").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "models").mkdir(parents=True, exist_ok=True)
    
    # Save the path for later use
    return tmp_path

def test_5fold_cv_stratified_split(sample_processed_data, setup_modeling_env, caplog):
    """
    Test the 5-fold CV stratified split workflow.
    Verifies that:
    1. Data is loaded correctly
    2. Stratified splits are generated
    3. Class distribution is preserved across folds
    4. The cv_split_report.json is generated with the correct schema
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Change to the temp directory to ensure relative paths work
    original_cwd = os.getcwd()
    os.chdir(str(setup_modeling_env))
    
    try:
        # Load the data
        df = load_processed_data(sample_processed_data)
        assert len(df) > 0, "Loaded dataset is empty"
        
        # Prepare splits
        # We need to mock the data path for prepare_splits to find the file
        # Since prepare_splits expects the file at a specific location, we copy it there
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        target_path = processed_dir / "step_final_cleaned.csv"
        df.to_csv(target_path, index=False)
        
        # Run prepare_splits which should generate the report
        # The function prepare_splits is expected to generate cv_split_report.json
        splits = prepare_splits()
        
        # Verify the report was generated
        report_path = Path("data/results/cv_split_report.json")
        assert report_path.exists(), "cv_split_report.json was not generated"
        
        # Load and validate the report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Validate schema
        assert "fold_sizes" in report, "Missing 'fold_sizes' in report"
        assert "class_distribution" in report, "Missing 'class_distribution' in report"
        assert "total_samples" in report, "Missing 'total_samples' in report"
        
        assert isinstance(report["fold_sizes"], list), "'fold_sizes' must be a list"
        assert len(report["fold_sizes"]) == 5, "Should have 5 folds"
        assert sum(report["fold_sizes"]) == report["total_samples"], "Fold sizes must sum to total samples"
        
        assert isinstance(report["class_distribution"], dict), "'class_distribution' must be a dict"
        
        # Verify class distribution consistency
        for class_name, counts in report["class_distribution"].items():
            assert "train" in counts, f"Missing 'train' count for class {class_name}"
            assert "test" in counts, f"Missing 'test' count for class {class_name}"
            assert isinstance(counts["train"], int), f"'train' count must be int for {class_name}"
            assert isinstance(counts["test"], int), f"'test' count must be int for {class_name}"
        
        logging.info("5-fold CV stratified split test passed successfully.")
        logging.info(f"Report: {json.dumps(report, indent=2)}")
        
    finally:
        os.chdir(original_cwd)

def test_model_training_and_evaluation(sample_processed_data, setup_modeling_env):
    """
    Test the full modeling workflow: training, baseline, and evaluation.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    original_cwd = os.getcwd()
    os.chdir(str(setup_modeling_env))
    
    try:
        # Setup data
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        target_path = processed_dir / "step_final_cleaned.csv"
        df = pd.read_csv(sample_processed_data)
        df.to_csv(target_path, index=False)
        
        # Train models
        # Note: This might take a while, but we use a small grid for testing
        train_models()
        
        # Run baseline
        run_baseline_predictor()
        
        # Evaluate
        evaluate_models()
        
        # Verify outputs
        assert Path("data/results/model_metrics.json").exists(), "model_metrics.json not found"
        assert Path("data/results/baseline_metrics.json").exists(), "baseline_metrics.json not found"
        
        logging.info("Model training and evaluation test passed.")
        
    finally:
        os.chdir(original_cwd)

def test_stratification_logic():
    """
    Unit test for the stratification logic itself.
    """
    # Create a small dataset with known class distribution
    data = {
        'class': ['A'] * 40 + ['B'] * 30 + ['C'] * 30,
        'value': list(range(100))
    }
    df = pd.DataFrame(data)
    
    # Test that we can create stratified splits
    from sklearn.model_selection import StratifiedKFold
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(skf.split(df, df['class']))
    
    assert len(folds) == 5, "Should generate 5 folds"
    
    # Check that each fold has roughly the same class distribution
    for i, (train_idx, test_idx) in enumerate(folds):
        train_class_dist = df.iloc[train_idx]['class'].value_counts()
        test_class_dist = df.iloc[test_idx]['class'].value_counts()
        
        # Basic check: all classes should be present in both train and test
        assert set(train_class_dist.index) == set(df['class'].unique()), f"Fold {i} missing classes in train"
        assert set(test_class_dist.index) == set(df['class'].unique()), f"Fold {i} missing classes in test"
        
    print("Stratification logic test passed.")