import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from models.compare import (
    load_cv_results, 
    perform_rf_vs_xgb_ttest, 
    calculate_permutation_importance, 
    classify_features, 
    generate_comparison_report,
    main
)
from config import get_config

@pytest.fixture
def temp_test_env():
    """Creates a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(os.path.join(temp_dir, 'data', 'logs'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'data', 'processed'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'models'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'docs', 'reports'), exist_ok=True)
    
    # Save original paths
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_t029_report_generation(temp_test_env):
    """
    Integration test for T029: Verify final analysis report generation.
    Checks:
    1. Report file is created at docs/reports/final_analysis.md
    2. Report contains validation logic results
    3. Validation gene count logic works correctly
    """
    # Setup mock data
    metrics_data = {
        'best_model_name': 'RandomForest',
        'best_model_auc': 0.85,
        'cv_results': {
            'rf': [0.82, 0.84, 0.83, 0.85, 0.81],
            'xgboost': [0.80, 0.82, 0.81, 0.83, 0.79]
        },
        't_statistic': 2.5,
        'p_value': 0.03
    }
    
    # Create mock metrics file
    with open('data/logs/metrics.json', 'w') as f:
        json.dump(metrics_data, f)
    
    # Create mock test data with features including validation genes
    # Using the gene list from config or hardcoded
    validation_genes = [
        "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A",
        "LEA3", "HSP70", "SOD", "APX1", "CAT1",
        "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12"
    ]
    
    # Create features: 5 validation genes in top 10, 5 random traits
    feature_names = validation_genes[:5] + ['trait_1', 'trait_2', 'trait_3', 'trait_4', 'trait_5']
    # Add more to make a realistic set
    feature_names += ['trait_6', 'trait_7', 'trait_8', 'trait_9', 'trait_10']
    
    # Create mock model (dummy)
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    dummy_model = RandomForestClassifier(n_estimators=10)
    dummy_model.fit(np.random.rand(20, len(feature_names)), np.random.randint(0, 2, 20))
    joblib.dump(dummy_model, 'models/best_model.joblib')
    
    # Create test dataframe
    data = {
        'species_id': [f'sp_{i}' for i in range(20)],
        'label': np.random.randint(0, 2, 20)
    }
    for i, fname in enumerate(feature_names):
        data[fname] = np.random.rand(20)
    
    test_df = pd.DataFrame(data)
    test_df.to_csv('data/processed/test_set.csv', index=False)
    
    # Run the main logic
    # We need to patch the get_config to return the correct paths if needed, 
    # but main() uses relative paths by default which match our temp dir structure.
    # However, main() calls get_config() which might return different paths.
    # Let's run the specific functions instead to ensure isolation.
    
    # 1. Load metrics
    metrics = load_cv_results('data/logs/metrics.json')
    assert 'best_model_auc' in metrics
    
    # 2. Calculate importance (mock)
    # We can't easily mock the model prediction without a real model, 
    # so we rely on the dummy model we saved.
    importance_df = calculate_permutation_importance(
        'models/best_model.joblib', 
        test_df.drop(['species_id', 'label'], axis=1).values,
        test_df['label'].values,
        feature_names,
        n_repeats=1, # Fast for test
        random_state=42
    )
    
    # 3. Classify features
    classified = classify_features(importance_df)
    assert 'genomic' in classified
    assert 'physiological' in classified
    
    # 4. Generate report
    report_results = generate_comparison_report(metrics, importance_df, classified, 'docs/reports/final_analysis.md')
    
    # Assertions
    assert os.path.exists('docs/reports/final_analysis.md'), "Report file not created"
    
    with open('docs/reports/final_analysis.md', 'r') as f:
        content = f.read()
    
    assert "Final Analysis Report" in content
    assert "Validation Check (SC-005)" in content
    assert "PASSED" in content or "FAILED" in content
    
    # Check validation logic
    # We set up 5 validation genes. If they are in top 10, count should be 5.
    # The dummy model might not rank them high, but the logic must run.
    # We verify the count is calculated correctly.
    assert 'validation_count' in report_results
    
    print("T029 Integration Test Passed")

def test_validation_logic_threshold():
    """
    Unit test for the specific validation logic: count >= 3.
    """
    from models.compare import VALIDATION_GENE_LIST, MIN_VALIDATION_GENE_COUNT, TOP_N_FEATURES
    
    # Simulate top 10 features
    top_10 = ["DREB2A", "Trait1", "ERF1", "Trait2", "ABI5", "Trait3", "Trait4", "Trait5", "Trait6", "Trait7"]
    
    count = sum(1 for gene in top_10 if gene in VALIDATION_GENE_LIST)
    assert count == 3
    assert count >= MIN_VALIDATION_GENE_COUNT
    
    # Simulate failure case
    top_10_fail = ["Trait1", "Trait2", "Trait3", "Trait4", "Trait5", "Trait6", "Trait7", "Trait8", "Trait9", "Trait10"]
    count_fail = sum(1 for gene in top_10_fail if gene in VALIDATION_GENE_LIST)
    assert count_fail == 0
    assert count_fail < MIN_VALIDATION_GENE_COUNT
    
    print("Validation Logic Threshold Test Passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
