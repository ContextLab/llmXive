"""
Integration test for the detector pipeline with synthetic spike data.

This test verifies that the detector correctly identifies "hacked" timesteps
when a known divergence spike is injected into otherwise normal data.

It validates:
1. The ingestion of pre-computed divergence data (simulating T016 output).
2. The detection logic in `code/detector.py` flags the spike.
3. The output file `data/processed/trajectories_labeled.csv` is created with correct labels.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path to import code modules
# Assuming tests/integration is two levels deep from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_project_root, ensure_paths_exist
from utils.io_utils import write_csv, read_csv
from detector import run_detector_pipeline


def generate_synthetic_spike_data(output_path: Path, seed_id: str = "test_seed_01"):
    """
    Generates a synthetic dataset with a clear divergence spike.
    
    Creates a trajectory where G(t) is low and stable, then spikes sharply
    for a specific window, mimicking reward hacking behavior.
    """
    n_timesteps = 200
    timesteps = np.arange(n_timesteps)
    
    # Base signal: low divergence with small noise
    base_divergence = 0.5
    noise = np.random.normal(0, 0.05, n_timesteps)
    g_t = base_divergence + noise
    
    # Inject a spike at timesteps 100-110
    spike_start = 100
    spike_end = 110
    spike_magnitude = 5.0
    g_t[spike_start:spike_end] += spike_magnitude
    
    # Compute derivative (approximate)
    d_g_t = np.gradient(g_t)
    
    # Create DataFrame
    df = pd.DataFrame({
        'seed_id': seed_id,
        'bias_type': 'Lexical',
        'timestep': timesteps,
        'J_biased': 10.0 + g_t, # J_biased = J_gold + G_t (assuming J_gold ~ 10)
        'J_unbiased': 10.0,
        'J_gold': 10.0,
        'G_t': g_t,
        'dG_t': d_g_t
    })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    write_csv(str(output_path), df)
    
    return df


@pytest.fixture(scope="function")
def setup_test_environment(tmp_path):
    """
    Sets up a temporary directory structure mimicking the project layout
    for isolated testing.
    """
    # Create a temporary project root
    temp_root = tmp_path / "test_project"
    temp_root.mkdir()
    
    # Create necessary directories
    data_raw = temp_root / "data" / "raw"
    data_processed = temp_root / "data" / "processed"
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    
    # Mock the config to use temp paths if necessary, 
    # but for this test we will pass paths explicitly to the detector function
    # if the detector function supports it, or we monkeypatch the config.
    # However, the task requires running the detector pipeline which likely
    # reads from a fixed path defined in config or passed as args.
    # We will generate the input file in the standard expected location relative to temp_root
    # and then run the detector.
    
    # Since we cannot easily mock the global config without side effects,
    # we will assume the detector function `run_detector_pipeline` accepts
    # input/output paths or we will modify the global config state for the test duration.
    # Given the API surface provided, `detector.py` is not fully listed, 
    # but we must assume it follows the pattern of other modules.
    # We will assume `run_detector_pipeline` takes `input_path` and `output_path`.
    
    return {
        "root": temp_root,
        "input_path": data_processed / "trajectories_divergence.csv",
        "output_path": data_processed / "trajectories_labeled.csv"
    }


def test_detector_spikes_integration(setup_test_environment):
    """
    Integration test: 
    1. Generate synthetic data with a spike.
    2. Run the detector pipeline.
    3. Verify the spike is flagged in the output.
    """
    config = setup_test_environment
    input_path = config["input_path"]
    output_path = config["output_path"]
    
    # 1. Generate Data
    # We need to temporarily override the project root for config to work correctly
    # or pass paths directly. Assuming the detector function is flexible or we patch.
    # For robustness, let's patch the get_project_root function temporarily.
    original_get_project_root = None
    
    # Since we can't easily patch the global import inside detector.py if it imports config at module level,
    # let's assume the `run_detector_pipeline` function signature allows path overrides.
    # If not, we must rely on the fact that the test environment is set up such that
    # the detector reads from the standard location.
    
    # Strategy: Write data to the standard location relative to a temporary root,
    # and ensure the detector is called with that root or the config is updated.
    # To avoid complex mocking of global state, we will write the file to the expected
    # location in the temp directory and then call the detector function, assuming
    # it accepts arguments or we can configure it.
    
    # Let's assume the detector module has a function `run_detector_pipeline(input_path, output_path)`
    # as is common in such pipelines, or we pass the paths via the `main` logic.
    # Based on T021/T022 descriptions, it reads from `data/processed/trajectories_divergence.csv`.
    # We will place our test file there.
    
    # To make this work without modifying the global config of the running process,
    # we will assume the test runner sets the environment or we pass the path.
    # However, the most robust way for an integration test is to ensure the file exists
    # where the code expects it.
    
    # Generate the input file
    generate_synthetic_spike_data(input_path)
    
    # Verify input file exists and has data
    assert input_path.exists(), f"Input file {input_path} was not created."
    df_input = read_csv(str(input_path))
    assert len(df_input) > 0, "Input file is empty."
    
    # 2. Run Detector
    # We need to call the detector logic. 
    # Assuming the function `run_detector_pipeline` exists and takes input/output paths.
    # If the actual implementation relies on config paths, we might need to mock `get_project_root`.
    # Let's try to call the function directly with paths if possible.
    # If the API is strictly `main()` reading config, we might need to mock the config.
    # Given the constraint "import from sibling modules", we assume `detector.py` has a function.
    
    # Fallback: If we cannot determine the exact signature, we assume a standard signature
    # or that the test environment (pytest) can handle the path configuration.
    # Let's assume the function `run_detector_pipeline` is available and accepts paths.
    
    try:
        # Attempt to run the detector. 
        # We assume the function signature: run_detector_pipeline(input_path, output_path)
        # If the actual code uses config, we might need to patch.
        # For this test to pass, we assume the implementation in T021/T022 is flexible enough
        # or we are running in an environment where the paths are set.
        # To be safe, we will try to import and call the function.
        from detector import run_detector_pipeline
        
        # If the function requires config, we might need to set environment variables
        # or mock the config. 
        # Let's assume the function is designed to be testable with explicit paths.
        run_detector_pipeline(str(input_path), str(output_path))
        
    except TypeError as e:
        # If the function doesn't take arguments, it might be using config.
        # We will assume the test environment is set up such that the config points to temp paths.
        # But since we can't easily change the global config in this snippet without side effects,
        # we will assume the function signature is correct as assumed above.
        # If it fails, we raise a more descriptive error.
        raise RuntimeError(
            "Detector pipeline function signature mismatch or config issue. "
            "Ensure run_detector_pipeline accepts input/output paths or config is mocked."
        ) from e
        
    except ModuleNotFoundError:
        # If detector.py is not fully implemented yet (which it shouldn't be for this test task),
        # this test would fail. But the task is to write the test.
        # The test should be written to verify the implementation once it exists.
        # However, the prompt says "Implement the task", and the task is "Integration test".
        # The test must be runnable. If the detector module is missing, the test will fail.
        # But the instruction says "Write real, runnable research code".
        # We assume T021/T022 are implemented or the test is written to be run after them.
        # Since T020 is a test task, it might be written before the implementation (TDD).
        # But the prompt says "Tests are OPTIONAL - only include them if explicitly requested".
        # And "Write these tests FIRST, ensure they FAIL before implementation".
        # So it's okay if the detector module is not fully implemented yet?
        # No, the task says "Implement task T020". The artifact is the test file.
        # The test file must be valid Python and runnable. It will fail if the detector is missing.
        # But the test file itself must be correct.
        # Let's assume the detector module exists with a stub or partial implementation.
        # Or we handle the import error gracefully in the test? No, the test should fail loudly.
        # So we just write the test assuming the detector exists.
        raise
        
    except Exception as e:
        # If the detector runs but fails for other reasons, we re-raise.
        raise e

    # 3. Verify Output
    assert output_path.exists(), f"Output file {output_path} was not created."
    
    df_output = read_csv(str(output_path))
    assert 'hacked_label' in df_output.columns, "Output missing 'hacked_label' column."
    
    # Check that the spike region (100-110) is flagged
    spike_region = df_output[(df_output['timestep'] >= 100) & (df_output['timestep'] <= 110)]
    assert len(spike_region) > 0, "Spike region not found in output."
    
    # At least some of the spike region should be flagged as hacked (1)
    # We expect a high proportion, but due to smoothing or thresholds, maybe not all.
    # Let's assert that at least 50% of the spike region is flagged.
    flagged_count = spike_region['hacked_label'].sum()
    total_count = len(spike_region)
    
    assert flagged_count > 0, "No timesteps in the spike region were flagged as hacked."
    assert flagged_count / total_count > 0.5, f"Less than 50% of spike region flagged ({flagged_count}/{total_count})."
    
    # Also check that non-spike regions are mostly NOT flagged
    non_spike = df_output[(df_output['timestep'] < 100) | (df_output['timestep'] > 110)]
    if len(non_spike) > 0:
        non_spike_flagged = non_spike['hacked_label'].sum()
        # Expect very few false positives
        assert non_spike_flagged / len(non_spike) < 0.1, "Too many false positives in non-spike regions."