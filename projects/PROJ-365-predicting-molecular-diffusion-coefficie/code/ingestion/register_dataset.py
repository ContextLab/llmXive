import argparse
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# Import project root helper
try:
    from utils.config import get_project_root
except ImportError:
    # Fallback if utils.config is not available – use current working directory
    def get_project_root() -> Path:
        return Path(__file__).resolve().parents[2]

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute the SHA256 checksum of the given file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hexadecimal SHA256 checksum.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _verified_datasets_path() -> Path:
    """Return the absolute path to the verified datasets JSON file."""
    return get_project_root() / "data" / "verified_datasets.json"

def load_verified_datasets() -> List[Dict]:
    """
    Load the list of verified dataset records from the JSON file.
    Returns an empty list if the file does not exist.
    """
    path = _verified_datasets_path()
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            # If the file exists but does not contain a list, treat as corrupted.
            return []
    except json.JSONDecodeError:
        # Corrupted JSON – start fresh
        return []

def save_verified_datasets(datasets: List[Dict]) -> None:
    """
    Persist the list of verified dataset records to the JSON file.
    The file is written with an indentation of 2 spaces for readability.
    """
    path = _verified_datasets_path()
    # Ensure the data directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(datasets, f, indent=2, sort_keys=True)

def update_plan_with_registry_reference(plan_path: Path) -> None:
    """
    Ensure that ``plan.md`` contains a reference line to the verified datasets
    registry file. If the line already exists, it is left unchanged.
    The reference line format is:

    ``Verified Datasets Registry: data/verified_datasets.json``

    Parameters
    ----------
    plan_path: Path
        Absolute path to the project's ``plan.md`` file.
    """
    reference_line = "Verified Datasets Registry: data/verified_datasets.json"
    if not plan_path.is_file():
        # If plan.md does not exist, create it with the reference line.
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(reference_line + "\n", encoding="utf-8")
        return

    content = plan_path.read_text(encoding="utf-8").splitlines()
    if any(reference_line in line for line in content):
        # Reference already present – nothing to do.
        return

    # Append the reference line at the end of the file.
    with plan_path.open("a", encoding="utf-8") as f:
        f.write("\n" + reference_line + "\n")

def register_dataset(url: str, file_path: Path, source_type: str) -> None:
    """
    Register a successfully downloaded dataset.

    This function computes the SHA256 checksum of the provided file, creates a
    record containing the URL, checksum, download timestamp, and source type,
    appends the record to ``data/verified_datasets.json``, and updates
    ``plan.md`` to reference the registry.

    Parameters
    ----------
    url: str
        The URL from which the dataset was downloaded.
    file_path: Path
        Path to the downloaded dataset file.
    source_type: str
        Identifier for the source (e.g., ``NIST`` or ``Zenodo``).
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    checksum = compute_file_checksum(file_path)
    record = {
        "url": url,
        "checksum_sha256": checksum,
        "download_date_iso": datetime.now(timezone.utc).isoformat(),
        "source_type": source_type,
    }

    datasets = load_verified_datasets()
    datasets.append(record)
    save_verified_datasets(datasets)

    # Update plan.md
    plan_path = get_project_root() / "plan.md"
    update_plan_with_registry_reference(plan_path)

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Register a downloaded molecular diffusion dataset in the verified "
            "registry. The script computes a SHA256 checksum, stores metadata, "
            "and updates ``plan.md`` with a reference to the registry file."
        )
    )
    parser.add_argument(
        "--url",
        required=True,
        help="The URL from which the dataset was downloaded.",
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the downloaded dataset file (e.g., data/raw/dataset.csv).",
    )
    parser.add_argument(
        "--source-type",
        required=True,
        help="Identifier for the source (e.g., NIST, Zenodo).",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    """
    Entry point for the ``register_dataset`` script.

    It parses command‑line arguments and invokes :func:`register_dataset`.
    """
    args = _parse_args(argv)
    try:
        register_dataset(url=args.url, file_path=args.file, source_type=args.source_type)
    except Exception as e:
        # Print the error to stderr and exit with a non‑zero status to signal failure.
        sys.stderr.write(f"Error registering dataset: {e}\\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
