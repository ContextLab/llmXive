"""High‑level pipeline for processing GPE snapshot data.

The functions in this module orchestrate the per‑snapshot analysis
performed by :mod:`analysis.vortex_detector` and :mod:`analysis.metrics`.
All public callables are documented with NumPy‑style docstrings.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from analysis.vortex_detector import detect_vortices_phase_winding

def process_single_snapshot(file_path: str) -> Dict[str, Any]:
    """Process a single snapshot file.

    This function loads the wavefunction, detects vortices using the phase‑
    winding method, and returns a dictionary with the results.

    Parameters
    ----------
    file_path : str
        Path to the ``.npy`` file containing the complex wavefunction.

    Returns
    -------
    dict
        Dictionary with keys ``vortices`` (list of detected vortices) and
        ``num_vortices`` (integer count).
    """
    psi = np.load(file_path)
    vortices = detect_vortices_phase_winding(psi)
    return {"vortices": vortices, "num_vortices": len(vortices)}

def process_batch_snapshots(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Process a batch of snapshot files.

    Parameters
    ----------
    file_paths : list of str
        List of paths to ``.npy`` wavefunction snapshots.

    Returns
    -------
    list of dict
        List of per‑snapshot result dictionaries.
    """
    results = []
    for fp in file_paths:
        results.append(process_single_snapshot(fp))
    return results

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate a list of per‑snapshot results.

    The aggregation currently computes the total number of vortices across
    all snapshots and the average vortex count per snapshot.

    Parameters
    ----------
    results : list of dict
        List of dictionaries returned by :func:`process_single_snapshot`.

    Returns
    -------
    dict
        Aggregated statistics with keys ``total_vortices`` and
        ``average_vortices_per_snapshot``.
    """
    total = sum(r["num_vortices"] for r in results)
    avg = total / len(results) if results else 0.0
    return {"total_vortices": total, "average_vortices_per_snapshot": avg}

def main() -> None:
    """Command‑line interface for the analysis pipeline.

    The CLI accepts either a single file or a directory containing multiple
    ``.npy`` snapshots and prints aggregated statistics as JSON.
    """
    parser = argparse.ArgumentParser(description="Run analysis pipeline on GPE snapshots.")
    parser.add_argument(
        "input",
        help="Path to a .npy snapshot or a directory containing snapshots.",
    )
    args = parser.parse_args()
    input_path = Path(args.input)
    if input_path.is_dir():
        files = sorted(str(p) for p in input_path.glob("*.npy"))
    else:
        files = [str(input_path)]

    batch_results = process_batch_snapshots(files)
    agg = aggregate_results(batch_results)
    print(json.dumps(agg, indent=2))

if __name__ == "__main__":
    main()
