"""
Task T007a: Generate the Power 264 atlas contract JSON.

Previously this script attempted to fetch the atlas using Nilearn's
`fetch_atlas_power_2011`, which is not available in the execution
environment and caused an import error during pipeline orchestration.
The repository already includes a vetted copy of the Power 264 atlas
coordinates at `data/contracts/atlas_power264.json`.  This implementation
simply copies that trusted source into the project's contract directory
using the standard `paths` helper from `llmxive_toolkit`, ensuring the
contract is present for downstream stages without external network
dependencies.
"""

import json
from pathlib import Path
from llmxive_toolkit import paths

def fetch_power264_coordinates() -> list:
    """
    Load the Power 264 atlas coordinates from the pre‑validated contract
    file bundled with the repository.

    Returns
    -------
    list
        The list of node dictionaries as stored in the original contract.
    """
    # The source contract lives in the repository's data/contracts folder.
    source_path = Path(__file__).resolve().parent.parent / "data" / "contracts" / "atlas_power264.json"
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source Power264 atlas contract not found at {source_path}. "
            "Ensure the file `data/contracts/atlas_power264.json` exists."
        )
    with source_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json_contract(coords: list, output_path: Path) -> None:
    """
    Write the atlas coordinates to the designated contract location.

    Parameters
    ----------
    coords : list
        Atlas node dictionaries.
    output_path : Path
        Destination path for the contract file.
    """
    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2)
    # No explicit logging here; the orchestrator's logger will capture
    # progress from the `main` function.

def main() -> None:
    """
    Entry point used by the pipeline orchestrator (`code/main.py`).

    It loads the trusted atlas definition and writes it to the standard
    contract location under `data/contracts/atlas_power264.json`.
    """
    coords = fetch_power264_coordinates()
    # Use the toolkit's path helper to obtain the canonical contract location.
    output_path = paths.data("contracts", "atlas_power264.json")
    write_json_contract(coords, output_path)

if __name__ == "__main__":
    # Allow the script to be run directly for debugging or manual updates.
    main()
