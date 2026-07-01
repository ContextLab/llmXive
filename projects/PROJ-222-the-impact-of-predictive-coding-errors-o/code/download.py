import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Importing from sibling modules as per project API surface
# Note: In a real environment, these would be installed or on the path.
# Assuming config.py exists for seed and paths as per T007/T001.
try:
    from config import get_data_dir, get_config
except ImportError:
    # Fallback for standalone execution if config is not yet fully integrated
    # or to avoid circular dependency during initial setup.
    # We define minimal defaults if config is missing.
    def get_data_dir():
        return Path("data")
    
    def get_config():
        return {}

REQUIRED_COLUMNS = ["duration_estimate", "stimulus_sequence", "participant_id"]
GATE0_STATUS_FILE = "gate0_status.json"

def parse_readme_datasets(readme_path: str) -> List[Dict[str, Any]]:
    """
    Parses data/README.md to extract dataset IDs and sources.
    Expected format in README:
    ### Verified datasets
    - id: openml_123
      source: openml
      type: time_perception
    - id: hf_dataset_name
      source: huggingface
      type: time_perception
    """
    datasets = []
    readme_file = Path(readme_path)
    if not readme_file.exists():
        return datasets

    in_verified_section = False
    current_dataset = {}

    with open(readme_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if "### Verified datasets" in line or "Verified datasets" in line:
                in_verified_section = True
                continue
            if in_verified_section:
                if line.startswith("- id:"):
                    if current_dataset:
                        datasets.append(current_dataset)
                    current_dataset = {"id": line.split("id:", 1)[1].strip()}
                elif line.startswith("source:"):
                    current_dataset["source"] = line.split("source:", 1)[1].strip()
                elif line.startswith("type:"):
                    current_dataset["type"] = line.split("type:", 1)[1].strip()
                elif line.startswith("###") and "Verified datasets" not in line:
                    # End of section
                    if current_dataset:
                        datasets.append(current_dataset)
                        current_dataset = {}
                    in_verified_section = False
                elif line and not line.startswith("#"):
                    # Handle key: value on same line or continuation if format varies
                    if ":" in line and not line.startswith("-"):
                        key, val = line.split(":", 1)
                        current_dataset[key.strip()] = val.strip()
    
    if current_dataset:
        datasets.append(current_dataset)

    return datasets

def fetch_openml_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a dataset from OpenML.
    Requires: openml==0.14.2
    """
    try:
        import openml
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, categorical, feature_names = dataset.get_data(dataset_format="dataframe", target=dataset.default_target_attribute)
        
        # Return as a dictionary-like object or DataFrame
        # We assume the dataset has the necessary columns or can be mapped
        return {
            "source": "openml",
            "id": dataset_id,
            "data": X,
            "target": y,
            "feature_names": feature_names
        }
    except Exception as e:
        print(f"Error fetching OpenML dataset {dataset_id}: {e}", file=sys.stderr)
        return None

def fetch_huggingface_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a dataset from HuggingFace.
    Requires: datasets==2.14.0
    """
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_id, split="train")
        # Convert to pandas for consistency if needed, or keep as Dataset
        # Assuming we need a pandas DataFrame for column checks
        df = ds.to_pandas()
        return {
            "source": "huggingface",
            "id": dataset_id,
            "data": df,
            "feature_names": list(df.columns)
        }
    except Exception as e:
        print(f"Error fetching HuggingFace dataset {dataset_id}: {e}", file=sys.stderr)
        return None

def validate_gate0(dataset_info: Dict[str, Any]) -> tuple[bool, str]:
    """
    Gate 0 Logic:
    Verifies presence of required columns: duration_estimate, stimulus_sequence, participant_id.
    Returns (is_valid, reason).
    """
    data = dataset_info.get("data")
    if data is None:
        return False, "No data loaded"

    # Check if data has columns attribute (pandas DataFrame)
    if hasattr(data, 'columns'):
        columns = list(data.columns)
        missing = [col for col in REQUIRED_COLUMNS if col not in columns]
        if missing:
            return False, f"Missing required columns: {missing}"
        return True, "All required columns present"
    else:
        # Fallback for non-pandas structures if necessary, though spec implies CSV/DataFrame
        return False, "Data structure does not support column inspection (expected DataFrame)"

def write_gate_status(status: str, reason: str, output_path: str = GATE0_STATUS_FILE):
    """
    Writes the Gate 0 status to a JSON file.
    """
    status_data = {
        "status": status,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    print(f"Gate 0 status written to {output_path}: {status} - {reason}")

def run_download_pipeline():
    """
    Main pipeline execution for T013 (Gate 0) and T012 (Download).
    1. Reads data/README.md for verified datasets.
    2. Attempts to fetch each dataset.
    3. Runs Gate 0 validation on each.
    4. If any valid dataset is found, logs success and exits.
    5. If NO valid dataset is found after checking all, writes gate0_status.json with status="blocked".
    """
    readme_path = "data/README.md"
    datasets = parse_readme_datasets(readme_path)

    if not datasets:
        write_gate_status("blocked", "No datasets listed in data/README.md")
        return

    valid_datasets = []
    blocked_reasons = []

    for ds in datasets:
        ds_id = ds.get("id")
        source = ds.get("source", "unknown")
        print(f"Processing dataset: {ds_id} from {source}")

        fetched_data = None
        if source == "openml":
            fetched_data = fetch_openml_dataset(ds_id)
        elif source == "huggingface":
            fetched_data = fetch_huggingface_dataset(ds_id)
        else:
            blocked_reasons.append(f"Unknown source: {source} for {ds_id}")
            continue

        if fetched_data is None:
            blocked_reasons.append(f"Failed to fetch {ds_id} from {source}")
            continue

        is_valid, reason = validate_gate0(fetched_data)
        if is_valid:
            valid_datasets.append(fetched_data)
            print(f"Gate 0 PASSED for {ds_id}")
        else:
            blocked_reasons.append(f"Gate 0 FAILED for {ds_id}: {reason}")

    if valid_datasets:
        write_gate_status("passed", f"Found {len(valid_datasets)} valid dataset(s).")
        # In a full pipeline, we would save these to data/processed here.
        # For T013, we just confirm Gate 0 is passed.
        return True
    else:
        write_gate_status("blocked", "; ".join(blocked_reasons) if blocked_reasons else "No valid datasets found.")
        return False

if __name__ == "__main__":
    success = run_download_pipeline()
    sys.exit(0 if success else 1)
