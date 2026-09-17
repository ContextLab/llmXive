import os
import sys
import yaml
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from simulation.logging_utils import compute_log_checksum

STATE_FILE = "state/projects/PROJ-034-quantifying-uncertainty-in-small-sample-.yaml"

def main():
    log_checksum = compute_log_checksum()
    if not log_checksum:
        print("Error: simulation.log not found or empty. Cannot compute checksum.")
        sys.exit(1)

    state_path = Path(STATE_FILE)
    if not state_path.exists():
        print(f"Error: State file {STATE_FILE} not found.")
        sys.exit(1)

    with open(state_path, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f) or {}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"]["simulation_log"] = log_checksum

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    print(f"Updated {STATE_FILE} with simulation_log checksum: {log_checksum}")

if __name__ == "__main__":
    main()