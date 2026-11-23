"""
Integration test for T039: Quickstart Validation.
This test verifies that the end-to-end pipeline runs successfully on a small subset.
"""
import pytest
import os
import sys
import json
import logging
from pathlib import Path
import time

# Setup path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_config, PipelineConfig
from main import run_baseline_extraction, run_noise_sweep, run_final_analysis, ensure_output_directory
from streaming_utils import sample_streaming_dataset
from data_loader import load_reasoning_dataset, ConfigurationError
from memory_monitor import reset_memory_tracker, save_memory_profile

logger = logging.getLogger("test_quickstart")
logger.setLevel(logging.DEBUG)

@pytest.mark.integration
def test_quickstart_end_to_end():
    """
    Run the full pipeline on a small subset (10 rows) and verify outputs.
    """
    # Setup config
    config = load_config()
    config.data_config.max_samples = 10
    config.noise_sweep_config.sigma_values = [0.1]
    config.noise_sweep_config.sigma_min = 0.1
    config.noise_sweep_config.sigma_max = 0.1
    config.noise_sweep_config.step = 0.1

    # Ensure directories
    ensure_output_directory(config.output_paths.baseline_vectors)
    ensure_output_directory(config.output_paths.perturbed_vectors)
    ensure_output_directory(config.output_paths.validity_log)
    ensure_output_directory(config.output_paths.statistical_results)
    ensure_output_directory(config.output_paths.trade_off_curve)
    ensure_output_directory(config.output_paths.global_trade_off_curve)
    ensure_output_directory(config.output_paths.sensitivity_report)

    reset_memory_tracker()

    # 1. Load Data
    logger.info("Loading real dataset subset...")
    try:
        dataset_iter = load_reasoning_dataset(config.data_config)
        sample_data = list(sample_streaming_dataset(dataset_iter, n=10, seed=42))
        assert len(sample_data) > 0, "No data loaded from real source"
    except ConfigurationError as e:
        pytest.fail(f"Data loading configuration error: {e}")
    except Exception as e:
        pytest.fail(f"Data loading failed: {e}")

    # 2. Baseline Extraction
    logger.info("Running baseline extraction...")
    try:
        run_baseline_extraction(config)
        assert Path(config.output_paths.baseline_vectors).exists(), "Baseline vectors missing"
    except Exception as e:
        pytest.fail(f"Baseline extraction failed: {e}")

    # 3. Noise Sweep
    logger.info("Running noise sweep...")
    try:
        run_noise_sweep(config)
        assert Path(config.output_paths.perturbed_vectors).exists(), "Perturbed vectors missing"
        assert Path(config.output_paths.validity_log).exists(), "Validity log missing"
    except Exception as e:
        pytest.fail(f"Noise sweep failed: {e}")

    # 4. Analysis
    logger.info("Running final analysis...")
    try:
        run_final_analysis(config)
        assert Path(config.output_paths.statistical_results).exists(), "Statistical results missing"
        assert Path(config.output_paths.trade_off_curve).exists(), "Trade-off curve missing"
        assert Path(config.output_paths.global_trade_off_curve).exists(), "Global trade-off missing"
        assert Path(config.output_paths.sensitivity_report).exists(), "Sensitivity report missing"
    except Exception as e:
        pytest.fail(f"Final analysis failed: {e}")

    # 5. Verify Content (Basic)
    baseline_path = Path(config.output_paths.baseline_vectors)
    with open(baseline_path, 'r') as f:
        header = f.readline()
        assert "pair_id" in header, "Baseline CSV missing pair_id column"
        assert "vector_base64" in header, "Baseline CSV missing vector_base64 column"

    stats_path = Path(config.output_paths.statistical_results)
    with open(stats_path, 'r') as f:
        stats = json.load(f)
        assert "p_value" in stats or "results" in stats, "Statistical results missing expected keys"

    logger.info("All checks passed.")