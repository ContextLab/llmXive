"""
Generate synthetic audit logs (INPUT DATA) for the SPEAR benchmark.

This module generates deterministic synthetic data representing audit logs
for the SPEAR (Smart Protocol for Evaluation of Agent Robustness) benchmark.
The data is structured to be consumed by the simulation runners (e.g., spear_runner.py).

Output is deterministic based on provided random seeds.
"""

import json
import os
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root if run as a script
import sys
from pathlib import Path

# Add project root to path for imports if necessary
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from foundation_protocol.utils import log_seed, get_hash


# Constants for synthetic data generation
AGENT_TYPES = ["validator", "auditor", "executor", "coordinator"]
ACTION_TYPES = [
    "initiate_transaction",
    "validate_block",
    "execute_contract",
    "submit_audit",
    "request_checkpoint",
    "recover_state",
    "broadcast_message"
]
STATUS_TYPES = ["success", "partial_success", "failed", "timeout", "recovered"]
FAILURE_MODES = [
    "network_partition",
    "node_crash",
    "double_spend_attempt",
    "consensus_failure",
    "timeout",
    "malformed_message"
]

# Output configuration
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "spear_audit_logs.json"
METADATA_FILE = OUTPUT_DIR / "spear_metadata.json"


def generate_audit_id(seed: int, index: int) -> str:
    """Generate a deterministic unique ID for an audit log entry."""
    log_seed(seed)
    unique_str = f"{seed}-{index}-{datetime.now().isoformat()}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:16]


def generate_timestamp(base_time: datetime, offset_seconds: float) -> str:
    """Generate a deterministic timestamp string."""
    ts = base_time + timedelta(seconds=offset_seconds)
    return ts.isoformat() + "Z"


def generate_audit_entry(
    seed: int,
    index: int,
    base_time: datetime,
    time_offset: float,
    include_failure: bool = False
) -> Dict[str, Any]:
    """Generate a single synthetic audit log entry."""
    log_seed(seed)

    entry_id = generate_audit_id(seed, index)

    # Deterministic selection based on seed and index
    random.seed(seed + index)

    sender_id = f"agent_{random.randint(1000, 9999)}"
    receiver_id = f"agent_{random.randint(1000, 9999)}"
    agent_type = random.choice(AGENT_TYPES)
    action = random.choice(ACTION_TYPES)

    # Status logic
    if include_failure:
        status = random.choice(["failed", "timeout", "recovered"])
        failure_mode = random.choice(FAILURE_MODES)
    else:
        status = random.choices(
            STATUS_TYPES,
            weights=[0.85, 0.05, 0.03, 0.02, 0.05]
        )[0]
        failure_mode = None

    # Payload size simulation (bytes)
    payload_size = random.randint(256, 65536)

    # Latency simulation (ms)
    latency_ms = random.uniform(1.0, 500.0) if status != "timeout" else random.uniform(5000.0, 30000.0)

    entry = {
        "audit_id": entry_id,
        "timestamp": generate_timestamp(base_time, time_offset),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "agent_type": agent_type,
        "action": action,
        "status": status,
        "payload_size_bytes": payload_size,
        "latency_ms": round(latency_ms, 3),
        "checkpoint_ref": f"ckpt_{seed}_{index}" if status == "recovered" else None,
        "failure_mode": failure_mode,
        "metadata": {
            "seed": seed,
            "entry_index": index,
            "protocol_version": "1.0.0",
            "environment": "synthetic_spear_benchmark"
        }
    }

    return entry


def generate_spear_dataset(
    num_seeds: int = 5,
    entries_per_seed: int = 100,
    failure_rate: float = 0.15,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate the complete SPEAR benchmark dataset.

    Args:
        num_seeds: Number of distinct random seeds to generate data for.
        entries_per_seed: Number of audit log entries per seed.
        failure_rate: Probability that an entry will be a failure/recovery scenario.
        output_dir: Directory to write output files. Defaults to 'data'.

    Returns:
        Dictionary containing metadata about the generation process.
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    all_entries = []
    generation_seeds = []

    base_time = datetime(2024, 1, 1, 0, 0, 0)

    print(f"Generating SPEAR dataset with {num_seeds} seeds, {entries_per_seed} entries each...")

    for seed_idx in range(num_seeds):
        # Use a deterministic seed value
        seed_value = 42 + seed_idx * 17  # Prime multiplier for distribution
        generation_seeds.append(seed_value)

        print(f"  Generating seed {seed_value}...")

        for i in range(entries_per_seed):
            # Determine if this entry should be a failure
            random.seed(seed_value + i)
            is_failure = random.random() < failure_rate

            entry = generate_audit_entry(
                seed=seed_value,
                index=i,
                base_time=base_time,
                time_offset=i * 0.5,  # 0.5 second intervals
                include_failure=is_failure
            )
            all_entries.append(entry)

    # Sort entries by timestamp for realistic ordering
    all_entries.sort(key=lambda x: x["timestamp"])

    # Write main dataset
    dataset_path = output_dir / "spear_audit_logs.json"
    with open(dataset_path, "w") as f:
        json.dump(all_entries, f, indent=2)

    # Write metadata
    metadata = {
        "dataset_name": "SPEAR Synthetic Audit Logs",
        "version": "1.0.0",
        "generation_timestamp": datetime.now().isoformat(),
        "total_entries": len(all_entries),
        "num_seeds": num_seeds,
        "entries_per_seed": entries_per_seed,
        "failure_rate": failure_rate,
        "seeds_used": generation_seeds,
        "output_file": str(dataset_path),
        "file_hash": get_hash(str(dataset_path)),
        "schema_version": "spear_audit_v1"
    }

    metadata_path = output_dir / "spear_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Dataset generated: {dataset_path}")
    print(f"Metadata written: {metadata_path}")
    print(f"Total entries: {len(all_entries)}")

    return metadata


def main():
    """Main entry point for script execution."""
    print("Starting SPEAR dataset generation...")

    # Generate with default parameters (can be overridden via CLI in future)
    metadata = generate_spear_dataset(
        num_seeds=5,
        entries_per_seed=100,
        failure_rate=0.15
    )

    print("SPEAR dataset generation complete.")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")


if __name__ == "__main__":
    main()