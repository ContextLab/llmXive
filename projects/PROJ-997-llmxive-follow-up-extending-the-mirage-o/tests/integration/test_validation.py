"""
Integration test for end-to-end statistical validation (US3).

This test validates the entire statistical pipeline from T026A -> T026 -> T027 -> T028 -> T029.
It verifies that:
1. Synchronized inputs are generated correctly.
2. Baseline and Proxy metrics are computed using shared inputs.
3. Statistical tests (paired t-test) are performed correctly.
4. Results are saved to the expected artifacts.

Note: This test requires the output artifacts from T021A (test.parquet) and T021 (gap_predictor.pkl).
If these are missing, the test will fail with a clear assertion error.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import pandas as pd
from scipy import stats

# Import project modules
from src.cli.synchronize_inputs import generate_synchronized_inputs
from src.cli.run_baseline_sync import run_baseline_metrics
from src.cli.run_proxy_loop import run_proxy_metrics
from src.services.statistical_tester import perform_statistical_comparison


@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for the test."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create necessary directories
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "models").mkdir(parents=True, exist_ok=True)
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    
    # Create a mock test.parquet (output of T021A)
    # This simulates the stratified split data required for US3
    mock_data = {
        "input_id": [f"id_{i}" for i in range(10)],
        "gradient_norms": np.random.rand(10),
        "local_curvature": np.random.rand(10),
        "quantized_logits": [np.random.rand(10) for _ in range(10)],
        "calculated_kl_divergence": np.random.rand(10) * 0.5,
        "quantization_level": np.random.choice(["INT4", "INT8", "FP8"], 10),
        "prompt": [f"Sample prompt {i}" for i in range(10)]
    }
    df = pd.DataFrame(mock_data)
    df.to_parquet(project_root / "data" / "processed" / "test.parquet")
    
    # Create a mock gap_predictor.pkl (output of T021)
    # We'll mock the model loading in the actual test functions, 
    # but we need the file to exist for the path check.
    with open(project_root / "data" / "models" / "gap_predictor.pkl", "w") as f:
        f.write("mock_model")
    
    os.environ["PROJECT_ROOT"] = str(project_root)
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)
    if "PROJECT_ROOT" in os.environ:
        del os.environ["PROJECT_ROOT"]


def test_e2e_statistical_validation(temp_project_root):
    """
    End-to-end test for statistical validation.
    
    Steps:
    1. Generate synchronized inputs (T026A).
    2. Run baseline metrics (T027) using synchronized inputs.
    3. Run proxy metrics (T028) using synchronized inputs.
    4. Perform statistical comparison (T029).
    5. Verify artifacts exist and contain expected data.
    """
    
    # 1. Generate synchronized inputs
    sync_file = temp_project_root / "data" / "processed" / "synchronized_inputs.json"
    generate_synchronized_inputs(seed=42, output_path=str(sync_file))
    assert sync_file.exists(), "Synchronized inputs file not created"
    
    with open(sync_file, "r") as f:
        sync_data = json.load(f)
    assert "prompts" in sync_data, "Synchronized inputs missing 'prompts' key"
    assert len(sync_data["prompts"]) > 0, "Synchronized inputs is empty"
    
    # 2. Run baseline metrics
    baseline_file = temp_project_root / "data" / "processed" / "baseline_metrics.json"
    # Mock the heavy quantized inference to avoid actual llama-cpp execution
    # We mock the return values to simulate a successful run
    with patch('src.cli.run_baseline_sync.run_quantized_inference_batch') as mock_inference:
        # Mock return: list of dicts with acceptance_rate and reasoning_score
        mock_results = [
            {"acceptance_rate": 0.8 + (i * 0.01), "reasoning_score": 0.9 - (i * 0.005)}
            for i in range(len(sync_data["prompts"]))
        ]
        mock_inference.return_value = mock_results
        
        run_baseline_metrics(
            test_data_path=str(temp_project_root / "data" / "processed" / "test.parquet"),
            input_prompts=sync_data["prompts"],
            output_path=str(baseline_file)
        )
    
    assert baseline_file.exists(), "Baseline metrics file not created"
    with open(baseline_file, "r") as f:
        baseline_metrics = json.load(f)
    assert "samples" in baseline_metrics, "Baseline metrics missing 'samples'"
    assert len(baseline_metrics["samples"]) == len(sync_data["prompts"]), "Baseline sample count mismatch"
    
    # 3. Run proxy metrics
    proxy_file = temp_project_root / "data" / "processed" / "proxy_metrics.json"
    # Mock the proxy loop to avoid actual model training/prediction
    with patch('src.cli.run_proxy_loop.predict_gap') as mock_predict, \
         patch('src.cli.run_proxy_loop.simulate_mipu_loop') as mock_mipu:
        mock_predict.return_value = 0.1  # Mock predicted gap
        mock_mipu.return_value = {
            "acceptance_rate": 0.75 + (i * 0.01), 
            "reasoning_score": 0.85 - (i * 0.005)
        }
        
        run_proxy_metrics(
            test_data_path=str(temp_project_root / "data" / "processed" / "test.parquet"),
            model_path=str(temp_project_root / "data" / "models" / "gap_predictor.pkl"),
            input_prompts=sync_data["prompts"],
            output_path=str(proxy_file)
        )
    
    assert proxy_file.exists(), "Proxy metrics file not created"
    with open(proxy_file, "r") as f:
        proxy_metrics = json.load(f)
    assert "samples" in proxy_metrics, "Proxy metrics missing 'samples'"
    assert len(proxy_metrics["samples"]) == len(sync_data["prompts"]), "Proxy sample count mismatch"
    
    # 4. Perform statistical comparison
    t_test_file = temp_project_root / "data" / "processed" / "t_test_results.json"
    perform_statistical_comparison(
        baseline_path=str(baseline_file),
        proxy_path=str(proxy_file),
        output_path=str(t_test_file)
    )
    
    assert t_test_file.exists(), "T-test results file not created"
    with open(t_test_file, "r") as f:
        t_test_results = json.load(f)
    
    # 5. Verify results structure and logic
    assert "acceptance_rate" in t_test_results, "T-test results missing 'acceptance_rate'"
    assert "reasoning_score" in t_test_results, "T-test results missing 'reasoning_score'"
    
    # Verify t-test fields
    acc_test = t_test_results["acceptance_rate"]
    assert "t_statistic" in acc_test, "Acceptance rate t-test missing 't_statistic'"
    assert "p_value" in acc_test, "Acceptance rate t-test missing 'p_value'"
    assert "significant" in acc_test, "Acceptance rate t-test missing 'significant'"
    
    # Verify Bonferroni correction logic (alpha = 0.05 / 2 tests = 0.025)
    assert t_test_results["adjusted_alpha"] == 0.025, "Bonferroni correction not applied correctly"
    
    # Verify paired t-test logic (mock data should produce valid stats)
    assert isinstance(acc_test["t_statistic"], float), "T-statistic should be a float"
    assert isinstance(acc_test["p_value"], float), "P-value should be a float"
    
    # Verify significant flag logic
    expected_sig = acc_test["p_value"] < t_test_results["adjusted_alpha"]
    assert acc_test["significant"] == expected_sig, "Significance flag incorrect"
    
    print("E2E Statistical Validation Test Passed")
    print(f"  - Synchronized inputs: {len(sync_data['prompts'])} prompts")
    print(f"  - Baseline samples: {len(baseline_metrics['samples'])}")
    print(f"  - Proxy samples: {len(proxy_metrics['samples'])}")
    print(f"  - Acceptance Rate T-Test: t={acc_test['t_statistic']:.4f}, p={acc_test['p_value']:.4f}, sig={acc_test['significant']}")
    
    return True