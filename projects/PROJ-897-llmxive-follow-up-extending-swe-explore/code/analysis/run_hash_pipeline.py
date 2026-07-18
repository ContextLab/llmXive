"""
Pipeline script to run the complete hashing workflow for User Story 2.
This script orchestrates hashing of curated data and agent logs.
"""
import sys
from pathlib import Path

from utils.hash_artifacts import hash_directory
from config import get_path, get_config_summary


def hash_curated_data() -> bool:
    """Hash the curated data directory."""
    curated_dir = get_path("curated")
    if not curated_dir.exists():
        print(f"Warning: Curated data directory not found: {curated_dir}")
        return False

    print(f"Hashing curated data in: {curated_dir}")
    manifest = hash_directory(
        directory=curated_dir,
        output_manifest_path=curated_dir.parent / "curated_manifest.json"
    )
    print(f"Curated data hashed. Manifest: {manifest['manifest_path']}")
    return True


def hash_agent_logs() -> bool:
    """Hash the agent logs directory."""
    logs_dir = get_path("agent_logs")
    if not logs_dir.exists():
        print(f"Warning: Agent logs directory not found: {logs_dir}")
        return False

    print(f"Hashing agent logs in: {logs_dir}")
    manifest = hash_directory(
        directory=logs_dir,
        output_manifest_path=logs_dir.parent / "agent_logs_manifest.json"
    )
    print(f"Agent logs hashed. Manifest: {manifest['manifest_path']}")
    return True


def hash_final_metrics() -> bool:
    """Hash the final metrics file."""
    metrics_path = get_path("final_metrics")
    if not metrics_path.exists():
        print(f"Warning: Final metrics file not found: {metrics_path}")
        return False

    from analysis.hash_final_metrics import hash_final_metrics_file
    print(f"Hashing final metrics: {metrics_path}")
    result = hash_final_metrics_file(metrics_path)
    print(f"Final metrics hashed. Manifest: {result['manifest_path']}")
    return True


def main() -> int:
    """
    Main entry point for the hashing pipeline.
    """
    config_summary = get_config_summary()
    print(f"Starting hashing pipeline with config: {config_summary}")
    print("-" * 60)

    results = {
        "curated_data": False,
        "agent_logs": False,
        "final_metrics": False
    }

    # Step 1: Hash curated data (from US1)
    results["curated_data"] = hash_curated_data()
    print()

    # Step 2: Hash agent logs (from US2 - T026)
    results["agent_logs"] = hash_agent_logs()
    print()

    # Step 3: Hash final metrics (from US3)
    results["final_metrics"] = hash_final_metrics()
    print()

    # Summary
    print("-" * 60)
    print("Hashing Pipeline Summary:")
    for step, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {step}")

    if all(results.values()):
        print("\nAll artifacts hashed successfully.")
        return 0
    else:
        print("\nSome artifacts were missing or could not be hashed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())