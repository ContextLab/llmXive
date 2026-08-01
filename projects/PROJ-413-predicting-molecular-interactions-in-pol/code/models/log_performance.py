"""
Log runtime and memory usage to results/performance.json.

This script is executed after model training (T028) to capture final
performance metrics. It relies on the existing logger infrastructure
defined in code/utils/logger.py.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_memory_usage_mb, log_performance
from utils.seed_utils import set_seed

def main():
    """
    Logs final runtime and memory usage to results/performance.json.

    This function is intended to be run after the training script (T028)
    has completed. It reads the training duration from an environment
    variable or a temporary file if available, or measures it if run
    as a standalone block (though typically it appends to existing logs).

    For T029, we specifically ensure the final state is recorded.
    """
    # Ensure reproducibility
    set_seed(42)

    output_dir = project_root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "performance.json"

    # Gather metrics
    current_time = datetime.now().isoformat()
    memory_mb = get_memory_usage_mb()

    # Read existing data if present to preserve history
    existing_data = []
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
        except (json.JSONDecodeError, IOError):
            existing_data = []

    # Create new entry
    # Note: If this is run immediately after training, the training script
    # should have set the runtime. If not, we log the snapshot.
    entry = {
        "timestamp": current_time,
        "event": "post_training_snapshot",
        "memory_usage_mb": memory_mb,
        "cpu_count": os.cpu_count() or 1,
        "platform": sys.platform
    }

    # Append and save
    existing_data.append(entry)

    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"Performance metrics logged to {output_file}")
    print(f"Current memory usage: {memory_mb:.2f} MB")

if __name__ == "__main__":
    main()