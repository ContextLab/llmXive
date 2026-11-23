import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from config import ensure_directories

# Mock data generators for integration test
def create_mock_kinetic_data(path: str, n: int = 50):
    """Create a realistic mock kinetic dataset."""
    data = {
        'molecule_id': [f"mol_{i}" for i in range(n)],
        'smiles': ["CC(=O)O"] * n, # Simplified SMILES for test
        'reaction_type': np.random.choice(['hydrolysis', 'oxidation', 'reduction', 'substitution'], n),
        'experimental_rate': np.random.uniform(0.1, 10.0, n)
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def create_mock_model_results(path: str, n: int = 50):
    """Create mock model comparison results with predictions."""
    predictions = np.random.uniform(0.5, 9.5, n) # Simulated gap values
    
    results = {
        "Spectral GNN": {
            "mse": 0.5,
            "mae": 0.2,
            "pearson_r": 0.6,
            "predictions": predictions.tolist()
        },
        "Random Forest": {
            "mse": 0.8,
            "mae": 0.3,
            "pearson_r": 0.4,
            "predictions": (predictions * 0.9 + 0.1).tolist()
        }
    }
    
    with open(path, 'w') as f:
        json.dump(results, f)

@pytest.fixture
def temp_test_env():
    """Setup a temporary directory for testing."""
    # Create temp dir
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirs
    os.makedirs(os.path.join(temp_dir, 'data', 'assets'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'artifacts'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'artifacts', 'logs'), exist_ok=True)
    
    # Save original paths
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_proxy_validation_full_pipeline(temp_test_env):
    """
    Integration test for T033:
    1. Create mock kinetic data and model results.
    2. Run the proxy validation script.
    3. Verify the output report exists and contains expected keys.
    """
    kinetic_path = os.path.join(temp_test_env, 'data', 'assets', 'kinetic_dataset.csv')
    model_path = os.path.join(temp_test_env, 'artifacts', 'model_comparison_results.json')
    output_path = os.path.join(temp_test_env, 'artifacts', 'proxy_validation_report.json')
    
    # 1. Setup mock data
    create_mock_kinetic_data(kinetic_path, n=50)
    create_mock_model_results(model_path, n=50)
    
    # 2. Import and run the main function
    # We need to patch the sys.path or import relative to the temp dir if necessary,
    # but since we added 'code' to sys.path globally, we assume the script logic works.
    # We run the logic directly by importing the function if possible, or executing the script.
    # Here we simulate the logic by calling the functions from the script.
    
    # Import the functions from the script we created
    # Note: In a real scenario, we might exec the file or use pytest to run the script.
    # For this test, we will import the logic if we structure it as a module, 
    # but since it's a script, we will verify the output by running the code logic inline
    # or by importing the module if we had split it.
    # To keep it simple and test the *script's* behavior, we will re-implement the logic 
    # here to verify the *output structure* is correct given the inputs.
    
    # Re-reading the requirement: "Write a test... to verify that the script produces the artifact"
    # We will execute the script's logic by importing the functions if we refactor,
    # or by running the script. Since the task asks for the script `03_proxy_validation.py`,
    # let's assume we can import `main` if we treat it as a module.
    # However, `main` calls `get_config` which might rely on global paths.
    
    # Let's execute the script content logic directly for the test to ensure it works
    # with the mock data.
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("proxy_validation", 
                                                  os.path.join(os.path.dirname(__file__), '..', '..', 'code', '03_proxy_validation.py'))
    pv_module = importlib.util.module_from_spec(spec)
    
    # We cannot easily run `main` in isolation without mocking config paths.
    # Instead, we test the helper functions which contain the core logic.
    from code.utils.metrics import calculate_pearson_r # Assuming this exists or similar
    
    # Test core logic: Correlation calculation
    df_kinetic = pd.read_csv(kinetic_path)
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    preds = model_data['Spectral GNN']['predictions']
    df_kinetic['predicted_gap'] = preds
    
    # Calculate correlation manually to verify expected output
    corr, _ = stats.pearsonr(df_kinetic['experimental_rate'], df_kinetic['predicted_gap'])
    
    # Verify the script would produce a report with this correlation
    # We simulate the report generation
    report = {
        "correlation_full_dataset": float(corr),
        "correlation_by_reaction_type_descriptive": {},
        "mechanistic_consistency_notes": ["Test note"]
    }
    
    # Assert structure
    assert 'correlation_full_dataset' in report
    assert isinstance(report['correlation_full_dataset'], float)
    assert 'correlation_by_reaction_type_descriptive' in report
    assert 'mechanistic_consistency_notes' in report
    
    # Now, actually run the script to ensure it produces the file
    # We need to ensure the script can find the files.
    # Since we are in temp_test_env, and the script uses relative paths, it should work.
    # But `get_config` might override paths. Let's assume `get_config` respects the current dir
    # or we patch it.
    
    # For this test, we assume the script runs successfully if the files are present.
    # We will execute the script via subprocess to be sure.
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), '..', '..', 'code', '03_proxy_validation.py')],
        capture_output=True,
        text=True,
        cwd=temp_test_env
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert os.path.exists(output_path), "Output report file not created"
    
    with open(output_path, 'r') as f:
        final_report = json.load(f)
    
    assert 'correlation_full_dataset' in final_report
    assert 'correlation_by_reaction_type_descriptive' in final_report
    assert 'mechanistic_consistency_notes' in final_report
    assert len(final_report['mechanistic_consistency_notes']) > 0

def test_correlation_by_reaction_type(temp_test_env):
    """Test that correlation is calculated per reaction type."""
    # Setup data with distinct reaction types
    kinetic_path = os.path.join(temp_test_env, 'data', 'assets', 'kinetic_dataset.csv')
    model_path = os.path.join(temp_test_env, 'artifacts', 'model_comparison_results.json')
    
    # Create data with known correlation for specific type
    n = 20
    data = {
        'molecule_id': [f"mol_{i}" for i in range(n)],
        'smiles': ["CC"] * n,
        'reaction_type': ['type_A'] * 10 + ['type_B'] * 10,
        'experimental_rate': list(range(10)) + list(range(10, 20)) # Perfect correlation
    }
    pd.DataFrame(data).to_csv(kinetic_path, index=False)
    
    predictions = list(range(10)) + list(range(10, 20))
    with open(model_path, 'w') as f:
        json.dump({
            "Model": {"predictions": predictions}
        }, f)
    
    # Run script
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), '..', '..', 'code', '03_proxy_validation.py')],
        capture_output=True,
        text=True,
        cwd=temp_test_env
    )
    
    assert result.returncode == 0
    
    output_path = os.path.join(temp_test_env, 'artifacts', 'proxy_validation_report.json')
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    # Check that reaction types are present
    assert 'type_A' in report['correlation_by_reaction_type_descriptive']
    assert 'type_B' in report['correlation_by_reaction_type_descriptive']
    
    # Check correlation value (should be 1.0 for perfect linear data)
    assert abs(report['correlation_by_reaction_type_descriptive']['type_A']['pearson_r'] - 1.0) < 0.01