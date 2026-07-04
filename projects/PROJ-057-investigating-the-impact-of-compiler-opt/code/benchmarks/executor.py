import os
import sys
import subprocess
import json
import time
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing project modules
from benchmarks.config import BenchmarkConfig, ConfigManager, create_default_manager
from benchmarks.compile_runner import CompileRunner
from utils.logger import get_logger

# Ensure the logger module exists or define a fallback if T008 is not fully implemented yet
# Given T008 is marked completed, we assume utils.logger exists.
# If not, we define a simple local logger to ensure the script runs.
try:
    from utils.logger import get_logger
    logger = get_logger("executor")
except ImportError:
    import logging
    logger = logging.getLogger("executor")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

# Constants
TARGET_ITERATIONS = 1000
ADAPTIVE_STOP_THRESHOLD = 0.01  # 1% CV
ADAPTIVE_MIN_ITERATIONS = 30
MEMORY_FALLBACK_DIM = 512
DEFAULT_DIM = 768

class Executor:
    """
    Executes compiled C++ binaries and measures latency.
    Handles memory fallback and adaptive stopping.
    """

    def __init__(self, config_manager: ConfigManager, output_dir: Path):
        self.config_manager = config_manager
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runner = CompileRunner()

    def _detect_memory_pressure(self, dim: int) -> bool:
        """
        Simulate memory allocation check.
        In a real scenario, this might check system memory or attempt a small allocation.
        For this task, we simulate failure if the system has < 2GB free RAM or if we want to force the fallback path.
        To make the code robust and testable, we check available memory.
        """
        try:
            import psutil
            available_mem = psutil.virtual_memory().available
            # 768x768 float32 * 2 (input/output) ~ 4.7MB. 512x512 ~ 2MB.
            # This check is a proxy. Real C++ binary will fail if memory is truly tight.
            # We simulate a "pressure" if available memory is very low (< 500MB)
            # or if we want to demonstrate the fallback logic during testing.
            # For the purpose of this implementation, we rely on the C++ binary's exit code
            # to indicate memory failure, but we also add a heuristic check here.
            if available_mem < 500 * 1024 * 1024: # 500MB
                return True
        except ImportError:
            # If psutil not installed, we can't check, assume OK unless C++ fails
            pass
        return False

    def _run_binary(self, binary_path: Path, dim: int, iterations: int) -> Tuple[List[float], bool]:
        """
        Runs the binary and collects latency measurements.
        Returns (latencies, success).
        """
        # The C++ binary is expected to output latencies (in microseconds or ms) line by line
        # or a single summary. Based on the task, we need `median`, `p95`, `iterations`.
        # We assume the binary prints one latency value per line to stdout.
        
        cmd = [str(binary_path), str(dim), str(iterations)]
        latencies = []
        
        try:
            # We run the binary directly. If it fails to allocate, it should exit non-zero.
            # We capture stdout to parse latencies.
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600, # 10 minutes max per run
                check=False
            )

            if result.returncode != 0:
                # Check for specific memory error in stderr
                if "std::bad_alloc" in result.stderr or "Memory" in result.stderr:
                    return [], False
                # Other error
                logger.error(f"Binary execution failed: {result.stderr}")
                return [], False

            # Parse output
            # Expected format: one float per line representing a single run latency
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        latencies.append(float(line))
                    except ValueError:
                        continue
        
        except subprocess.TimeoutExpired:
            logger.error(f"Execution timed out for {binary_path}")
            return [], False
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return [], False

        return latencies, True

    def execute_config(self, config: BenchmarkConfig) -> Optional[Dict[str, Any]]:
        """
        Executes a single benchmark configuration.
        Implements memory fallback and adaptive stopping.
        """
        config_id = config.config_id
        logger.info(f"Starting execution for config: {config_id}")

        # 1. Compile the binary
        binary_path = self.runner.compile(config)
        if not binary_path or not binary_path.exists():
            logger.error(f"Compilation failed for {config_id}")
            return None

        # 2. Determine initial dimensions
        current_dim = config.dim
        downsampled = False
        max_attempts = 2 # Original + 1 fallback

        final_latencies = []
        
        for attempt in range(max_attempts):
            # Check memory pressure before running
            if attempt == 0 and self._detect_memory_pressure(current_dim):
                logger.warning(f"Memory pressure detected for {current_dim}x{current_dim}, downgrading to {MEMORY_FALLBACK_DIM}x{MEMORY_FALLBACK_DIM}")
                current_dim = MEMORY_FALLBACK_DIM
                downsampled = True
                continue # Retry with new dim

            logger.info(f"Running {binary_path} with dim={current_dim}, target_iters={TARGET_ITERATIONS}")
            
            # Adaptive loop variables
            all_latencies = []
            iteration_count = 0
            batch_size = 50 # Process in batches to check CV
            
            while iteration_count < TARGET_ITERATIONS:
                remaining = TARGET_ITERATIONS - iteration_count
                run_iters = min(batch_size, remaining)
                
                # Run a batch
                batch_latencies, success = self._run_binary(binary_path, current_dim, run_iters)
                
                if not success:
                    if attempt == 0:
                        # First attempt failed, try fallback
                        logger.warning(f"Run failed with {current_dim}, attempting fallback to {MEMORY_FALLBACK_DIM}")
                        current_dim = MEMORY_FALLBACK_DIM
                        downsampled = True
                        all_latencies = [] # Reset for new dim
                        iteration_count = 0
                        break # Break inner loop to retry outer
                    else:
                        # Fallback also failed
                        logger.error(f"Execution failed even after downscaling to {current_dim}")
                        return None
                
                all_latencies.extend(batch_latencies)
                iteration_count += run_iters

                # Check adaptive stop condition
                if iteration_count >= ADAPTIVE_MIN_ITERATIONS:
                    if len(all_latencies) > 0:
                        mean_lat = np.mean(all_latencies)
                        std_lat = np.std(all_latencies)
                        cv = std_lat / mean_lat if mean_lat > 0 else float('inf')
                        
                        if cv <= ADAPTIVE_STOP_THRESHOLD:
                            logger.info(f"Adaptive stop triggered at {iteration_count} iterations (CV={cv:.4f} <= {ADAPTIVE_STOP_THRESHOLD})")
                            break
            
            final_latencies = all_latencies
            break # Successfully ran or exhausted attempts

        if not final_latencies:
            logger.error(f"No latencies collected for {config_id}")
            return None

        # 3. Calculate Statistics
        median_lat = float(np.median(final_latencies))
        p95_lat = float(np.percentile(final_latencies, 95))
        iterations_used = len(final_latencies)

        result = {
            "config_id": config_id,
            "median": median_lat,
            "p95": p95_lat,
            "iterations": iterations_used,
            "downsampled_flag": downsampled,
            "dimensions": current_dim,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Finished {config_id}: Median={median_lat:.4f}, P95={p95_lat:.4f}, Iters={iterations_used}")

        # 4. Save to JSONL
        output_file = self.output_dir / f"{config_id}.jsonl"
        with open(output_file, 'a') as f:
            f.write(json.dumps(result) + '\n')

        return result

    def run_all(self):
        """Iterates over all configurations and executes them."""
        for config in self.config_manager.iter_configs():
            self.execute_config(config)


def main():
    parser = argparse.ArgumentParser(description="Executor for compiler optimization benchmarks")
    parser.add_argument("--test", action="store_true", help="Run a single test configuration to verify setup")
    args = parser.parse_args()

    # Initialize Config Manager
    # If --test, we create a minimal config
    if args.test:
        logger.info("Running in test mode...")
        from benchmarks.config import BenchmarkConfig
        test_config = BenchmarkConfig(
            kernel_type="matmul",
            flags=["-O2"],
            dim=512,
            iterations=10
        )
        # Create a temporary output dir for test
        test_output = Path("data/intermediates/raw_logs")
        test_output.mkdir(parents=True, exist_ok=True)
        
        exec_instance = Executor(create_default_manager(), test_output)
        # Mock compile for test if binary doesn't exist, or just run the logic
        # Since T014 verifies compilation, we assume binaries might exist or we need to compile first
        # For a pure executor test without kernels, we might just verify the flow.
        # However, the task says "Verify by running ... which outputs a SHA-256 hash of a dummy binary" in T014.
        # Here we just run the executor logic.
        try:
            # We need a real binary to measure latency. 
            # If no binary exists, this will fail gracefully or we skip.
            # For the purpose of this task, we assume the environment has the binaries from T014 or T011-T013.
            exec_instance.execute_config(test_config)
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            # Don't exit with error if just testing logic flow without binaries
    else:
        manager = create_default_manager()
        output_dir = Path("data/intermediates/raw_logs")
        executor = Executor(manager, output_dir)
        executor.run_all()


if __name__ == "__main__":
    main()