"""
Helper utilities for test data generation and validation.
(Optional artifact to support the integration tests if needed, 
though most logic is inline in test_preprocessing.py)
"""
import numpy as np
import pandas as pd

def generate_test_merged_data(n_samples=1000, seed=42):
    """
    Generate a synthetic merged dataset similar to the output of 01_data_ingestion.py.
    Used for unit/integration testing without real data dependencies.
    """
    np.random.seed(seed)
    data = {
        'participant_id': [f"P{i:04d}" for i in range(n_samples)],
        'age': np.random.randint(40, 90, size=n_samples),
        'bmi': np.random.normal(27, 5, size=n_samples),
        'education_years': np.random.randint(8, 20, size=n_samples),
        'cognitive_score': np.random.normal(50, 10, size=n_samples),
    }
    
    # Introduce missing values
    bmi_missing_idx = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
    data['bmi'] = pd.Series(data['bmi']).astype(float)
    data['bmi'].iloc[bmi_missing_idx] = np.nan
    
    edu_missing_idx = np.random.choice(n_samples, size=int(n_samples * 0.03), replace=False)
    data['education_years'] = pd.Series(data['education_years']).astype(float)
    data['education_years'].iloc[edu_missing_idx] = np.nan
    
    # Add genera
    for i in range(5):
        data[f'genus_{chr(65+i)}'] = np.random.dirichlet(np.ones(5), size=n_samples)[:, 0]
        
    return pd.DataFrame(data)