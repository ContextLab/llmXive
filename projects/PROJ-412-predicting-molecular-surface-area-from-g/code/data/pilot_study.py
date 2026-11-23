"""
T014-Pilot: Pilot study to estimate per-molecule processing runtime.

Reads SMILES from the ingested chunk parquet files (T048 output). If no
chunk files exist on disk yet, it fetches a REAL sample of SMILES from
PubChem PUG-REST (a public, programmatically-accessible source) so the
pilot measures real RDKit conformer-generation + SASA runtime on real
molecules. No synthetic data is ever generated.

Per-molecule processing mirrors the T015a pipeline stage: SMILES parse,
ETKDG 3D conformer embedding (maxAttempts=100, randomSeed=42), UFF
energy minimization (200 steps), and SASA calculation.

Output: data/processed/pilot_report.json with:
  - avg_time_per_mol (float, seconds)
  - total_estimated_time (float, hours)
"""
import argparse
import glob
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List

import pandas as pd

# Project imports (run from repository root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import MAX_MOLECULES, RANDOM_SEED  # noqa: E402

# Conformer generation parameters (must match T015a / conformer_params.json)
CONFORMER_PARAMS = {
    "numThreads": 4,
    "maxAttempts": 100,
    "energyMinimizationSteps": 200,
    "random_seed": RANDOM_SEED,
}

FAILURE_RATE_THRESHOLD = 0.10
PUBCHEM_BATCH_SIZE = 20  # small batches to stay within PUG-REST limits
PUBCHEM_MAX_RETRIES = 3


def load_smiles_from_chunks(pattern: str) -> List[str]:
    """Load SMILES strings from ingested chunk parquet files."""
    files = sorted(glob.glob(pattern))
    smiles_list: List[str] = []
    for f in files:
        df = pd.read_parquet(f)
        if "smiles" in df.columns:
            smiles_list.extend(df["smiles"].dropna().astype(str).tolist())
    return smiles_list


def _pubchem_request(url: str) -> bytes:
    """Perform a PUG-REST request with bounded retries on transient errors."""
    last_err: Exception | None = None
    for attempt in range(PUBCHEM_MAX_RETRIES):
        req = urllib.request.Request(
            url, headers={"User-Agent": "llmXive-pilot-study/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status != 200:
                    raise ConnectionError(
                        f"PubChem PUG-REST returned status {resp.status}"
                    )
                return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_err = e
            time.sleep(2.0 * (attempt + 1))
    raise ConnectionError(f"PubChem PUG-REST unreachable after retries: {last_err}")


def fetch_smiles_from_pubchem(count: int) -> List[str]:
    """
    Fetch real SMILES from PubChem PUG-REST (first `count` CIDs).

    Requests are batched (JSON format) to avoid the CSV endpoint's
    size/shape issues. This is a REAL public data source; if
    unreachable, raises loudly.
    """
    from rdkit import Chem  # validate parse downstream anyway

    smiles: List[str] = []
    cid = 1
    while len(smiles) < count:
        cids = ",".join(
            str(i) for i in range(cid, cid + PUBCHEM_BATCH_SIZE)
        )
        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
            f"property/CanonicalSMILES/JSON?cid={cids}"
        )
        payload = json.loads(_pubchem_request(url).decode("utf-8"))
        features = payload.get("PropertyTable", {}).get("Properties", [])
        if not features:
            raise ValueError(
                "PubChem response did not contain CanonicalSMILES data"
            )
        got_any = False
        for entry in features:
            smi = entry.get("CanonicalSMILES")
            if smi and Chem.MolFromSmiles(smi) is not None:
                smiles.append(smi)
                got_any = True
                if len(smiles) >= count:
                    break
        if not got_any:
            # A whole batch of CIDs yielded nothing usable -> data issue
            raise ValueError(
                "No valid SMILES obtained from PubChem batch "
                f"starting at CID {cid}"
            )
        cid += PUBCHEM_BATCH_SIZE
    if not smiles:
        raise ValueError("No valid SMILES obtained from PubChem")
    return smiles[:count]


def process_single_molecule(smiles: str) -> bool:
    """
    Process one molecule exactly as the T015a stage would:
    parse -> ETKDG embed -> UFF minimize -> SASA. Returns True on success.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdMolDescriptors

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.maxIterations = CONFORMER_PARAMS["maxAttempts"]
    params.randomSeed = CONFORMER_PARAMS["random_seed"]
    params.numThreads = CONFORMER_PARAMS["numThreads"]
    cid = AllChem.EmbedMolecule(mol, params)
    if cid != 0:
        return False
    if AllChem.UFFHasAllMoleculeParams(mol):
        AllChem.UFFOptimizeMolecule(
            mol, maxIters=CONFORMER_PARAMS["energyMinimizationSteps"]
        )
    rdMolDescriptors.CalcSASA(mol)
    return True


def run_pilot(pattern: str, count: int) -> dict:
    source = "chunks"
    smiles_list = load_smiles_from_chunks(pattern)
    if not smiles_list:
        source = "pubchem_pug_rest"
        smiles_list = fetch_smiles_from_pubchem(count)

    # Deterministic sample using the project seed
    sample = smiles_list[:count] if len(smiles_list) <= count else pd.Series(
        smiles_list
    ).sample(n=count, random_state=RANDOM_SEED).tolist()

    times = []
    failures = 0
    for smi in sample:
        t0 = time.perf_counter()
        try:
            ok = process_single_molecule(smi)
        except Exception:
            ok = False
        elapsed = time.perf_counter() - t0
        if ok:
            times.append(elapsed)
        else:
            failures += 1

    attempted = len(sample)
    if attempted == 0:
        raise ValueError("Pilot study had no molecules to process.")
    if not times:
        raise ValueError("All pilot molecules failed processing; cannot estimate runtime.")
    failure_rate = failures / attempted
    if failure_rate > FAILURE_RATE_THRESHOLD:
        raise RuntimeError(
            f"Pilot failure rate {failure_rate:.2%} exceeds threshold "
            f"{FAILURE_RATE_THRESHOLD:.0%}; halting."
        )

    avg_time_per_mol = sum(times) / len(times)
    # Total dataset size the estimate applies to: molecules available in
    # the input (all chunk data), capped by the pilot-study MAX_MOLECULES.
    total_dataset_size = min(len(smiles_list), MAX_MOLECULES)
    total_estimated_time = avg_time_per_mol * total_dataset_size / 3600.0

    return {
        "avg_time_per_mol": avg_time_per_mol,
        "total_estimated_time": total_estimated_time,
        "sample_size": attempted,
        "successful": len(times),
        "failed": failures,
        "failure_rate": failure_rate,
        "total_dataset_size": total_dataset_size,
        "data_source": source,
        "conformer_params": CONFORMER_PARAMS,
    }


def main():
    parser = argparse.ArgumentParser(
        description="T014-Pilot: estimate per-molecule processing runtime."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/chunk_*.parquet",
        help="Glob pattern for input chunk parquet files.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of molecules to process in the pilot sample.",
    )
    args = parser.parse_args()

    report = run_pilot(args.input, args.count)

    output_path = PROJECT_ROOT / "data" / "processed" / "pilot_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Pilot report written to {output_path}")
    print(f"avg_time_per_mol: {report['avg_time_per_mol']:.6f} s")
    print(f"total_estimated_time: {report['total_estimated_time']:.4f} h")


if __name__ == "__main__":
    main()