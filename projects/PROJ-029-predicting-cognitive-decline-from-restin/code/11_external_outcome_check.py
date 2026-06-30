"""
Task T025: External Outcome Check for MCI Conversion Data.

Checks if the dataset (ds000246) contains MCI conversion data.
If unavailable, writes a limitation note to data/artifacts/limitations.txt.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import load_json, ensure_dir

# Constants
DATASET_JSON_PATH = "data/raw/ds000246/dataset_description.json"
LIMITATIONS_FILE = "data/artifacts/limitations.txt"
MCI_KEYWORDS = ["mci", "conversion", "longitudinal_mci", "mci_status", "mci_convert"]

def check_mci_availability(data_dir: Path, logger) -> bool:
    """
    Checks for MCI conversion data in the dataset.
    
    Strategy:
    1. Check dataset_description.json for keywords.
    2. Scan participants.tsv (if exists) for MCI-related columns.
    3. Scan JSON sidecars for MCI-related keys.
    
    Returns True if MCI data is found, False otherwise.
    """
    logger.info("Checking for MCI conversion data availability...")
    
    # 1. Check dataset_description.json
    ds_desc_path = data_dir / "dataset_description.json"
    if ds_desc_path.exists():
        try:
            ds_data = load_json(ds_desc_path)
            ds_text = json.dumps(ds_data).lower()
            for keyword in MCI_KEYWORDS:
                if keyword in ds_text:
                    logger.info(f"Found potential MCI indicator in dataset_description.json: {keyword}")
                    return True
        except Exception as e:
            logger.warning(f"Could not parse dataset_description.json: {e}")

    # 2. Check participants.tsv for MCI columns
    participants_path = data_dir / "participants.tsv"
    if participants_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(participants_path, sep='\t')
            columns = [str(c).lower() for c in df.columns]
            for keyword in MCI_KEYWORDS:
                if any(keyword in col for col in columns):
                    logger.info(f"Found MCI-related column in participants.tsv: {keyword}")
                    return True
        except Exception as e:
            logger.warning(f"Could not parse participants.tsv: {e}")

    # 3. Scan a sample of JSON sidecars if available (optional deep check)
    # We limit this to avoid long scans on large datasets
    json_files = list(data_dir.rglob("*.json"))
    # Only check top 50 to save time
    for json_file in json_files[:50]:
        if "dataset" in json_file.name or "participants" in json_file.name:
            continue # Already checked
        try:
            with open(json_file, 'r') as f:
                content = f.read().lower()
                for keyword in MCI_KEYWORDS:
                    if keyword in content:
                        logger.info(f"Found MCI indicator in {json_file}: {keyword}")
                        return True
        except Exception:
            continue

    logger.info("No MCI conversion data found in dataset.")
    return False

def write_limitation_note(output_path: Path, logger):
    """
    Writes a limitation note to the specified file.
    """
    ensure_dir(output_path.parent)
    note = """
Limitation Note: External Outcome Data (MCI Conversion)
-------------------------------------------------------
The dataset ds000246 (Constitution VI, FR-001) was analyzed for MCI conversion
labels (e.g., 'mci_status', 'conversion'). No explicit MCI conversion outcomes
were found in the dataset metadata or participant files.

Consequently, the predictive model in this study is trained to predict cognitive
decline defined strictly by the drop in MMSE/MOCA scores (>= 3 points) between
longitudinal timepoints, as defined in Task T023. The model does NOT predict
clinical MCI conversion status.

This limitation should be noted when interpreting the clinical relevance of the
model's predictions regarding progression to MCI.
"""
    with open(output_path, 'w') as f:
        f.write(note.strip())
    logger.info(f"Limitation note written to {output_path}")

def main():
    logger = get_logger("external_outcome_check")
    project_root = Path(__file__).parent.parent
    data_raw_dir = project_root / "data" / "raw" / "ds000246"
    limitations_path = project_root / "data" / "artifacts" / "limitations.txt"

    if not data_raw_dir.exists():
        logger.error(f"Dataset directory not found: {data_raw_dir}")
        logger.error("Please ensure T017 (download_and_filter) has been run successfully.")
        sys.exit(1)

    mci_found = check_mci_availability(data_raw_dir, logger)

    if not mci_found:
        write_limitation_note(limitations_path, logger)
        logger.info("External outcome check completed. Limitation note generated.")
    else:
        logger.info("MCI conversion data found. No limitation note needed.")
        # Optionally, we could log that we have it, but the task specifically
        # asks to write the note if unavailable.

    return 0

if __name__ == "__main__":
    sys.exit(main())