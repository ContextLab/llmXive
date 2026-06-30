"""
Integration test for baseline vs. intervention comparison in Hanabi.

This test asserts that data generation runs successfully for both
Foundation Protocol and Native Direct Communication protocols.

It does not perform statistical analysis (that is for T019), but verifies
the end-to-end pipeline produces valid MetricRecord outputs for both
protocols, ensuring the infrastructure is ready for the full experiment suite.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
from data.generate_seeds import generate_seed_pool, create_seed_configurations
from foundation_protocol.middleware import FoundationMiddleware, create_middleware_agent
from foundation_protocol.direct_comm import DirectCommAgent
from benchmarks.hanabi_runner import run_hanabi_benchmark
from foundation_protocol.utils import log_seed


def test_comparison_logic():
    """
    Integration test: Run Hanabi benchmark with Foundation and Native Direct protocols.
    
    Assertions:
    1. Data generation (seeds) completes without error.
    2. Benchmark runs for Foundation Protocol and produces output file.
    3. Benchmark runs for Native Direct Protocol and produces output file.
    4. Output files are valid CSVs with expected columns (MetricRecord schema).
    5. At least one row is generated per protocol.
    """
    # Setup temporary directory for this test run to avoid polluting data/
    temp_dir = Path(tempfile.mkdtemp(prefix="hanabi_test_"))
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True)
    
    # Configuration for a minimal run (small number of seeds/episodes)
    num_seeds = 2
    num_episodes = 3
    protocol_names = ["foundation", "native_direct"]
    
    try:
        # 1. Generate Seeds
        # Using a fixed base seed for reproducibility in this test
        base_seed = 42
        seed_pool = generate_seed_pool(base_seed, num_seeds)
        assert len(seed_pool) == num_seeds, "Seed generation failed to produce requested count"
        
        seed_configs = create_seed_configurations(seed_pool, num_episodes)
        assert len(seed_configs) == num_seeds, "Seed configuration creation failed"
        
        # 2. Run Benchmarks for each protocol
        results = {}
        
        for protocol in protocol_names:
            output_file = output_dir / f"hanabi_{protocol}_results.csv"
            
            # Determine the runner mode based on protocol name
            # The runner handles the logic internally based on the protocol argument
            success = run_hanabi_benchmark(
                seed_configurations=seed_configs,
                protocol=protocol,
                output_file=str(output_file),
                num_episodes=num_episodes
            )
            
            assert success, f"Benchmark run failed for protocol: {protocol}"
            assert output_file.exists(), f"Output file not created for protocol: {protocol}"
            
            # 3. Validate Output File
            df = pd.read_csv(output_file)
            
            # Verify schema compliance (MetricRecord fields)
            expected_columns = {
                'seed', 'protocol', 'episode_length', 'msg_count', 
                'bytes_sent', 'recovery_success', 'recovery_latency', 'task_success'
            }
            actual_columns = set(df.columns)
            
            missing = expected_columns - actual_columns
            assert not missing, f"Missing MetricRecord columns in {protocol} output: {missing}"
            
            # Verify data presence
            assert len(df) > 0, f"No data rows generated for protocol: {protocol}"
            
            results[protocol] = df
        
        # 4. Cross-protocol consistency check (optional but good for integration)
        # Ensure both runs used the same seeds
        for protocol in protocol_names:
            df = results[protocol]
            # Seeds should be consistent across runs for the same configuration
            # This just checks that the data structure is uniform
            assert 'seed' in df.columns
            assert 'protocol' in df.columns
            
        # 5. Success condition
        print(f"Integration test passed. Generated {len(results['foundation'])} rows for Foundation and {len(results['native_direct'])} rows for Native Direct.")
        return True
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_comparison_logic()
    print("T014 Integration Test: PASSED")
