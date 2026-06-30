"""
Integration test for multi-task bandwidth comparison (User Story 3).

This test verifies that the simulation pipeline can successfully execute
across multiple benchmark tasks (Hanabi, SPEAR, Resource Allocation) for
both Foundation Protocol and Native Direct Communication baselines,
and that the resulting bandwidth metrics are collected and schema-compliant.

It does NOT perform the statistical analysis (LMM/t-tests) - that is the
responsibility of stats_analyzer.py (T034). This test ensures the data
generation pipeline works end-to-end.
"""
import os
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any

# Project imports
from benchmarks.hanabi_runner import run_hanabi_benchmark
from benchmarks.spear_runner import run_spear_benchmark
from benchmarks.resource_alloc_runner import run_resource_allocation_benchmark
from foundation_protocol.middleware import FoundationMiddleware
from foundation_protocol.direct_comm import DirectCommAgent
from experiments.run_simulation import run_single_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for the test
TEST_SEED = 42
TEST_EPISODES = 2  # Minimal episodes for integration speed
PROTOCOLS = ["foundation", "direct"]
TASKS = ["hanabi", "spear", "resource_alloc"]


def _run_single_task_protocol(
    task_name: str,
    protocol: str,
    seed: int,
    episodes: int,
    output_dir: Path
) -> List[Dict[str, Any]]:
    """
    Run a single task with a specific protocol and collect metric records.
    """
    logger.info(f"Running {task_name} with {protocol} protocol (seed={seed})...")

    # Prepare output path
    output_path = output_dir / f"{task_name}_{protocol}_seed{seed}.json"

    # Run the appropriate benchmark
    if task_name == "hanabi":
        records = run_hanabi_benchmark(
            protocol=protocol,
            seed=seed,
            num_episodes=episodes,
            output_path=str(output_path)
        )
    elif task_name == "spear":
        records = run_spear_benchmark(
            protocol=protocol,
            seed=seed,
            num_episodes=episodes,
            output_path=str(output_path)
        )
    elif task_name == "resource_alloc":
        records = run_resource_allocation_benchmark(
            protocol=protocol,
            seed=seed,
            num_episodes=episodes,
            output_path=str(output_path)
        )
    else:
        raise ValueError(f"Unknown task: {task_name}")

    # Verify output file was written
    assert output_path.exists(), f"Output file not created: {output_path}"

    # Load and verify records
    with open(output_path, 'r') as f:
        loaded_records = json.load(f)

    assert isinstance(loaded_records, list), "Output must be a list of records"
    assert len(loaded_records) > 0, "No records generated"

    # Basic schema compliance check (ensure expected fields exist)
    required_fields = ["episode_length", "msg_count", "bytes_sent"]
    for rec in loaded_records:
        for field in required_fields:
            assert field in rec, f"Missing required field '{field}' in record: {rec}"

    return loaded_records


def test_multi_task_logic():
    """
    Integration test: Run all three tasks with both protocols.

    Validates:
    1. All tasks execute without crashing.
    2. Both protocols (Foundation, Direct) produce output.
    3. Output files are created on disk.
    4. Metrics contain expected fields (bytes_sent, msg_count, etc.).
    5. Foundation protocol generally reduces or matches bandwidth vs baseline
       (heuristic check for sanity, not statistical proof).
    """
    # Create temporary directory for test artifacts
    test_dir = Path(tempfile.mkdtemp(prefix="test_multi_task_"))
    try:
        logger.info(f"Using temporary directory: {test_dir}")

        all_results = {}

        # Execute all combinations
        for task in TASKS:
            all_results[task] = {}
            for protocol in PROTOCOLS:
                records = _run_single_task_protocol(
                    task_name=task,
                    protocol=protocol,
                    seed=TEST_SEED,
                    episodes=TEST_EPISODES,
                    output_dir=test_dir
                )
                all_results[task][protocol] = records

                # Sanity check: bytes_sent should be non-negative
                for rec in records:
                    assert rec["bytes_sent"] >= 0, f"Negative bytes_sent in {task}/{protocol}"

        # Aggregated comparison (heuristic sanity check)
        # For each task, compare mean bytes_sent between protocols
        for task in TASKS:
            foundation_records = all_results[task]["foundation"]
            direct_records = all_results[task]["direct"]

            mean_foundation = sum(r["bytes_sent"] for r in foundation_records) / len(foundation_records)
            mean_direct = sum(r["bytes_sent"] for r in direct_records) / len(direct_records)

            logger.info(f"Task: {task} | Foundation Mean Bytes: {mean_foundation:.2f} | Direct Mean Bytes: {mean_direct:.2f}")

            # Heuristic assertion: Foundation should not be catastrophically worse
            # (e.g., > 2x baseline). Real statistical validation is in T034/T035.
            # We allow some variance due to small sample size (2 episodes).
            if mean_direct > 0:
                ratio = mean_foundation / mean_direct
                assert ratio < 2.0, (
                    f"Foundation bandwidth ({mean_foundation:.2f}) is > 2x Direct ({mean_direct:.2f}) "
                    f"for task {task}. This indicates a potential regression in the protocol overhead."
                )

        logger.info("Integration test passed: All tasks and protocols executed successfully.")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        logger.info(f"Cleaned up temporary directory: {test_dir}")