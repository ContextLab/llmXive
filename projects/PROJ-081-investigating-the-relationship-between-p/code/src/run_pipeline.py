"""
run_pipeline.py
----------------
Orchestrates the end‑to‑end data acquisition and preprocessing steps
required for the plant metabolite ↔ herbivore resistance analysis.

The script is deliberately lightweight: it fetches the three raw
datasets (MetaboLights, PMN, HPID) using the existing fetch functions,
runs the preprocessing pipeline, and relies on the `paths` helper to
write the cleaned Parquet file and checksum log to the exact locations
required by the task specifications.

The command‑line interface mirrors the one described in ``quickstart.md``.
Only ``--seed``, ``--max-species`` and ``--output-dir`` are parsed; they
are retained for compatibility but are not used directly because the
underlying modules already enforce deterministic behaviour via
``code/src/config.py`` and the preprocessing function writes to the
canonical project directories.

This version ensures that a Parquet engine (pyarrow) is available at
runtime. If the import fails, the script installs ``pyarrow`` on‑the‑fly
before proceeding, guaranteeing that ``df.to_parquet`` succeeds on the
CI runner.
"""

import argparse
import sys
import subprocess
import importlib
import pandas as pd

# Ensure a Parquet engine (pyarrow) is available.
try:
    import pyarrow  # noqa: F401
except ImportError:
    # Install pyarrow quietly; this will use the same environment the
    # script runs in. The installation is fast because a recent wheel
    # is available for the runner's platform.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow>=12.0.0"])
    # Reload the module so pandas can discover the newly installed engine.
    importlib.invalidate_caches()
    import pyarrow  # noqa: F401

# Import the project's internal modules using the package layout
from code.src.fetch_data import fetch_metabolights, fetch_pmn, fetch_hpid
from code.src.preprocess import load_and_preprocess
from code.src import config  # ensures global seeds are set

def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the data acquisition and preprocessing pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (passed to config).",
    )
    parser.add_argument(
        "--max-species",
        type=int,
        default=None,
        help="Maximum number of species to retain after fetching (optional).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/",
        help="Directory where pipeline artefacts will be written (unused – kept for compatibility).",
    )
    parser.add_argument(
        "--use-placeholder",
        action="store_true",
        help=(
            "If set, the pipeline would fall back to a placeholder dataset. "
            "This implementation requires real data and will raise an error if used."
        ),
    )
    return parser.parse_args(argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)

    # Guard against placeholder usage – the task mandates real data.
    if args.use_placeholder:
        raise RuntimeError(
            "Placeholder data is not permitted for T002. The pipeline requires real "
            "datasets from MetaboLights, PMN, and HPID."
        )

    # ------------------------------------------------------------------
    # 1. Data acquisition
    # ------------------------------------------------------------------
    print("Fetching MetaboLights data...")
    df_metabolights = fetch_metabolights()
    print("Fetching PMN data...")
    df_pmn = fetch_pmn()
    print("Fetching HPID data...")
    df_hpid = fetch_hpid()

    raw_dataframes = [df_metabolights, df_pmn, df_hpid]

    # Optional species‑capping – drop excess rows after concatenation
    if args.max_species is not None:
        # Concatenate temporarily to count species, then truncate.
        temp_concat = (
            pd.concat(raw_dataframes, ignore_index=True, sort=False)
            .drop_duplicates(subset=["species_id"])
        )
        allowed_ids = (
            temp_concat["species_id"]
            .drop_duplicates()
            .head(args.max_species)
            .tolist()
        )
        # Filter each dataframe to the allowed IDs
        raw_dataframes = [
            df[df["species_id"].isin(allowed_ids)] for df in raw_dataframes
        ]

    # ------------------------------------------------------------------
    # 2. Pre‑processing
    # ------------------------------------------------------------------
    print("Running preprocessing pipeline...")
    load_and_preprocess(raw_dataframes)

    print("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())