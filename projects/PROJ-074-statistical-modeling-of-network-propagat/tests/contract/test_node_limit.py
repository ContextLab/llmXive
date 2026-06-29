"""
Contract test for T071: Verify cascades exceeding node limit are logged in skipped_cascades.log.

This test confirms that:
1. Cascades with > 2000 nodes are skipped and logged to skipped_cascades.log
2. Cascades with ≤ 2000 nodes are processed normally
3. The log file contains the correct cascade IDs
4. The log file format matches expectations

Per T010: "cascades with > 2,000 nodes are logged to skipped_cascades.log and skipped"
"""

import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from pipeline.utils import load_cascade, setup_logger, set_global_seed

# Constants matching T010 specification
NODE_LIMIT = 2000
SKIP_LOG_FILENAME = "skipped_cascades.log"

# Set global seed for reproducibility (per T060)
set_global_seed(12345)


def create_test_cascade(cascade_id: str, num_nodes: int, temp_dir: Path) -> Path:
    """
    Create a test cascade JSON file with specified number of nodes.

    Args:
        cascade_id: Unique identifier for the cascade
        num_nodes: Number of nodes in the cascade
        temp_dir: Directory to write the cascade file to

    Returns:
        Path to the created cascade file
    """
    cascade_data = {
        "cascade_id": cascade_id,
        "nodes": [],
        "edges": []
    }

    # Create nodes
    for i in range(num_nodes):
        node_data = {
            "node_id": f"node_{i}",
            "timestamp": "2024-01-15T10:00:00Z",
            "user_id": f"user_{i % 10}",
            "message_id": f"msg_{i}",
            "platform_id": "twitter"
        }
        cascade_data["nodes"].append(node_data)

    # Create edges (simple chain)
    for i in range(num_nodes - 1):
        edge_data = {
            "source": f"node_{i}",
            "target": f"node_{i + 1}",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        cascade_data["edges"].append(edge_data)

    # Write to file
    cascade_file = temp_dir / f"{cascade_id}.json"
    with open(cascade_file, "w") as f:
        json.dump(cascade_data, f)

    return cascade_file


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def setup_test_cascades(temp_test_dir):
    """
    Create a mix of cascades: some under limit, some over limit.

    Returns:
        dict with paths and expected results
    """
    # Cascades under limit (should be processed)
    under_limit_ids = ["cascade_under_1", "cascade_under_2"]
    under_limit_paths = []
    for cid in under_limit_ids:
        path = create_test_cascade(cid, 500, temp_test_dir)  # 500 nodes
        under_limit_paths.append(path)

    # Cascades over limit (should be skipped)
    over_limit_ids = ["cascade_over_1", "cascade_over_2"]
    over_limit_paths = []
    for cid in over_limit_ids:
        path = create_test_cascade(cid, 2500, temp_test_dir)  # 2500 nodes
        over_limit_paths.append(path)

    return {
        "under_limit_ids": under_limit_ids,
        "over_limit_ids": over_limit_ids,
        "under_limit_paths": under_limit_paths,
        "over_limit_paths": over_limit_paths,
        "test_dir": temp_test_dir
    }


def test_skipped_cascades_log_created_for_over_limit_cascades(setup_test_cascades):
    """
    Test that skipped_cascades.log is created when cascades exceed node limit.

    Per T010: "cascades with > 2,000 nodes are logged to skipped_cascades.log and skipped"
    """
    test_dir = setup_test_cascades["test_dir"]
    over_limit_ids = setup_test_cascades["over_limit_ids"]

    # Initialize logger (will write to test_dir)
    log_path = test_dir / SKIP_LOG_FILENAME
    logger = setup_logger(log_path)

    # Process over-limit cascades (should trigger logging)
    for path in setup_test_cascades["over_limit_paths"]:
        # Load each cascade - this should trigger the node limit check
        try:
            result = load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
            # If load_cascade returns, the cascade was skipped (result should indicate skip)
        except Exception as e:
            # Expected: load_cascade may raise or return None for oversized cascades
            pass

    # Verify log file was created
    assert log_path.exists(), f"skipped_cascades.log should be created at {log_path}"


def test_skipped_cascades_log_contains_over_limit_cascade_ids(setup_test_cascades):
    """
    Test that skipped_cascades.log contains the IDs of cascades exceeding the node limit.

    Per T010: "cascades with > 2,000 nodes are logged to skipped_cascades.log"
    """
    test_dir = setup_test_cascades["test_dir"]
    over_limit_ids = setup_test_cascades["over_limit_ids"]

    # Initialize logger
    log_path = test_dir / SKIP_LOG_FILENAME
    logger = setup_logger(log_path)

    # Process over-limit cascades
    for path in setup_test_cascades["over_limit_paths"]:
        try:
            load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

    # Read log file and verify IDs are present
    with open(log_path, "r") as f:
        log_content = f.read()

    for cid in over_limit_ids:
        assert cid in log_content, (
            f"Cascade ID '{cid}' (over {NODE_LIMIT} nodes) should be logged in {SKIP_LOG_FILENAME}"
        )


def test_skipped_cascades_log_does_not_contain_under_limit_cascade_ids(setup_test_cascades):
    """
    Test that skipped_cascades.log does NOT contain IDs of cascades under the node limit.

    Per T010: Only cascades exceeding the limit should be logged.
    """
    test_dir = setup_test_cascades["test_dir"]
    under_limit_ids = setup_test_cascades["under_limit_ids"]

    # Initialize logger
    log_path = test_dir / SKIP_LOG_FILENAME
    logger = setup_logger(log_path)

    # Process under-limit cascades (should NOT be logged)
    for path in setup_test_cascades["under_limit_paths"]:
        try:
            load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

    # Read log file
    if log_path.exists():
        with open(log_path, "r") as f:
            log_content = f.read()

        for cid in under_limit_ids:
            assert cid not in log_content, (
                f"Cascade ID '{cid}' (under {NODE_LIMIT} nodes) should NOT be in {SKIP_LOG_FILENAME}"
            )


def test_skipped_cascades_log_format_is_valid(setup_test_cascades):
    """
    Test that skipped_cascades.log follows expected format.

    Expected format per T010: Each line should contain cascade ID and reason.
    """
    test_dir = setup_test_cascades["test_dir"]

    # Initialize logger
    log_path = test_dir / SKIP_LOG_FILENAME
    logger = setup_logger(log_path)

    # Process over-limit cascades to generate log entries
    for path in setup_test_cascades["over_limit_paths"]:
        try:
            load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

    # Verify log file exists and has content
    assert log_path.exists(), f"{SKIP_LOG_FILENAME} should be created"
    assert log_path.stat().st_size > 0, f"{SKIP_LOG_FILENAME} should not be empty"

    # Read and verify format
    with open(log_path, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0, f"{SKIP_LOG_FILENAME} should contain at least one entry"

    # Each line should contain cascade ID and node count information
    for line in lines:
        line = line.strip()
        if line:  # Skip empty lines
            assert len(line) > 0, "Log entries should not be empty"
            # Check that node limit is mentioned
            assert "node" in line.lower() or "limit" in line.lower(), (
                f"Log entry should mention node limit: {line}"
            )


def test_node_limit_threshold_is_exactly_2000(setup_test_cascades):
    """
    Test that the node limit threshold is exactly 2000 (not 1999 or 2001).

    Per T010: "cascades with > 2,000 nodes are logged to skipped_cascades.log"
    This means exactly 2000 should be OK, but 2001 should be skipped.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)

        # Create cascade with exactly 2000 nodes (should be OK)
        exact_limit_path = create_test_cascade("cascade_exact_limit", NODE_LIMIT, test_dir)

        # Create cascade with 2001 nodes (should be skipped)
        over_by_one_path = create_test_cascade("cascade_over_by_one", NODE_LIMIT + 1, test_dir)

        # Initialize logger
        log_path = test_dir / SKIP_LOG_FILENAME
        logger = setup_logger(log_path)

        # Process exact limit cascade
        try:
            load_cascade(exact_limit_path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

        # Process over-by-one cascade
        try:
            load_cascade(over_by_one_path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

        # Read log file
        if log_path.exists():
            with open(log_path, "r") as f:
                log_content = f.read()

            # Exact limit should NOT be in log
            assert "cascade_exact_limit" not in log_content, (
                f"Cascade with exactly {NODE_LIMIT} nodes should NOT be logged"
            )

            # Over by one SHOULD be in log
            assert "cascade_over_by_one" in log_content, (
                f"Cascade with {NODE_LIMIT + 1} nodes should be logged"
            )


def test_skipped_cascades_log_is_created_in_correct_location(setup_test_cascades):
    """
    Test that skipped_cascades.log is created in the expected location.

    Per T010: The log should be written to the project's data directory
    or the location specified by the pipeline configuration.
    """
    test_dir = setup_test_cascades["test_dir"]
    expected_log_path = test_dir / SKIP_LOG_FILENAME

    # Initialize logger (creates log file)
    logger = setup_logger(expected_log_path)

    # Process a cascade to trigger potential logging
    for path in setup_test_cascades["over_limit_paths"]:
        try:
            load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

    # Verify log is at expected path
    assert expected_log_path.exists(), (
        f"{SKIP_LOG_FILENAME} should be created at {expected_log_path}"
    )


def test_multiple_over_limit_cascades_all_logged(setup_test_cascades):
    """
    Test that ALL cascades exceeding the node limit are logged, not just the first.
    """
    test_dir = setup_test_cascades["test_dir"]
    over_limit_ids = setup_test_cascades["over_limit_ids"]

    # Initialize logger
    log_path = test_dir / SKIP_LOG_FILENAME
    logger = setup_logger(log_path)

    # Process ALL over-limit cascades
    for path in setup_test_cascades["over_limit_paths"]:
        try:
            load_cascade(path, node_limit=NODE_LIMIT, logger=logger)
        except Exception:
            pass

    # Read log file
    with open(log_path, "r") as f:
        log_content = f.read()

    # Verify ALL over-limit cascade IDs are logged
    for cid in over_limit_ids:
        assert log_content.count(cid) >= 1, (
            f"Each over-limit cascade ID '{cid}' should appear in {SKIP_LOG_FILENAME}"
        )
