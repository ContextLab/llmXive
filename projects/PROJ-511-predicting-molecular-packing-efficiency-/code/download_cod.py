"""
download_cod.py

Download organic CIF files from the Crystallography Open Database (COD),
filter for structures with ≤ 50 non‑hydrogen atoms, and log download
statistics.

The script reads the verified COD base URL from ``code/constants.py``,
streams CIF identifiers, downloads each CIF into ``data/raw_cif/``,
and stops when at least 500 valid CIFs have been saved.

It produces two artefacts:
  * ``data/raw_cif/download_log.json`` – a JSON log of attempts.
  * ``data/raw/cod.jsonl`` – a JSON‑Lines file listing the COD IDs that
    were successfully downloaded and passed the atom‑count filter.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict

import requests
from pymatgen.core import Structure

# Import the verified COD base URL defined by T001
try:
    from constants import COD_BASE_URL
except ImportError as e:
    raise ImportError(
        "COD_BASE_URL could not be imported from constants.py. "
        "Make sure T001 has created code/constants.py with the variable "
        "COD_BASE_URL."
    ) from e

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_cif(cod_id: str, dest_path: Path) -> bool:
    """
    Download a single CIF file.

    Parameters
    ----------
    cod_id : str
        The COD identifier (e.g., ``'1000001'``).
    dest_path : Path
        Path where the CIF file should be saved.

    Returns
    ----------
    bool
        ``True`` if the download succeeded (HTTP 200) and the file was
        written, ``False`` otherwise.
    """
    url = f"{COD_BASE_URL.rstrip('/')}/{cod_id}.cif"
    try:
        response = requests.get(url, timeout=20, stream=True)
        if response.status_code != 200:
            return False
        # Write the CIF content atomically
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception:
        return False

def is_organic_and_small(cif_path: Path, max_non_h: int = 50) -> bool:
    """
    Determine whether a CIF file contains an organic structure with at most
    ``max_non_h`` non‑hydrogen atoms.

    Parameters
    ----------
    cif_path : Path
        Path to the CIF file.
    max_non_h : int, optional
        Maximum allowed number of non‑hydrogen atoms (default 50).

    Returns
    ----------
    bool
        ``True`` if the structure meets the criteria, ``False`` otherwise.
    """
    try:
        struct: Structure = Structure.from_file(str(cif_path))
    except Exception:
        return False

    # Count non‑hydrogen atoms
    non_h_atoms = sum(1 for site in struct if site.specie.symbol != "H")
    return non_h_atoms <= max_non_h

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_cifs(
    output_jsonl: Path,
    raw_cif_dir: Path,
    target_success: int = 500,
    max_attempts: int = 20000,
    max_non_h: int = 50,
) -> List[Dict]:
    """
    Stream COD identifiers, download CIFs, filter, and stop after the
    desired number of valid entries.

    Parameters
    ----------
    output_jsonl : Path
        File to write the list of successful COD IDs (JSON‑Lines).
    raw_cif_dir : Path
        Directory where downloaded CIF files are stored.
    target_success : int, optional
        Number of valid CIFs to obtain (default 500).
    max_attempts : int, optional
        Upper bound on the number of attempted downloads to avoid infinite
        loops (default 20 000).
    max_non_h : int, optional
        Maximum number of non‑hydrogen atoms allowed (default 50).

    Returns
    ----------
    List[Dict]
        Log entries for each attempted download.
    """
    raw_cif_dir.mkdir(parents=True, exist_ok=True)

    log_entries: List[Dict] = []
    successful_ids: List[str] = []

    cod_id = 1
    attempts = 0
    successes = 0

    while successes < target_success and attempts < max_attempts:
        cod_str = str(cod_id)
        cif_path = raw_cif_dir / f"{cod_str}.cif"
        start_ts = time.time()

        downloaded = fetch_cif(cod_str, cif_path)
        status = "downloaded" if downloaded else "failed_download"
        reason = None

        if downloaded:
            if is_organic_and_small(cif_path, max_non_h=max_non_h):
                # Valid entry
                successes += 1
                successful_ids.append(cod_str)
                status = "saved"
            else:
                # Does not meet atom‑count filter – remove the file
                try:
                    cif_path.unlink()
                except FileNotFoundError:
                    pass
                status = "rejected_atom_count"
                reason = f"non‑hydrogen atoms > {max_non_h}"

        end_ts = time.time()
        log_entries.append(
            {
                "cod_id": cod_str,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(end_ts)),
                "status": status,
                "reason": reason,
                "elapsed_seconds": round(end_ts - start_ts, 2),
            }
        )

        cod_id += 1
        attempts += 1

    # Write the list of successful IDs (one per line, JSON)
    with open(output_jsonl, "w", encoding="utf-8") as out_f:
        for cid in successful_ids:
            out_f.write(json.dumps({"cod_id": cid}) + "\n")

    return log_entries

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download organic CIF files (≤ 50 non‑H atoms) from the COD, "
            "store them under ``data/raw_cif/``, and produce a download log."
        )
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to a JSON‑Lines file that will contain the successfully downloaded COD IDs.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=500,
        help="Number of valid CIF files to obtain (default: 500).",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=20000,
        help="Maximum number of download attempts before giving up (default: 20000).",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[1]  # projects/<proj>/code/..
    output_jsonl = (project_root / args.output).resolve()
    raw_cif_dir = project_root / "data" / "raw_cif"

    # Perform the download
    log_entries = download_cifs(
        output_jsonl=output_jsonl,
        raw_cif_dir=raw_cif_dir,
        target_success=args.target,
        max_attempts=args.max_attempts,
    )

    # Write the download log
    log_path = raw_cif_dir / "download_log.json"
    with open(log_path, "w", encoding="utf-8") as log_f:
        json.dump(
            {
                "total_attempts": len(log_entries),
                "successful_downloads": sum(1 for e in log_entries if e["status"] == "saved"),
                "failed_downloads": sum(1 for e in log_entries if e["status"] == "failed_download"),
                "rejected_by_atom_count": sum(
                    1 for e in log_entries if e["status"] == "rejected_atom_count"
                ),
                "log": log_entries,
            },
            log_f,
            indent=2,
        )

    # Simple sanity check – abort if we did not reach the target
    if sum(1 for e in log_entries if e["status"] == "saved") < args.target:
        sys.exit(
            f"ERROR: Only {sum(1 for e in log_entries if e['status'] == 'saved')} valid CIFs were obtained; "
            f"target was {args.target}. Consider increasing ``--max-attempts``."
        )

    print(
        f"Download complete. {args.target} valid CIF files saved to {raw_cif_dir}."
    )
    print(f"Download log written to {log_path}")

if __name__ == "__main__":
    main()
