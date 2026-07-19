import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from data_loader import fetch_advbench, fetch_hf4
from config import get_path, ensure_directories

def generate_static_fixture() -> Path:
    """
    Generate a static test fixture combining a sample of AdvBench and HF4 data.
    Saves to data/test_static_logs.json.
    """
    ensure_directories()
    output_path = get_path("test_dir") / "test_static_logs.json"

    advbench_logs = fetch_advbench()
    hf4_logs = fetch_hf4()

    # Take a small sample to keep the fixture manageable
    sample_size = 100
    combined_logs = (advbench_logs[:sample_size] + hf4_logs[:sample_size])

    with open(output_path, "w") as f:
        json.dump(combined_logs, f, indent=2)

    print(f"Generated fixture at {output_path} with {len(combined_logs)} logs.")
    return output_path

if __name__ == "__main__":
    generate_static_fixture()
