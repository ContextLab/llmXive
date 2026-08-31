import pytest
import json
import tempfile
import os
from pathlib import Path
import pandas as pd
import yaml

from model_runner import main, run_reproducibility_assessment
from metrics import calculate_deviation_index

def test_full_pipeline(tmp_path):
    """Test the full pipeline end-to-end."""
    # Setup temporary directories
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create dummy processed data
    df = pd.DataFrame({
        'smiles': ['CCO', 'CC', 'O', 'C', 'N', 'CO', 'C=O', 'CN'],
        'yield': [0.8, 0.6, 0.9, 0.5, 0.7, 0.85, 0.75, 0.65]
    })
    data_file = data_dir / "paper1.csv"
    df.to_csv(data_file, index=False)
    
    # Create manifest
    manifest = {
        'papers': [
            {
                'id': 'paper1',
                'reported_metrics': {'mae': 0.5, 'r2': 0.8, 'spearman': 0.7},
                'seed': 42,
                'data_file': 'paper1.csv'
            }
        ]
    }
    manifest_path = tmp_path / "data" / "manifest.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)
    
    # Save original paths
    original_cwd = os.getcwd()
    original_data_dir = Path("data")
    original_manifest = Path("data/manifest.yaml")
    
    try:
        # Change to temp directory
        os.chdir(tmp_path)
        
        # Create necessary directories
        (tmp_path / "artifacts").mkdir()
        (tmp_path / "artifacts" / "reports").mkdir()
        
        # Run main
        results = main()
        
        # Check output file
        output_path = Path("artifacts/reports/repro_results.json")
        assert output_path.exists(), "Output file not created"
        
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        assert isinstance(saved_results, list)
        assert len(saved_results) == 1
        assert saved_results[0]['paper_id'] == 'paper1'
        assert saved_results[0]['status'] == 'success'
        assert 'metrics' in saved_results[0]
        assert 'sensitivity_analysis' in saved_results[0]
        
    finally:
        # Restore original state
        os.chdir(original_cwd)

def test_model_substitution_flag(tmp_path):
    """Test that model substitution is correctly flagged."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    df = pd.DataFrame({
        'smiles': ['CCO'] * 20,
        'yield': [0.8] * 20
    })
    data_file = data_dir / "paper1.csv"
    df.to_csv(data_file, index=False)
    
    manifest = {
        'papers': [
            {
                'id': 'paper1',
                'reported_metrics': {'mae': 0.5},
                'data_file': 'paper1.csv'
            }
        ]
    }
    manifest_path = tmp_path / "data" / "manifest.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)
    
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / "artifacts").mkdir()
        (tmp_path / "artifacts" / "reports").mkdir()
        
        results = main()
        
        # Check that substitution flag is present
        assert 'model_substituted' in results[0]
        
    finally:
        os.chdir(original_cwd)
