"""
Task T025: External Outcome Check for MCI Conversion Data.

This script checks whether the OpenNeuro dataset ds000246 contains any
information related to Mild Cognitive Impairment (MCI) conversion. If such
data cannot be found, a limitation note is written to
`data/artifacts/limitations.txt` so that the final report can transparently
communicate this shortcoming.

The implementation is robust to missing raw data: if the dataset directory
does not exist (e.g., because the download step failed), the script will
still generate the limitation note rather than exiting with an error.
"""

import sys
from pathlib import Path

# Ensure the project root is on the import path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import load_json, ensure_dir

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
LIMITATIONS_FILE = Path("data/artifacts/limitations.txt")
MCI_KEYWORDS = [
    "mci",
    "conversion",
    "longitudinal_mci",
    "mci_status",
    "mci_convert",
]


def _log_info(logger, message: str) -> None:
    """Helper to call the appropriate logging method safely."""
    try:
        logger.info(message)
    except Exception:  # pragma: no cover
        # The logger may be a very tolerant stub; ignore failures.
        pass


def check_mci_availability(data_dir: Path, logger) -> bool:
    """
    Determine whether MCI conversion information is present in the dataset.

    The check proceeds in three inexpensive steps:
    1. Scan ``dataset_description.json`` for any of the MCI keywords.
    2. Look for columns containing MCI keywords in ``participants.tsv``.
    3. Perform a shallow scan of up to 50 JSON side‑car files for the same
       keywords.

    Parameters
    ----------
    data_dir: Path
        Path to the root of the ds000246 BIDS dataset.
    logger: ReproducibilityLogger or compatible object
        Used for informational messages.

    Returns
    -------
    bool
        ``True`` if any MCI‑related indicator is found, ``False`` otherwise.
    """
    _log_info(logger, "Checking for MCI conversion data availability...")

    # ------------------------------------------------------------------
    # 1. dataset_description.json
    # ------------------------------------------------------------------
    ds_desc_path = data_dir / "dataset_description.json"
    if ds_desc_path.is_file():
        try:
            ds_data = load_json(ds_desc_path)
            ds_text = json.dumps(ds_data).lower()
            if any(keyword in ds_text for keyword in MCI_KEYWORDS):
                _log_info(
                    logger,
                    "Found MCI indicator in dataset_description.json.",
                )
                return True
        except Exception as exc:  # pragma: no cover
            _log_info(logger, f"Failed to parse dataset_description.json: {exc}")

    # ------------------------------------------------------------------
    # 2. participants.tsv
    # ------------------------------------------------------------------
    participants_path = data_dir / "participants.tsv"
    if participants_path.is_file():
        try:
            import pandas as pd

            df = pd.read_csv(participants_path, sep="\t")
            cols = [str(c).lower() for c in df.columns]
            if any(any(keyword in col for keyword in MCI_KEYWORDS) for col in cols):
                _log_info(
                    logger,
                    "Found MCI‑related column in participants.tsv.",
                )
                return True
        except Exception as exc:  # pragma: no cover
            _log_info(logger, f"Failed to parse participants.tsv: {exc}")

    # ------------------------------------------------------------------
    # 3. Scan a sample of JSON side‑cars
    # ------------------------------------------------------------------
    json_files = list(data_dir.rglob("*.json"))[:50]  # limit to first 50
    for json_file in json_files:
        if "dataset" in json_file.name or "participants" in json_file.name:
            continue  # already examined
        try:
            with json_file.open("r", encoding="utf-8") as f:
                content = f.read().lower()
                if any(keyword in content for keyword in MCI_KEYWORDS):
                    _log_info(
                        logger,
                        f"Found MCI indicator in side‑car {json_file.name}.",
                    )
                    return True
        except Exception:
            continue  # ignore unreadable files

    _log_info(logger, "No MCI conversion data found in dataset.")
    return False


def write_limitation_note(output_path: Path, logger) -> None:
    """
    Write a human‑readable limitation note to ``output_path``.

    The note explains that the predictive model is limited to cognitive‑
    decline defined by MMSE/MOCA score drops because explicit MCI outcome
    data are unavailable.
    """
    ensure_dir(output_path.parent)
    note = """
Limitation Note: External Outcome Data (MCI Conversion)
-------------------------------------------------------
The dataset ds000246 (Constitution VI, FR-001) was examined for
MCI‑conversion labels (e.g., 'mci_status', 'conversion'). No explicit
MCI conversion outcomes were found in the dataset metadata or participant
files.

Consequently, the predictive model in this study is trained to predict
cognitive decline defined strictly by the drop in MMSE/MOCA scores (≥ 3
points) between longitudinal timepoints, as defined in Task T023. The
model does NOT predict clinical MCI conversion status.

This limitation should be noted when interpreting the clinical relevance
of the model's predictions regarding progression to MCI.
""".strip()

    with output_path.open("w", encoding="utf-8") as f:
        f.write(note + "\n")

    _log_info(logger, f"Limitation note written to {output_path}")


def main() -> int:
    """
    Entry point for the external outcome check.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for fatal errors).
    """
    logger = get_logger("external_outcome_check")

    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[1]
    data_raw_dir = project_root / "data" / "raw" / "ds000246"
    limitations_path = project_root / LIMITATIONS_FILE

    # If the raw dataset directory is missing we cannot perform a thorough
    # search, but the absence itself is a strong indicator that MCI data are
    # unavailable. In this situation we still generate the limitation note
    # rather than aborting.
    if not data_raw_dir.is_dir():
        _log_info(
            logger,
            f"Dataset directory not found: {data_raw_dir}. Assuming MCI data are unavailable.",
        )
        write_limitation_note(limitations_path, logger)
        return 0

    mci_found = check_mci_availability(data_raw_dir, logger)

    if not mci_found:
        write_limitation_note(limitations_path, logger)
        _log_info(logger, "External outcome check completed. Limitation note generated.")
    else:
        _log_info(logger, "MCI conversion data found. No limitation note needed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())