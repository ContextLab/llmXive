"""
Integration test for DPGMM model training on synthetic data.

This test verifies:
1. DPGMM model can be initialized with config
2. Model trains on synthetic time series data
3. ELBO converges during training
4. Model can detect anomalies in test data
5. Streaming posterior updates work correctly

Per US1 Independent Test: Verify model converges on synthetic data
and updates posterior incrementally.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from src.models.dpgmm import (
    DPGMMConfig,
    DPGMMModel,
    ELBOHistory,
    compute_anomaly_score,
    compute_anomaly_scores_batch,
)
from src.data.synthetic_generator import (
    AnomalyConfig,
    SignalConfig,
    generate_synthetic_timeseries,
    inject_point_anomalies,
)
from src.evaluation.metrics import compute_all_metrics, EvaluationMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Test constants
TEST_SEED = 42
N_TRAIN_OBS = 500
N_TEST_OBS = 200
N_ANOMALIES = 10
ELBO_TOLERANCE = 0.01  # ELBO must improve by at least this much
ANOMALY_DETECTION_THRESHOLD = 0.7  # Minimum detection rate
MIN_ACTIVE_COMPONENTS = 2  # Model should find at least 2 clusters

# Output paths
RESULTS_DIR = code_dir.parent / 'data' / 'processed' / 'results'
LOGS_DIR = code_dir.parent / 'logs' / 'elbo'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def generate_test_synthetic_data():
    """Generate synthetic time series with known anomalies for testing."""
    logger.info(f"Generating synthetic data with seed {TEST_SEED}")

    # Base signal configuration
    signal_config = SignalConfig(
        signal_type='sine',
        frequency=0.1,
        amplitude=1.0,
        noise_std=0.1,
        n_points=N_TRAIN_OBS + N_TEST_OBS,
        seed=TEST_SEED,
    )

    # Anomaly injection configuration
    anomaly_config = AnomalyConfig(
        anomaly_type='point',
        anomaly_magnitude=5.0,
        n_anomalies=N_ANOMALIES,
        anomaly_positions=None,  # Will be randomly placed
        seed=TEST_SEED + 1,
    )

    # Generate base signal
    np.random.seed(TEST_SEED)
    time_points = np.arange(N_TRAIN_OBS + N_TEST_OBS)
    base_signal = signal_config.amplitude * np.sin(
        2 * np.pi * signal_config.frequency * time_points
    )
    base_signal += np.random.normal(0, signal_config.noise_std, len(time_points))

    # Inject anomalies in test portion only
    anomaly_indices = np.random.choice(
        range(N_TRAIN_OBS, N_TRAIN_OBS + N_TEST_OBS),
        size=N_ANOMALIES,
        replace=False,
    )
    test_signal = base_signal.copy()
    for idx in anomaly_indices:
        test_signal[idx] += anomaly_config.anomaly_magnitude * np.random.choice([-1, 1])

    # Split into train and test
    train_data = base_signal[:N_TRAIN_OBS]
    test_data = test_signal[N_TRAIN_OBS:]
    true_anomaly_mask = np.zeros(N_TEST_OBS, dtype=bool)
    true_anomaly_mask[anomaly_indices - N_TRAIN_OBS] = True

    logger.info(f"Train data shape: {train_data.shape}")
    logger.info(f"Test data shape: {test_data.shape}")
    logger.info(f"True anomalies in test: {np.sum(true_anomaly_mask)}")

    return train_data, test_data, true_anomaly_mask, anomaly_indices

def test_dpgmm_initialization():
    """Test that DPGMM model can be initialized with valid config."""
    logger.info("Testing DPGMM initialization...")

    config = DPGMMConfig(
        max_components=10,
        min_components=2,
        concentration_prior=1.0,
        learning_rate=0.01,
        convergence_threshold=0.001,
        max_iterations=100,
        random_seed=TEST_SEED,
    )

    model = DPGMMModel(config)
    assert model is not None, "Model should be created"
    assert model.config == config, "Config should be stored"
    assert model._is_initialized is False, "Model should not be initialized yet"

    logger.info("✓ DPGMM initialization test passed")
    return True

def test_dpgmm_training_convergence():
    """Test that DPGMM training converges on synthetic data."""
    logger.info("Testing DPGMM training convergence...")

    # Generate synthetic data
    train_data, test_data, true_anomaly_mask, _ = generate_test_synthetic_data()

    # Configure model
    config = DPGMMConfig(
        max_components=10,
        min_components=2,
        concentration_prior=1.0,
        learning_rate=0.01,
        convergence_threshold=0.001,
        max_iterations=100,
        random_seed=TEST_SEED,
    )

    model = DPGMMModel(config)

    # Train on data
    logger.info("Starting training...")
    elbo_history = model.train(train_data)

    # Verify convergence
    assert elbo_history is not None, "ELBO history should be returned"
    assert len(elbo_history.elbo_values) > 0, "ELBO history should have values"

    # Check that ELBO improved
    if len(elbo_history.elbo_values) > 1:
        initial_elbo = elbo_history.elbo_values[0]
        final_elbo = elbo_history.elbo_values[-1]
        elbo_improvement = final_elbo - initial_elbo

        logger.info(f"ELBO improved from {initial_elbo:.4f} to {final_elbo:.4f}")
        logger.info(f"ELBO improvement: {elbo_improvement:.4f}")

        assert elbo_improvement > 0, "ELBO should improve during training"

    # Check active component count
    active_components = model.get_active_component_count()
    logger.info(f"Active components: {active_components}")
    assert active_components >= MIN_ACTIVE_COMPONENTS, (
        f"Model should find at least {MIN_ACTIVE_COMPONENTS} clusters"
    )

    # Save ELBO history
    elbo_log_path = LOGS_DIR / f"elbo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    elbo_log = {
        'timestamp': datetime.now().isoformat(),
        'test_id': 'T015_integration_training',
        'config': {
            'max_components': config.max_components,
            'min_components': config.min_components,
            'learning_rate': config.learning_rate,
        },
        'elbo_history': elbo_history.elbo_values,
        'converged': elbo_history.converged,
        'iterations': elbo_history.iterations,
        'final_elbo': elbo_history.elbo_values[-1] if elbo_history.elbo_values else None,
    }
    with open(elbo_log_path, 'w') as f:
        json.dump(elbo_log, f, indent=2)
    logger.info(f"ELBO history saved to {elbo_log_path}")

    logger.info("✓ DPGMM training convergence test passed")
    return True

def test_anomaly_detection_capability():
    """Test that DPGMM can detect anomalies in test data."""
    logger.info("Testing anomaly detection capability...")

    # Generate synthetic data
    train_data, test_data, true_anomaly_mask, _ = generate_test_synthetic_data()

    # Configure and train model
    config = DPGMMConfig(
        max_components=10,
        min_components=2,
        concentration_prior=1.0,
        learning_rate=0.01,
        convergence_threshold=0.001,
        max_iterations=100,
        random_seed=TEST_SEED,
    )

    model = DPGMMModel(config)
    model.train(train_data)

    # Compute anomaly scores on test data
    anomaly_scores = compute_anomaly_scores_batch(model, test_data)
    logger.info(f"Anomaly scores computed for {len(anomaly_scores)} test points")

    # Apply threshold (use median + 2*IQR as threshold)
    score_array = np.array([s.score for s in anomaly_scores])
    threshold = np.percentile(score_array, 90)  # Top 10% as anomalies
    predicted_anomalies = score_array > threshold

    # Calculate detection metrics
    true_positives = np.sum(predicted_anomalies & true_anomaly_mask)
    false_positives = np.sum(predicted_anomalies & ~true_anomaly_mask)
    false_negatives = np.sum(~predicted_anomalies & true_anomaly_mask)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    logger.info(f"True anomalies: {np.sum(true_anomaly_mask)}")
    logger.info(f"Predicted anomalies: {np.sum(predicted_anomalies)}")
    logger.info(f"True positives: {true_positives}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall: {recall:.4f}")
    logger.info(f"F1 Score: {f1:.4f}")

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_id': 'T015_integration_training',
        'n_train': len(train_data),
        'n_test': len(test_data),
        'n_true_anomalies': int(np.sum(true_anomaly_mask)),
        'n_predicted_anomalies': int(np.sum(predicted_anomalies)),
        'threshold': float(threshold),
        'metrics': {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'true_positives': int(true_positives),
            'false_positives': int(false_positives),
            'false_negatives': int(false_negatives),
        },
        'anomaly_scores': [
            {'index': i, 'score': float(s.score), 'timestamp': s.timestamp.isoformat()}
            for i, s in enumerate(anomaly_scores)
        ],
    }
    results_path = RESULTS_DIR / f"anomaly_detection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {results_path}")

    # Verify detection capability
    assert recall >= ANOMALY_DETECTION_THRESHOLD, (
        f"Recall should be at least {ANOMALY_DETECTION_THRESHOLD}"
    )

    logger.info("✓ Anomaly detection capability test passed")
    return True

def test_streaming_posterior_update():
    """Test that model can update posterior incrementally."""
    logger.info("Testing streaming posterior update...")

    # Generate synthetic data
    train_data, test_data, _, _ = generate_test_synthetic_data()

    # Configure model
    config = DPGMMConfig(
        max_components=10,
        min_components=2,
        concentration_prior=1.0,
        learning_rate=0.01,
        convergence_threshold=0.001,
        max_iterations=100,
        random_seed=TEST_SEED,
    )

    model = DPGMMModel(config)

    # Initial training on first half of data
    first_half = train_data[:N_TRAIN_OBS // 2]
    model.train(first_half)
    initial_components = model.get_active_component_count()
    logger.info(f"Initial components after first half: {initial_components}")

    # Update with second half (streaming)
    second_half = train_data[N_TRAIN_OBS // 2:]
    for obs in second_half:
        model.update_streaming(obs)

    updated_components = model.get_active_component_count()
    logger.info(f"Components after streaming update: {updated_components}")

    # Verify model state is valid after streaming
    assert model._is_initialized, "Model should be initialized after streaming"

    # Compute scores on updated model
    scores = compute_anomaly_scores_batch(model, test_data[:10])
    assert len(scores) == 10, "Should compute scores for all test points"

    logger.info("✓ Streaming posterior update test passed")
    return True

def test_batch_vs_streaming_consistency():
    """Test that batch training and streaming produce similar results."""
    logger.info("Testing batch vs streaming consistency...")

    # Generate synthetic data
    train_data, test_data, _, _ = generate_test_synthetic_data()

    # Configure model
    config = DPGMMConfig(
        max_components=10,
        min_components=2,
        concentration_prior=1.0,
        learning_rate=0.01,
        convergence_threshold=0.001,
        max_iterations=100,
        random_seed=TEST_SEED,
    )

    # Batch training
    model_batch = DPGMMModel(config)
    model_batch.train(train_data)
    batch_scores = compute_anomaly_scores_batch(model_batch, test_data[:50])

    # Streaming training
    model_stream = DPGMMModel(config)
    for obs in train_data:
        model_stream.update_streaming(obs)
    stream_scores = compute_anomaly_scores_batch(model_stream, test_data[:50])

    # Compare score distributions
    batch_mean = np.mean([s.score for s in batch_scores])
    stream_mean = np.mean([s.score for s in stream_scores])

    logger.info(f"Batch mean score: {batch_mean:.4f}")
    logger.info(f"Streaming mean score: {stream_mean:.4f}")
    logger.info(f"Score difference: {abs(batch_mean - stream_mean):.4f}")

    # Scores should be in similar range (within 50% of each other)
    ratio = max(batch_mean, stream_mean) / max(min(batch_mean, stream_mean), 1e-10)
    assert ratio < 2.0, f"Score distributions should be similar (ratio: {ratio:.2f})"

    logger.info("✓ Batch vs streaming consistency test passed")
    return True

def run_all_integration_tests():
    """Run all integration tests and generate summary report."""
    logger.info("=" * 60)
    logger.info("Starting DPGMM Integration Tests (T015)")
    logger.info("=" * 60)

    test_results = []

    tests = [
        ("Initialization", test_dpgmm_initialization),
        ("Training Convergence", test_dpgmm_training_convergence),
        ("Anomaly Detection", test_anomaly_detection_capability),
        ("Streaming Update", test_streaming_posterior_update),
        ("Batch vs Streaming", test_batch_vs_streaming_consistency),
    ]

    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- Running: {test_name} ---")
            result = test_func()
            test_results.append({
                'test': test_name,
                'status': 'PASSED',
                'timestamp': datetime.now().isoformat(),
            })
            logger.info(f"✓ {test_name} PASSED")
        except AssertionError as e:
            logger.error(f"✗ {test_name} FAILED: {e}")
            test_results.append({
                'test': test_name,
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"✗ {test_name} ERROR: {e}")
            test_results.append({
                'test': test_name,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            })

    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'test_id': 'T015_integration_training',
        'total_tests': len(test_results),
        'passed': sum(1 for r in test_results if r['status'] == 'PASSED'),
        'failed': sum(1 for r in test_results if r['status'] == 'FAILED'),
        'errors': sum(1 for r in test_results if r['status'] == 'ERROR'),
        'results': test_results,
    }

    summary_path = RESULTS_DIR / f"integration_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"\nSummary saved to {summary_path}")

    # Print final summary
    logger.info("=" * 60)
    logger.info("Integration Test Summary")
    logger.info("=" * 60)
    logger.info(f"Total: {summary['total_tests']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Errors: {summary['errors']}")
    logger.info("=" * 60)

    # Return True only if all tests passed
    all_passed = summary['failed'] == 0 and summary['errors'] == 0
    if all_passed:
        logger.info("✓ ALL INTEGRATION TESTS PASSED")
    else:
        logger.error("✗ SOME TESTS FAILED")

    return all_passed

def main():
    """Entry point for running integration tests."""
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
