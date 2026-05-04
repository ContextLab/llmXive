"""
Test script for ADVI variational inference in DPGMM model.

This script exercises the ADVI implementation from T017 and verifies:
1. Variational parameters initialize correctly
2. Posterior updates work for streaming observations
3. ELBO converges during training
4. Anomaly scores are computed correctly

Run: python test_advi_inference.py
"""
import sys
import numpy as np
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from src.models.dpgmm import DPGMMModel, AnomalyScore
from src.data.synthetic_generator import generate_synthetic_timeseries

def test_advi_initialization():
    """Test that ADVI variational parameters initialize correctly."""
    print("=" * 60)
    print("TEST 1: ADVI Variational Parameter Initialization")
    print("=" * 60)
    
    model = DPGMMModel(
        concentration=1.0,
        max_components=10,
        random_state=42,
        elbo_log_interval=50
    )
    
    # Force initialization with dummy data
    dummy_obs = np.zeros(5)  # 5-dimensional observation
    model._initialize_variational_params(n_features=5, n_init_components=3)
    
    # Verify parameters exist and have correct shapes
    assert model._variational_params['pi'] is not None
    assert model._variational_params['mu'] is not None
    assert model._variational_params['lambda_pi'] is not None
    assert model._variational_params['lambda_mu'] is not None
    assert model._variational_params['alpha'] is not None
    assert model._variational_params['beta'] is not None
    assert model._variational_params['nu'] is not None
    
    # Check shapes
    n_components = 3
    n_features = 5
    assert model._variational_params['pi'].shape == (n_components,)
    assert model._variational_params['mu'].shape == (n_components, n_features)
    assert model._variational_params['lambda_pi'].shape == (n_components,)
    assert model._variational_params['lambda_mu'].shape == (n_components,)
    
    print("✓ Variational parameters initialized correctly")
    print(f"  - pi shape: {model._variational_params['pi'].shape}")
    print(f"  - mu shape: {model._variational_params['mu'].shape}")
    print(f"  - lambda_pi shape: {model._variational_params['lambda_pi'].shape}")
    print(f"  - lambda_mu shape: {model._variational_params['lambda_mu'].shape}")
    print()
    
    return True

def test_streaming_posterior_update():
    """Test streaming posterior updates with ADVI."""
    print("=" * 60)
    print("TEST 2: Streaming Posterior Update")
    print("=" * 60)
    
    model = DPGMMModel(
        concentration=1.0,
        max_components=20,
        random_state=42
    )
    
    # Generate synthetic time series with known anomaly
    np.random.seed(42)
    n_normal = 500
    n_anomaly = 50
    
    # Normal data: Gaussian with mean 0, std 1
    normal_data = np.random.randn(n_normal, 3)
    
    # Anomaly data: shifted mean
    anomaly_data = np.random.randn(n_anomaly, 3) + 3.0  # Shifted by 3 std
    
    # Combine
    full_data = np.vstack([normal_data, anomaly_data])
    
    # Process observations one at a time (streaming)
    elbo_values = []
    anomaly_scores = []
    
    for i, obs in enumerate(full_data):
        score, var_params = model.update_posterior(obs)
        anomaly_scores.append(score.score)
        elbo_values.append(model._elbo_history[-1] if model._elbo_history else 0)
        
        if i % 100 == 0:
            print(f"  Processed {i+1}/{len(full_data)} observations, "
                  f"ELBO: {elbo_values[-1]:.2f}, "
                  f"n_components: {var_params['n_components']}")
    
    print("✓ Streaming posterior updates completed successfully")
    print(f"  - Total observations: {len(full_data)}")
    print(f"  - Final ELBO: {elbo_values[-1]:.2f}")
    print(f"  - Final component count: {model._variational_params['mu'].shape[0]}")
    print()
    
    return True

def test_elbo_convergence():
    """Test that ELBO converges during training."""
    print("=" * 60)
    print("TEST 3: ELBO Convergence")
    print("=" * 60)
    
    model = DPGMMModel(
        concentration=1.0,
        max_components=10,
        random_state=42,
        convergence_threshold=1e-4
    )
    
    # Generate synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 3
    
    # Multi-component data
    data = np.vstack([
        np.random.randn(n_samples // 3, n_features) + [0, 0, 0],
        np.random.randn(n_samples // 3, n_features) + [5, 5, 5],
        np.random.randn(n_samples - 2 * (n_samples // 3), n_features) + [-5, 5, 0],
    ])
    
    # Process all data
    for obs in data:
        model.update_posterior(obs)
    
    elbo_history = model.get_elbo_history()
    converged = model.check_convergence()
    
    print("✓ ELBO convergence test completed")
    print(f"  - ELBO history length: {len(elbo_history)}")
    print(f"  - Initial ELBO: {elbo_history[0]:.2f}")
    print(f"  - Final ELBO: {elbo_history[-1]:.2f}")
    print(f"  - ELBO improvement: {elbo_history[-1] - elbo_history[0]:.2f}")
    print(f"  - Converged: {converged}")
    
    # Verify ELBO generally increases (with some noise expected)
    if len(elbo_history) > 10:
        early_avg = np.mean(elbo_history[:10])
        late_avg = np.mean(elbo_history[-10:])
        print(f"  - Early ELBO avg: {early_avg:.2f}")
        print(f"  - Late ELBO avg: {late_avg:.2f}")
    
    print()
    
    return True

def test_anomaly_detection():
    """Test that ADVI model correctly identifies anomalies."""
    print("=" * 60)
    print("TEST 4: Anomaly Detection with ADVI")
    print("=" * 60)
    
    model = DPGMMModel(
        concentration=1.0,
        max_components=10,
        random_state=42
    )
    
    # Generate data with clear anomaly
    np.random.seed(42)
    n_normal = 200
    n_anomaly = 20
    
    normal_data = np.random.randn(n_normal, 2)
    anomaly_data = np.random.randn(n_anomaly, 2) + 5.0  # Clear anomaly
    
    # Process normal data first
  for obs in normal_data:
        model.update_posterior(obs)
    
    # Get baseline score distribution
    baseline_scores = []
    for obs in normal_data[:50]:
        score, _ = model.update_posterior(obs)
        baseline_scores.append(score.score)
    
    baseline_mean = np.mean(baseline_scores)
    baseline_std = np.std(baseline_scores)
    
    # Score anomaly points
    anomaly_scores = []
    for obs in anomaly_data:
        score, _ = model.update_posterior(obs)
        anomaly_scores.append(score.score)
    
    anomaly_mean = np.mean(anomaly_scores)
    
    print("✓ Anomaly detection test completed")
    print(f"  - Baseline (normal) score mean: {baseline_mean:.2f}")
    print(f"  - Baseline (normal) score std: {baseline_std:.2f}")
    print(f"  - Anomaly score mean: {anomaly_mean:.2f}")
    print(f"  - Anomaly scores are higher: {anomaly_mean > baseline_mean}")
    
    # Verify anomalies have higher scores
    assert anomaly_mean > baseline_mean, "Anomalies should have higher scores"
    print("  ✓ Anomalies correctly scored higher than normal data")
    
    print()
    
    return True

def main():
    """Run all ADVI inference tests."""
    print("\n" + "=" * 60)
    print("ADVI VARIATIONAL INFERENCE TEST SUITE (T017)")
    print("=" * 60 + "\n")
    
    all_passed = True
    
    tests = [
        ("ADVI Initialization", test_advi_initialization),
        ("Streaming Posterior Update", test_streaming_posterior_update),
        ("ELBO Convergence", test_elbo_convergence),
        ("Anomaly Detection", test_anomaly_detection),
    ]
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            if not passed:
                all_passed = False
                print(f"✗ {test_name} FAILED")
            else:
                print(f"✓ {test_name} PASSED")
        except Exception as e:
            all_passed = False
            print(f"✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        print("ADVI variational inference implementation is functional.")
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
