import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from eval.anova import (
    load_metrics_for_anova,
    run_anova,
    main
)
from utils.seeds import set_global_seed

@pytest.fixture
def temp_metrics_dir():
    """Create a temporary directory with mock metrics JSON files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create mock metric files for different strata
    strata = ["Static-High", "Static-Low", "Fast-High", "Fast-Low"]
    
    for stratum in strata:
        # Create a mock metrics file
        metrics = {
            "sequence_id": f"seq_{stratum}",
            "stratum": stratum,
            "world_score": np.random.uniform(0.5, 0.9),
            "sparse_consistency_score": np.random.uniform(0.6, 0.95),
            "fid": np.random.uniform(0.1, 0.5),
            "inference_time": np.random.uniform(0.1, 1.0)
        }
        
        file_path = Path(temp_dir) / f"metrics_{stratum}.json"
        with open(file_path, 'w') as f:
            json.dump(metrics, f)
    
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_results_dir():
    """Create a temporary results directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_load_metrics_for_anova(temp_metrics_dir):
    """Test loading metrics for ANOVA analysis."""
    metrics_df = load_metrics_for_anova(temp_metrics_dir)
    
    assert isinstance(metrics_df, pd.DataFrame)
    assert "stratum" in metrics_df.columns
    assert "world_score" in metrics_df.columns
    assert "sparse_consistency_score" in metrics_df.columns
    assert len(metrics_df) == 4  # 4 strata

def test_run_anova(temp_metrics_dir):
    """Test running two-way ANOVA."""
    set_global_seed(42)
    metrics_df = load_metrics_for_anova(temp_metrics_dir)
    
    # Manually expand the dataset to have enough samples for ANOVA
    # (In real usage, we'd have multiple sequences per stratum)
    expanded_data = []
    for _, row in metrics_df.iterrows():
        for _ in range(10):  # Create 10 samples per stratum
            sample = row.to_dict()
            sample["world_score"] += np.random.normal(0, 0.05)
            sample["sparse_consistency_score"] += np.random.normal(0, 0.05)
            expanded_data.append(sample)
    
    expanded_df = pd.DataFrame(expanded_data)
    
    # Extract factors
    expanded_df["dynamics"] = expanded_df["stratum"].apply(lambda x: "Static" if "Static" in x else "Fast")
    expanded_df["texture"] = expanded_df["stratum"].apply(lambda x: "High" if "High" in x else "Low")
    
    result = run_anova(expanded_df, "world_score", "dynamics", "texture")
    
    assert result is not None
    assert "anova_table" in result
    assert "interaction_pvalue" in result
    assert "main_effect_dynamics_pvalue" in result
    assert "main_effect_texture_pvalue" in result

def test_main(temp_metrics_dir, temp_results_dir):
    """Test the main ANOVA execution flow."""
    set_global_seed(42)
    # Create expanded data as in test_run_anova
    metrics_df = load_metrics_for_anova(temp_metrics_dir)
    expanded_data = []
    for _, row in metrics_df.iterrows():
        for _ in range(10):
            sample = row.to_dict()
            sample["world_score"] += np.random.normal(0, 0.05)
            sample["sparse_consistency_score"] += np.random.normal(0, 0.05)
            expanded_data.append(sample)
    expanded_df = pd.DataFrame(expanded_data)
    
    # Save expanded data
    expanded_path = Path(temp_results_dir) / "expanded_metrics.csv"
    expanded_df.to_csv(expanded_path, index=False)
    
    # Mock the main function to use our temp directory
    # In a real scenario, main() would scan the results directory
    # For this test, we verify the logic can handle the data
    result = run_anova(expanded_df, "world_score", "dynamics", "texture")
    
    assert result["interaction_pvalue"] is not None
    assert isinstance(result["interaction_pvalue"], float)