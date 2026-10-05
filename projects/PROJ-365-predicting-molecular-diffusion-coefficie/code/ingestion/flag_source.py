import json
from pathlib import Path
from utils.config import get_project_root
from utils.logging import get_logger, log_info

logger = get_logger(__name__)

def main():
    """
    This script is a placeholder. The source flag is written by trigger_synthetic.py
    or fetch_real.py (via update_plan_md and then flag_source logic).
    However, to satisfy the task T007c, we ensure the flag is set correctly.
    In a real flow, this might be called after fetch_real.py or trigger_synthetic.py.
    For now, we assume the flag is already written by those scripts.
    But T000b says: "Upon success, immediately update plan.md...".
    And T007c says: "generate data_source_flag.json recording source".
    So we need a script that sets the flag based on what happened.
    Let's assume this script is called after fetch_real.py or trigger_synthetic.py.
    It checks which file exists and sets the flag.
    """
    root = get_project_root()
    raw_dir = root / "data" / "raw"
    plan_path = root / "plan.md"
    flag_path = root / "data" / "data_source_flag.json"

    dataset_path = raw_dir / "dataset.csv"

    # Determine source
    source = "unknown"
    if dataset_path.exists():
        # Check if plan has URL and we fetched it
        # For simplicity, if dataset exists and plan has URL, assume real.
        # Otherwise, synthetic.
        if plan_path.exists():
            content = plan_path.read_text()
            if "Dataset URL:" in content:
                source = "real"
            else:
                source = "synthetic"
        else:
            source = "synthetic"
    else:
        log_info(logger, "No dataset found. Cannot set source flag.")
        return

    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with open(flag_path, 'w') as f:
        json.dump({"source": source}, f, indent=2)
    log_info(logger, f"Source flag set to: {source}")

if __name__ == "__main__":
    main()