"""
run_full_pipeline.py
---------------------

This script executes the complete end‑to‑end pipeline for the HEA yield‑strength
project and writes all required artefacts such as ``manifest.json``, ``report.md``,
``metrics.json`` and the runtime log.  It is deliberately lightweight – it only
orchestrates the high‑level functions that already exist in the code base and
adds a small manifest‑generation step that collects provenance information.

The script is intended to be run from the repository root:

    python code/run_full_pipeline.py

It will raise any exception that occurs inside the pipeline (``Fail loudly``) so
that the execution guard can detect fabrication or missing data.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
import importlib.metadata

# Project‑wide utilities
from utils.logging import set_seeds, get_logger, get_seed
from profiler import run_full_pipeline  # Executes the full data‑model‑training‑evaluation pipeline

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def sha256_checksum(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_versions() -> dict:
    """Collect version information for the most important third‑party packages."""
    packages = ["numpy", "pandas", "scikit-learn", "matplotlib", "seaborn"]
    versions = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "unknown"
    # Add Python version
    versions["python"] = f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    return versions


def build_manifest() -> dict:
    """
    Assemble the manifest JSON required by ``T047``.
    The manifest contains provenance fields such as seeds, hyper‑parameters,
    library versions, timestamps and checksums of the major artefacts.
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1️⃣  Seeds
    # ------------------------------------------------------------------
    seed = get_seed()

    # ------------------------------------------------------------------
    # 2️⃣  Hyper‑parameters (hard‑coded as they are fixed in the pipeline)
    # ------------------------------------------------------------------
    hyperparameters = {
        "random_forest": {
            "n_estimators": 500,
            "max_features": "sqrt",
            "random_state": 42,
            "n_jobs": -1,
        },
        "linear_regression": {
            "fit_intercept": True,
            "normalize": False,
        },
    }

    # ------------------------------------------------------------------
    # 3️⃣  Library versions
    # ------------------------------------------------------------------
    versions = collect_versions()

    # ------------------------------------------------------------------
    # 4️⃣  Timestamps
    # ------------------------------------------------------------------
    timestamp = datetime.utcnow().isoformat() + "Z"

    # ------------------------------------------------------------------
    # 5️⃣  Checksums of major artefacts
    # ------------------------------------------------------------------
    raw_path = Path("data/raw/heas_raw.csv")
    desc_path = Path("data/processed/hea_descriptors.csv")
    manifest_checksums = {}
    for p in (raw_path, desc_path):
        if p.is_file():
            manifest_checksums[p.as_posix()] = sha256_checksum(p)
        else:
            logger.error(f"Expected artefact {p} not found while building manifest.")
            raise FileNotFoundError(p)

    # ------------------------------------------------------------------
    # 6️⃣  VIF remediation decision
    # ------------------------------------------------------------------
    remediation_path = Path("output/remediation_results.json")
    vif_remediation = remediation_path.is_file()

    # ------------------------------------------------------------------
    # 7️⃣  Permutation‑importance settings (fixed by T044)
    # ------------------------------------------------------------------
    permutation_settings = {"n_permutations_per_feature": 1000}

    # ------------------------------------------------------------------
    # Assemble final manifest
    # ------------------------------------------------------------------
    manifest = {
        "seed": seed,
        "hyperparameters": hyperparameters,
        "library_versions": versions,
        "generated_at": timestamp,
        "artifact_checksums": manifest_checksums,
        "vif_remediation_applied": vif_remediation,
        "permutation_settings": permutation_settings,
    }

    logger.debug("Manifest constructed successfully.")
    return manifest


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full pipeline and write the required artefacts.
    The function follows the exact order required by the specification:

    1. Initialise deterministic environment (seeds, logging).
    2. Run the full pipeline (data download → preprocessing → descriptor
       calculation → model training → evaluation → report generation).
    3. Build and write ``output/manifest.json``.
    """
    logger = get_logger(__name__)

    # 1️⃣ Initialise deterministic environment
    logger.info("Setting deterministic seeds.")
    set_seeds(42)

    # 2️⃣ Run the full pipeline (this call is expected to create all
    #    artefacts such as metrics.json, report.md, etc.).
    logger.info("Running the full pipeline via `profiler.run_full_pipeline`.")
    try:
        run_full_pipeline()
    except Exception as exc:
        logger.exception("Full pipeline execution failed.")
        raise  # Propagate – the execution guard will treat this as a failure.

    # 3️⃣ Build and persist the manifest
    logger.info("Building project manifest.")
    manifest = build_manifest()
    manifest_path = Path("output/manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    logger.info(f"Manifest written to {manifest_path.resolve()}.")
    logger.info("Full pipeline execution completed successfully.")


if __name__ == "__main__":
    main()
