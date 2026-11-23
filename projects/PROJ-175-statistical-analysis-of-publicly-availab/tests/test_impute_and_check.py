import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import shutil

# Mock the necessary files for testing
@pytest.fixture
def setup_test_environment():
    # Create temporary directories
    test_dir = tempfile.mkdtemp()
    data_dir = Path(test_dir) / "data"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    processed_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)
    
    # Create mock amendment_log.json
    amendment_data = {
        "status": "RATIFIED",
        "methodology": "Correlational Analysis",
        "proxy_source": "Recipe1M"
    }
    with open(data_dir / "amendment_log.json", 'w') as f:
        json.dump(amendment_data, f)
    
    # Create mock similarity file (embedding)
    sim_df = pd.DataFrame({
        'ingredient_id': ['A', 'B', 'C'],
        'ingredient_id_2': ['B', 'C', 'A'],
        'flavor_similarity': [0.8, 0.5, None] # One missing
    })
    sim_df.to_parquet(processed_dir / "similarity_scores_embedding.parquet")
    
    # Create mock co-occurrence / functional roles file (pairs)
    pairs_df = pd.DataFrame({
        'ingredient_id': ['A', 'B', 'C', 'D'],
        'ingredient_id_2': ['B', 'C', 'A', 'E'],
        'log_co_occurrence': [10.0, 5.0, 8.0, None], # One missing
        'functional_role': ['primary', 'secondary', 'primary', None] # One missing role
    })
    pairs_df.to_parquet(processed_dir / "functional_roles_validated.parquet")
    
    yield test_dir, processed_dir, logs_dir, data_dir
    
    # Cleanup
    shutil.rmtree(test_dir)

def test_impute_missing(setup_test_environment):
    test_dir, processed_dir, logs_dir, data_dir = setup_test_environment
    
    # Change to test directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        from code.data.impute_and_check import impute_missing, load_processed_data, save_output, ensure_directories
        
        # Load data
        df = load_processed_data()
        
        # Check initial state
        assert df['flavor_similarity'].isnull().sum() > 0, "Test setup failed: no missing similarity"
        assert df['log_co_occurrence'].isnull().sum() > 0, "Test setup failed: no missing co-occurrence"
        assert df['functional_role'].isnull().sum() > 0, "Test setup failed: no missing role"
        
        # Impute
        df_imputed, log_data = impute_missing(df)
        
        # Check imputation
        assert df_imputed['flavor_similarity'].isnull().sum() == 0, "Similarity not imputed"
        assert (df_imputed['flavor_similarity'] == 0).sum() > 0, "Missing similarity not filled with 0"
        
        # Check exclusions
        assert 'exclusion_counts' in log_data
        assert log_data['exclusion_counts'].get('missing_functional_role', 0) > 0, "Rows with missing role not dropped"
        assert log_data['exclusion_counts'].get('missing_co_occurrence', 0) > 0, "Rows with missing co-occurrence not dropped"
        
        # Verify file saving
        output_dir, log_dir = ensure_directories()
        save_output(df_imputed, log_data, output_dir, log_dir)
        
        assert (output_dir / "ingredient_pairs.csv").exists(), "Output CSV not created"
        assert (log_dir / "imputation_log.json").exists(), "Log JSON not created"
        
    finally:
        os.chdir(original_cwd)

def test_amendment_log_validation(setup_test_environment):
    test_dir, processed_dir, logs_dir, data_dir = setup_test_environment
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # Change methodology to Causal
        amendment_data = {
            "status": "RATIFIED",
            "methodology": "Causal Independence",
            "proxy_source": "FlavorDB"
        }
        with open(data_dir / "amendment_log.json", 'w') as f:
            json.dump(amendment_data, f)
        
        # Create mock chemical similarity file
        sim_df = pd.DataFrame({
            'ingredient_id': ['A', 'B'],
            'ingredient_id_2': ['B', 'C'],
            'flavor_similarity': [0.9, 0.4]
        })
        sim_df.to_parquet(processed_dir / "similarity_scores_chemical.parquet")
        
        from code.data.impute_and_check import load_processed_data
        
        # Should load chemical file now
        df = load_processed_data()
        assert df is not None
        
    finally:
        os.chdir(original_cwd)
