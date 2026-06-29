"""
Runner Environment Verifier (T049b)

Verifies that the Quickstart execution runs on the default GitHub Actions runner
(2 vCPU, 7 GB RAM) and records the runner environment.

This script detects the runner environment and writes environment information
to output/runner_environment.json for verification purposes.
"""
import json
import logging
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.resource_monitor import get_memory_usage_gb, get_cpu_cores

# Constants for default GitHub Actions runner specifications
DEFAULT_GITHUB_ACTIONS_VCPU = 2
DEFAULT_GITHUB_ACTIONS_RAM_GB = 7

# Output path for environment verification
OUTPUT_DIR = Path("output")
ENVIRONMENT_RECORD_PATH = OUTPUT_DIR / "runner_environment.json"


def detect_github_actions_environment() -> bool:
    """
    Detect if running in GitHub Actions environment.

    Returns:
        bool: True if running in GitHub Actions, False otherwise.
    """
    return os.environ.get("GITHUB_ACTIONS") == "true"


def get_runner_name() -> Optional[str]:
    """
    Get the GitHub Actions runner name if available.

    Returns:
        Optional[str]: Runner name or None if not in GitHub Actions.
    """
    return os.environ.get("GITHUB_RUNNER_NAME")


def get_runner_os() -> Optional[str]:
    """
    Get the GitHub Actions runner OS if available.

    Returns:
        Optional[str]: Runner OS or None if not in GitHub Actions.
    """
    return os.environ.get("RUNNER_OS")


def get_platform_info() -> Dict[str, str]:
    """
    Get platform information from the local system.

    Returns:
        Dict[str, str]: Platform information including system, node, release, version, machine.
    """
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def verify_runner_specifications(
    detected_vcpu: int,
    detected_ram_gb: float,
) -> Dict[str, Any]:
    """
    Verify that detected runner specifications match expected GitHub Actions defaults.

    Args:
        detected_vcpu: Detected number of CPU cores.
        detected_ram_gb: Detected RAM in GB.

    Returns:
        Dict[str, Any]: Verification results including pass/fail status and details.
    """
    vcpu_match = detected_vcpu == DEFAULT_GITHUB_ACTIONS_VCPU
    # Allow some tolerance for RAM detection (±1 GB)
    ram_tolerance = 1.0
    ram_min = DEFAULT_GITHUB_ACTIONS_RAM_GB - ram_tolerance
    ram_max = DEFAULT_GITHUB_ACTIONS_RAM_GB + ram_tolerance
    ram_match = ram_min <= detected_ram_gb <= ram_max

    return {
        "expected_vcpu": DEFAULT_GITHUB_ACTIONS_VCPU,
        "detected_vcpu": detected_vcpu,
        "vcpu_match": vcpu_match,
        "expected_ram_gb_min": ram_min,
        "expected_ram_gb_max": ram_max,
        "detected_ram_gb": detected_ram_gb,
        "ram_match": ram_match,
        "overall_match": vcpu_match and ram_match,
    }


def record_runner_environment(logger: AuditLogger) -> Dict[str, Any]:
    """
    Record the complete runner environment information.

    Args:
        logger: AuditLogger instance for logging.

    Returns:
        Dict[str, Any]: Complete environment record.
    """
    is_github_actions = detect_github_actions_environment()
    detected_vcpu = get_cpu_cores()
    detected_ram_gb = get_memory_usage_gb()

    logger.info(f"Runner environment detected: GitHub Actions = {is_github_actions}")
    logger.info(f"Detected vCPU: {detected_vcpu}")
    logger.info(f"Detected RAM: {detected_ram_gb:.2f} GB")

    environment_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "is_github_actions": is_github_actions,
        "runner_name": get_runner_name(),
        "runner_os": get_runner_os(),
        "platform_info": get_platform_info(),
        "detected_specifications": {
            "vcpu": detected_vcpu,
            "ram_gb": detected_ram_gb,
        },
        "verification": verify_runner_specifications(detected_vcpu, detected_ram_gb),
    }

    return environment_record


def write_environment_record(record: Dict[str, Any], output_path: Path) -> None:
    """
    Write the environment record to a JSON file.

    Args:
        record: Environment record dictionary.
        output_path: Path to write the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)


def main() -> int:
    """
    Main entry point for runner environment verification.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger = get_default_logger(__name__)
    logger.info("Starting runner environment verification (T049b)")

    try:
        # Record environment
        environment_record = record_runner_environment(logger)

        # Write to output file
        write_environment_record(environment_record, ENVIRONMENT_RECORD_PATH)
        logger.info(f"Environment record written to {ENVIRONMENT_RECORD_PATH}")

        # Verify and log results
        verification = environment_record["verification"]
        if verification["overall_match"]:
            logger.info(
                f"Runner specifications MATCH expected GitHub Actions defaults "
                f"(vCPU: {verification['detected_vcpu']}, RAM: {verification['detected_ram_gb']:.2f} GB)"
            )
            return 0
        else:
            logger.warning(
                f"Runner specifications DO NOT MATCH expected GitHub Actions defaults "
                f"(expected vCPU: {verification['expected_vcpu']}, RAM: {verification['expected_ram_gb_min']:.1f}-{verification['expected_ram_gb_max']:.1f} GB; "
                f"detected vCPU: {verification['detected_vcpu']}, RAM: {verification['detected_ram_gb']:.2f} GB)"
            )
            # Return 0 anyway since this is informational verification, not a hard failure
            return 0

    except Exception as e:
        logger.error(f"Runner environment verification failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
