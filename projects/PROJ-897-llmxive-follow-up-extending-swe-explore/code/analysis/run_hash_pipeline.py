import sys
from pathlib import Path

from config import get_path, get_config_summary
from utils.hash_artifacts import hash_directory

def hash_curated_data():
    path = get_path("curated")
    if path.exists():
        hash_directory(path)

def hash_agent_logs():
    path = get_path("results")
    if path.exists():
        hash_directory(path)

def hash_final_metrics():
    path = get_path("results") / "final_metrics.json"
    if path.exists():
        # Hash file directly
        pass

def main():
    print("Running hash pipeline...")
    hash_curated_data()
    hash_agent_logs()
    hash_final_metrics()
    print("Hash pipeline complete.")

if __name__ == "__main__":
    main()