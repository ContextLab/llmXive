"""
data/download.py
-----------------
Implements the strict "Fail Loudly" logic for acquiring the user‑provided
HEA yield‑strength dataset.

The script expects the raw dataset CSV to be present at
``data/raw/heas_raw.csv``.  If the file is missing or unreadable, a
``FileNotFoundError`` is raised with an explicit, user‑facing error
message.  This message is documented verbatim in the project README
(see ``README.md``) so that users know exactly what to look for.

The function returns the string ``"SUCCESS"`` when the file exists.
"""

import os
from typing import Optional

from utils.logging import get_logger
from utils.config import get_config

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_DATASET_REL_PATH = os.path.join("data", "raw", "heas_raw.csv")
MISSING_DATASET_ERROR_MSG = (
    f"FileNotFoundError: Required dataset file '{DEFAULT_DATASET_REL_PATH}' not found. "
    "Please place the dataset at this path before running the pipeline."
)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def download_dataset(dataset_path: Optional[str] = None) -> str:
    """
    Validate the presence of the user‑provided dataset.

    Parameters
    ----------
    dataset_path : str, optional
        Path to the raw CSV file.  If ``None`` the default location
        ``data/raw/heas_raw.csv`` is used.

    Returns
    -------
    str
        ``"SUCCESS"`` if the file is present.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the expected location.
    """
    logger = get_logger(__name__)

    # Resolve the path: honour an explicit argument, otherwise fall back to the
    # default location used throughout the project.
    path_to_check = dataset_path or DEFAULT_DATASET_REL_PATH
    logger.debug("Checking for user‑provided dataset at %s", path_to_check)

    if not os.path.isfile(path_to_check):
        # Raising with the exact message required by the README.
        raise FileNotFoundError(MISSING_DATASET_ERROR_MSG)

    logger.info("User‑provided dataset found at %s", path_to_check)
    return "SUCCESS"


def main() -> None:
    """
    Entry‑point for ``python -m code.data.download``.

    The function simply calls :func:`download_dataset` and prints the
    returned status.  Any ``FileNotFoundError`` bubbles up, causing the
    process to abort with a non‑zero exit code – exactly what the
    verification step expects.
    """
    status = download_dataset()
    print(status)


if __name__ == "__main__":
    main()
