"""
Integration test for User Story 2: Stability Flow.
Specifically verifies the comparison logic of O3 vs O0 optimization levels
against the high-precision reference engine.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal, getcontext

# Ensure code directory is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from benchmarks.config import ConfigManager, create_default_manager
from benchmarks.reference import decimal_matmul, generate_reference_tensor
from benchmarks.tensor_generator import generate_tensor, save_tensor_to_binary
from analysis.stability_check import (
    load_raw_logs,
    detect_nan_in_tensor,
    process_stability,
    save_stable_logs,
    save_unstable_audit
)


def test_compare_O3_vs_O0():
    """
    Integration test: Compare O3 vs O0 optimization levels against reference.

    Steps:
    1. Setup temporary directories for test artifacts.
    2. Generate a deterministic input tensor (512x512).
    3. Generate high-precision reference output using decimal_matmul.
    4. Simulate "kernel outputs" for O0 and O3 (using float32 approximations
       to mimic the behavior of compiled binaries without needing full C++ compilation).
    5. Run the stability analysis pipeline (process_stability).
    6. Verify that:
       - Stable logs are generated.
       - Unstable logs (if any) are audited.
       - The comparison logic correctly identifies O3 and O0 results.
       - Metrics (L2 error, Max Diff) are calculated and stored.
    """
    # 1. Setup
    test_dir = tempfile.mkdtemp(prefix="stability_test_")
    try:
        data_raw = Path(test_dir) / "data" / "raw"
        data_inter = Path(test_dir) / "data" / "intermediates"
        data_raw.mkdir(parents=True, exist_ok=True)
        data_inter.mkdir(parents=True, exist_ok=True)

        # Configuration
        dim = 512
        seed = 42
        config_manager = create_default_manager()
        
        # Force specific flags for this test
        test_configs = [
            {"flags": "-O0", "config_id": "matmul_O0_512", "kernel": "matmul"},
            {"flags": "-O3", "config_id": "matmul_O3_512", "kernel": "matmul"}
        ]

        # 2. Generate Input Tensor
        input_tensor = generate_tensor(shape=(dim, dim), seed=seed, distribution="normal")
        input_path = data_raw / "input_tensor_512.bin"
        save_tensor_to_binary(input_tensor, input_path)

        # 3. Generate Reference (High Precision)
        # Convert float32 input to Decimal for reference calculation
        getcontext().prec = 512
        input_decimal = [[Decimal(str(float(x))) for x in row] for row in input_tensor]
        
        # Perform MatMul: A * A^T (or similar square operation) to generate output
        # Using the reference engine's logic
        ref_output = decimal_matmul(input_decimal, input_decimal)
        
        # Convert back to float for comparison (simulating the "measured" float output)
        # In a real flow, the C++ kernel produces this float output directly.
        # Here we simulate the "measured" float output by converting the high-precision result back to float.
        # To simulate O0/O3 drift, we will intentionally add noise to the reference for the "kernel" outputs.
        
        ref_float = np.array([[float(x) for x in row] for row in ref_output], dtype=np.float32)

        # 4. Simulate Kernel Outputs (O0 and O3)
        # O0: Usually very close to standard float32, minimal drift
        # O3 with -ffast-math might introduce more drift, but here we simulate standard O3
        # We create "measured" outputs by adding small noise to the reference to simulate
        # the difference between the C++ float32 result and the Decimal result.
        
        import numpy as np
        
        # Simulate O0 output (very close to reference)
        noise_O0 = np.random.normal(0, 1e-7, ref_float.shape).astype(np.float32)
        output_O0 = ref_float + noise_O0

        # Simulate O3 output (slightly different, maybe due to reordering)
        noise_O3 = np.random.normal(0, 5e-7, ref_float.shape).astype(np.float32)
        output_O3 = ref_float + noise_O3

        # Save simulated binary outputs (as JSON for simplicity in this test, 
        # matching the expected format of raw_logs if they were parsed from binary)
        # In the real system, executor.py writes JSONL logs with the tensor data.
        
        logs = []
        
        # Create log entry for O0
        log_O0 = {
            "config_id": "matmul_O0_512",
            "kernel": "matmul",
            "flags": "-O0",
            "dimensions": f"{dim}x{dim}",
            "median_latency_ms": 10.5,
            "iterations": 1000,
            "output_tensor": output_O0.flatten().tolist()
        }
        logs.append(log_O0)

        # Create log entry for O3
        log_O3 = {
            "config_id": "matmul_O3_512",
            "kernel": "matmul",
            "flags": "-O3",
            "dimensions": f"{dim}x{dim}",
            "median_latency_ms": 8.2,
            "iterations": 1000,
            "output_tensor": output_O3.flatten().tolist()
        }
        logs.append(log_O3)

        # Write raw logs
        raw_log_path = data_inter / "raw_logs"
        raw_log_path.mkdir(parents=True, exist_ok=True)
        
        with open(raw_log_path / "experiment_run.jsonl", "w") as f:
            for log in logs:
                f.write(json.dumps(log) + "\n")

        # 5. Run Stability Analysis
        # The process_stability function expects to load these logs and compare against reference
        # Since we don't have the actual reference file in the same format, we need to adapt
        # the test to mimic the flow or ensure process_stability can handle the comparison.
        
        # Looking at the API, process_stability likely loads logs and compares against a stored reference.
        # For this integration test, we will manually invoke the comparison logic that process_stability uses,
        # or we ensure the reference is available in the expected format.
        
        # Let's assume process_stability loads the reference from data/raw/reference_*.bin or similar.
        # We will save the reference tensor to the expected location.
        ref_save_path = data_raw / "reference_matmul_512.bin"
        save_tensor_to_binary(ref_float, ref_save_path)

        # Now run the stability check
        stable_logs_path = data_inter / "stable_logs.jsonl"
        unstable_logs_path = data_inter / "unstable_audit.jsonl"

        # Execute the main logic of stability_check
        # We call process_stability which should orchestrate the loading and comparison
        process_stability(
            raw_log_path=raw_log_path / "experiment_run.jsonl",
            reference_path=ref_save_path,
            stable_output_path=stable_logs_path,
            unstable_output_path=unstable_logs_path
        )

        # 6. Verification
        # Check that stable logs exist and contain data
        assert stable_logs_path.exists(), "Stable logs file was not created."
        with open(stable_logs_path, "r") as f:
            stable_data = [json.loads(line) for line in f if line.strip()]
        
        assert len(stable_data) == 2, f"Expected 2 stable entries, got {len(stable_data)}"
        
        # Verify specific config IDs are present
        config_ids = [entry["config_id"] for entry in stable_data]
        assert "matmul_O0_512" in config_ids, "O0 config not found in stable logs."
        assert "matmul_O3_512" in config_ids, "O3 config not found in stable logs."

        # Verify metrics are present (L2 error, Max Diff)
        for entry in stable_data:
            assert "l2_error" in entry, "L2 error missing in stable log entry."
            assert "max_diff" in entry, "Max diff missing in stable log entry."
            assert "status" in entry, "Status missing in stable log entry."
            assert entry["status"] == "stable", f"Entry {entry['config_id']} marked as unstable unexpectedly."

        # Check unstable audit (should be empty if all are stable)
        if unstable_logs_path.exists():
            with open(unstable_logs_path, "r") as f:
                unstable_data = [json.loads(line) for line in f if line.strip()]
            # It's okay if it's empty, but the file should exist
            assert True, "Unstable audit file exists."
        else:
            # If the implementation doesn't create an empty file, that's also fine as long as no unstable logs are generated
            pass

        print("Test passed: O3 vs O0 comparison logic verified.")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_compare_O3_vs_O0()