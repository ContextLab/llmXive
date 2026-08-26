"""
Integration test for T028: Save best model artifacts and hyperparameters.

This test verifies that the `save_models.py` script successfully:
1. Loads the processed data and split indices.
2. Trains the models (or loads pre-trained ones if refactored).
3. Writes the expected artifacts to `data/results/best_models/`.
4. Validates the schema of the saved artifacts.
"""
import json
import os
import pickle
from pathlib import Path

import pytest
import pandas as pd

import config
from utils.io import load_parquet, save_parquet
from preprocessing.sanitize import sanitize_reactions
from preprocessing.fingerprints import generate_fingerprints_batch
from preprocessing.scaffold import generate_scaffold_groups
from modeling.split import create_train_val_test_split, extract_validation_set
from modeling.train import train_random_forest_grid_search, train_svm_grid_search
from modeling.save_models import main as save_models_main

# Path constants
PROCESSED_DIR = Path(config.PROCESSED_DIR)
RESULTS_DIR = Path(config.OUTPUT_DIR)
BEST_MODELS_DIR = RESULTS_DIR / "best_models"

@pytest.fixture(scope="module")
def setup_test_data(tmp_path_factory):
    """
    Setup a minimal dataset for integration testing.
    Since we cannot rely on the full USPTO download in a quick test,
    we create a synthetic but structurally valid dataset that mimics the
    expected schema from T017/T010.
    
    NOTE: In a real CI environment, this would use the real data from T017.
    For this specific test task T028, we assume the pipeline up to T027 is functional.
    We will mock the data creation to ensure the save logic works.
    """
    # Create directories
    tmp_dir = tmp_path_factory.mktemp("test_save_models")
    data_dir = tmp_dir / "data"
    raw_dir = data_dir / "raw"
    proc_dir = data_dir / "processed"
    res_dir = data_dir / "results"
    raw_dir.mkdir(parents=True)
    proc_dir.mkdir(parents=True)
    res_dir.mkdir(parents=True)
    
    # Create a minimal synthetic dataset
    # We need: SMILES, yield, and generated fingerprints
    import numpy as np
    from rdkit import Chem
    from rdkit.Chem import AllChem, MACCSkeys
    
    n_samples = 50
    smiles_list = [
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C",
        "CCO", "CC(=O)O", "c1ccccc1", "CC1=CC=CC=C1", "CC(C)C"
    ] * 5 # Repeat to get 50
    
    # Generate fake yields
    yields = np.random.uniform(0, 100, n_samples)
    
    # Generate fingerprints
    ecfp4_list = []
    maccs_list = []
    
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            mol = Chem.MolFromSmiles("CCO") # Fallback
        
        # ECFP4 (2048 bits)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        arr = np.zeros((2048,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        ecfp4_list.append(arr)
        
        # MACCS (167 bits)
        mfp = MACCSkeys.GenMACCSKeys(mol)
        marr = np.zeros((167,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(mfp, marr)
        maccs_list.append(marr)
    
    df = pd.DataFrame({
        "smiles": smiles_list,
        "yield": yields,
        "fingerprint_ecfp4": ecfp4_list,
        "fingerprint_maccs": maccs_list
    })
    
    # Save processed data
    proc_file = proc_dir / "cleaned_reactions.parquet"
    df.to_parquet(proc_file)
    
    # Create scaffold groups (mock)
    df["scaffold_group"] = "default_scaffold"
    scaffold_file = proc_dir / "scaffold_groups.parquet"
    df.to_parquet(scaffold_file)
    
    # Create split indices
    # Simple random split for test
    indices = list(range(n_samples))
    np.random.seed(42)
    np.random.shuffle(indices)
    train_end = int(0.6 * n_samples)
    val_end = int(0.8 * n_samples)
    
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]
    
    split_data = []
    for i in train_idx:
        split_data.append({"index": i, "split": "train"})
    for i in val_idx:
        split_data.append({"index": i, "split": "val"})
    for i in test_idx:
        split_data.append({"index": i, "split": "test"})
        
    split_df = pd.DataFrame(split_data)
    split_file = proc_dir / "split_indices.parquet"
    split_df.to_parquet(split_file)
    
    # Override config paths for this test
    original_processed = config.PROCESSED_DIR
    original_output = config.OUTPUT_DIR
    
    config.PROCESSED_DIR = str(proc_dir)
    config.OUTPUT_DIR = str(res_dir)
    
    yield proc_dir, res_dir, split_file
    
    # Restore config
    config.PROCESSED_DIR = original_processed
    config.OUTPUT_DIR = original_output

def test_save_models_integration(setup_test_data):
    """
    Test that save_models.py runs and produces the expected artifacts.
    """
    proc_dir, res_dir, split_file = setup_test_data
    
    # Ensure the best_models directory doesn't exist yet (clean state)
    best_models_dir = res_dir / "best_models"
    if best_models_dir.exists():
        import shutil
        shutil.rmtree(best_models_dir)
    
    # Run the main function
    # Note: This might take a moment due to grid search, but with small data it should be fast.
    try:
        save_models_main()
    except Exception as e:
        pytest.fail(f"save_models_main() raised an exception: {e}")
    
    # Verify artifacts exist
    expected_files = [
        "random_forest_model.pkl",
        "random_forest_hyperparameters.json",
        "svm_model.pkl",
        "svm_hyperparameters.json",
        "model_registry.json"
    ]
    
    for filename in expected_files:
        filepath = best_models_dir / filename
        assert filepath.exists(), f"Expected artifact {filename} not found at {filepath}"
    
    # Validate content of hyperparameters JSON
    rf_hyper_path = best_models_dir / "random_forest_hyperparameters.json"
    with open(rf_hyper_path, "r") as f:
        rf_params = json.load(f)
    assert "n_estimators" in rf_params, "n_estimators missing in RF hyperparameters"
    assert "max_depth" in rf_params, "max_depth missing in RF hyperparameters"
    
    # Validate model pickle can be loaded
    rf_model_path = best_models_dir / "random_forest_model.pkl"
    with open(rf_model_path, "rb") as f:
        rf_model = pickle.load(f)
    assert hasattr(rf_model, "predict"), "Loaded object is not a valid model"
    
    # Validate registry JSON
    registry_path = best_models_dir / "model_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)
    assert "models" in registry, "models key missing in registry"
    assert "random_forest" in registry["models"], "random_forest missing in registry"
    assert "svm" in registry["models"], "svm missing in registry"