"""
Hashing module for agent logs.
Computes SHA256 hashes for all artifacts in data/results/agent_logs/
and generates a manifest file.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from utils.hash_artifacts import compute_sha256, hash_directory, generate_manifest
from config import get_path, get_config_summary


def hash_agent_logs_directory(output_dir: Path) -> Dict[str, Any]:
    """
    Hash all artifacts in the agent logs directory.

    Args:
        output_dir: Path to the directory containing agent logs (data/results/agent_logs/)

    Returns:
        Dictionary containing hash results and manifest path
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"Agent logs directory not found: {output_dir}")

    # Hash the entire directory
    manifest_data = hash_directory(
        directory=output_dir,
        output_manifest_path=output_dir.parent / "agent_logs_manifest.json"
    )

    return manifest_data


def main() -> int:
    """
    Main entry point for hashing agent logs.
    """
    config_summary = get_config_summary()
    print(f"Starting agent log hashing with config: {config_summary}")

    try:
        # Get the agent logs directory path
        agent_logs_dir = get_path("agent_logs")
        print(f"Hashing agent logs in: {agent_logs_dir}")

        if not agent_logs_dir.exists():
            print(f"Error: Agent logs directory does not exist: {agent_logs_dir}")
            print("Run the agent execution pipeline first to generate logs.")
            return 1

        # Hash the directory
        result = hash_agent_logs_directory(agent_logs_dir)

        print(f"Hashing complete.")
        print(f"Manifest saved to: {result['manifest_path']}")
        print(f"Total files hashed: {result['file_count']}")
        print(f"Directory hash: {result['directory_hash']}")

        # Print summary of hashed files
        print("\nHashed files:")
        for file_info in result['files']:
            print(f"  {file_info['relative_path']}: {file_info['sha256'][:16]}...")

        return 0

    except Exception as e:
        print(f"Error during hashing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
