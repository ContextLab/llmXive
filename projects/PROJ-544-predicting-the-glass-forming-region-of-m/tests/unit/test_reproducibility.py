"""
Unit test for reproducibility check (3 runs, same seed).

This test verifies that running the descriptor computation pipeline 
three times with the same random seed produces identical outputs.

Task: T024 [US3] Unit test for reproducibility check (3 runs, same seed)
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors.compute import compute_descriptors, parse_composition, safe_get_atomic_radius, safe_get_electronegativity, safe_get_binary_mixing_enthalpy
from descriptors.utils import get_periodic_table
from descriptors.vif_report import calculate_vif, load_descriptors
from models.importance import compute_permutation_importance
from models.train import train_and_evaluate

# Constants for reproducibility testing
NUM_RUNS = 3
RANDOM_SEED = 42
TOLERANCE = 1e-10  # Floating point comparison tolerance

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """Compute SHA-256 hash of a DataFrame's content."""
    # Convert to string representation for hashing
    content = df.to_csv(index=False).encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def run_descriptor_pipeline(seed: int, temp_dir: Path) -> Path:
    """Run the descriptor computation pipeline."""
    # Set seeds for reproducibility
    np.random.seed(seed)
    
    # Create a small synthetic dataset for testing
    # In a real scenario, this would load from data/derived/
    compositions = [
        "Cu50Zr50",
        "Cu60Zr40",
        "Cu40Zr60",
        "Zr50Cu50",
        "Cu33.3Zr33.3Hf33.3"
    ]
    
    df = pd.DataFrame({
        'composition': compositions,
        'phase_label': ['glass', 'glass', 'crystalline', 'glass', 'crystalline']
    })
    
    # Parse compositions and compute descriptors
    parsed_compositions = [parse_composition(comp) for comp in compositions]
    
    descriptors = []
    for comp in parsed_compositions:
        try:
            desc = compute_descriptors(comp)
            descriptors.append({
                'atomic_size_mismatch': desc['atomic_size_mismatch'],
                'mixing_enthalpy': desc['mixing_enthalpy'],
                'electronegativity_variance': desc['electronegativity_variance']
            })
        except Exception as e:
            # Log error but continue
            descriptors.append({
                'atomic_size_mismatch': np.nan,
                'mixing_enthalpy': np.nan,
                'electronegativity_variance': np.nan
            })
    
    descriptor_df = pd.DataFrame(descriptors)
    
    # Save to temp directory
    output_path = temp_dir / f"descriptors_seed{seed}.csv"
    descriptor_df.to_csv(output_path, index=False)
    
    return output_path

def run_vif_analysis(seed: int, temp_dir: Path, descriptor_path: Path) -> Path:
    """Run VIF analysis on descriptors."""
    np.random.seed(seed)
    
    # Load descriptors
    df = pd.read_csv(descriptor_path)
    
    # Calculate VIF
    vif_scores = calculate_vif(df)
    
    # Save VIF report
    output_path = temp_dir / f"vif_report_seed{seed}.json"
    import json
    with open(output_path, 'w') as f:
        json.dump({
            'vif_scores': {k: float(v) for k, v in vif_scores.items()},
            'seed': seed
        }, f, indent=2)
    
    return output_path

def run_model_training(seed: int, temp_dir: Path, descriptor_path: Path) -> Path:
    """Run model training and save metrics."""
    np.random.seed(seed)
    
    # Load descriptors and labels
    df = pd.read_csv(descriptor_path)
    
    # Create a simple test dataset
    X = df[['atomic_size_mismatch', 'mixing_enthalpy', 'electronegativity_variance']].fillna(0)
    y = pd.Series([1, 1, 0, 1, 0])  # 1=glass, 0=crystalline
    
    # Train a simple model
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    
    model = RandomForestClassifier(
        n_estimators=10,
        random_state=seed,
        max_depth=3
    )
    
    scores = cross_val_score(model, X, y, cv=3)
    
    # Save metrics
    output_path = temp_dir / f"model_metrics_seed{seed}.json"
    import json
    with open(output_path, 'w') as f:
        json.dump({
            'mean_auc': float(np.mean(scores)),
            'std_auc': float(np.std(scores)),
            'seed': seed
        }, f, indent=2)
    
    return output_path

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for reproducibility tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_descriptor_reproducibility(temp_workspace):
    """Test that descriptor computation is reproducible across 3 runs."""
    hashes = []
    
    for i in range(NUM_RUNS):
        np.random.seed(RANDOM_SEED)  # Reset seed for each run
        output_path = run_descriptor_pipeline(RANDOM_SEED, temp_workspace)
        file_hash = compute_file_hash(output_path)
        hashes.append(file_hash)
    
    # All hashes should be identical
    assert len(set(hashes)) == 1, f"Descriptor hashes differ across runs: {hashes}"

def test_vif_reproducibility(temp_workspace):
    """Test that VIF analysis is reproducible across 3 runs."""
    # First run descriptor pipeline
    np.random.seed(RANDOM_SEED)
    descriptor_path = run_descriptor_pipeline(RANDOM_SEED, temp_workspace)
    
    hashes = []
    
    for i in range(NUM_RUNS):
        np.random.seed(RANDOM_SEED)  # Reset seed for each run
        output_path = run_vif_analysis(RANDOM_SEED, temp_workspace, descriptor_path)
        file_hash = compute_file_hash(output_path)
        hashes.append(file_hash)
    
    # All hashes should be identical
    assert len(set(hashes)) == 1, f"VIF report hashes differ across runs: {hashes}"

def test_model_training_reproducibility(temp_workspace):
    """Test that model training metrics are reproducible across 3 runs."""
    # First run descriptor and VIF pipelines
    np.random.seed(RANDOM_SEED)
    descriptor_path = run_descriptor_pipeline(RANDOM_SEED, temp_workspace)
    run_vif_analysis(RANDOM_SEED, temp_workspace, descriptor_path)
    
    hashes = []
    
    for i in range(NUM_RUNS):
        np.random.seed(RANDOM_SEED)  # Reset seed for each run
        output_path = run_model_training(RANDOM_SEED, temp_workspace, descriptor_path)
        file_hash = compute_file_hash(output_path)
        hashes.append(file_hash)
    
    # All hashes should be identical
    assert len(set(hashes)) == 1, f"Model metrics hashes differ across runs: {hashes}"

def test_full_pipeline_reproducibility(temp_workspace):
    """Test full pipeline reproducibility (descriptors -> VIF -> model)."""
    all_hashes = []
    
    for i in range(NUM_RUNS):
        np.random.seed(RANDOM_SEED)  # Reset seed for each run
        
        # Run full pipeline
        descriptor_path = run_descriptor_pipeline(RANDOM_SEED, temp_workspace)
        vif_path = run_vif_analysis(RANDOM_SEED, temp_workspace, descriptor_path)
        model_path = run_model_training(RANDOM_SEED, temp_workspace, descriptor_path)
        
        # Compute combined hash
        combined_hash = ""
        for path in [descriptor_path, vif_path, model_path]:
            combined_hash += compute_file_hash(path)
        
        all_hashes.append(hashlib.sha256(combined_hash.encode()).hexdigest())
    
    # All combined hashes should be identical
    assert len(set(all_hashes)) == 1, f"Full pipeline hashes differ across runs: {all_hashes}"

def test_seed_consistency_across_runs():
    """Verify that using the same seed produces consistent results."""
    results = []
    
    for i in range(NUM_RUNS):
        np.random.seed(RANDOM_SEED)
        
        # Generate a random number to verify seed consistency
        random_val = np.random.random()
        results.append(random_val)
    
    # All values should be identical
    assert len(set(results)) == 1, f"Random values differ with same seed: {results}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
