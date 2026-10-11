"""
Download module for the plant disease resistance pipeline.

This implementation focuses on providing a functional stub that can be
exercised in CI mode (synthetic data) while laying the groundwork for a
future real‑data downloader. When run, it creates the ``data/raw`` directory
and writes three CSV files:

* ``genotype.csv`` – synthetic SNP matrix (samples × SNPs)
* ``metabolomics.csv`` – synthetic metabolite matrix (samples × metabolites)
* ``phenotype.csv`` – synthetic resistance phenotype (binary)

The module can be invoked as a script:

.. code-block:: bash

    python -m code.download [--ci-mode]

``--ci-mode`` forces synthetic data generation; when omitted the same
behaviour is performed because real‑data download is not yet implemented.
"""

import argparse
import logging
import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

def _ensure_raw_dir() -> None:
    """Create the raw data directory if it does not exist."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"Created raw data directory at {raw_dir}")

def _write_csv(df: pd.DataFrame, filename: str) -> None:
    """Write a DataFrame to the raw data directory."""
    out_path = paths.data("raw", filename)
    df.to_csv(out_path, index=False)
    log.info(f"Wrote synthetic raw file: {out_path}")

def _generate_synthetic_data(num_samples: int = 20,
                             num_snps: int = 10,
                             num_metabs: int = 8) -> None:
    """Generate small synthetic datasets for CI testing."""
    rng = np.random.default_rng(seed=42)

    # Sample identifiers
    sample_ids = [f"sample_{i:03d}" for i in range(1, num_samples + 1)]

    # Genotype matrix: binary SNP calls (0/1)
    genotype = pd.DataFrame(
        rng.integers(0, 2, size=(num_samples, num_snps)),
        columns=[f"SNP_{i+1}" for i in range(num_snps)],
    )
    genotype.insert(0, "sample_id", sample_ids)

    # Metabolomics matrix: continuous values, normal distribution
    metabolomics = pd.DataFrame(
        rng.normal(loc=0.0, scale=1.0, size=(num_samples, num_metabs)),
        columns=[f"METAB_{i+1}" for i in range(num_metabs)],
    )
    metabolomics.insert(0, "sample_id", sample_ids)

    # Phenotype: binary resistant (1) / susceptible (0)
    phenotype = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "resistance": rng.integers(0, 2, size=num_samples),
        }
    )

    _write_csv(genotype, "genotype.csv")
    _write_csv(metabolomics, "metabolomics.csv")
    _write_csv(phenotype, "phenotype.csv")

def main(argv: list | None = None) -> None:
    """Entry point for ``python -m code.download``."""
    parser = argparse.ArgumentParser(
        description="Download (or generate synthetic) raw multi‑omics data."
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Force generation of synthetic data for CI testing.",
    )
    args = parser.parse_args(argv)

    _ensure_raw_dir()

    # At this stage real‑data download is not implemented.
    # The CI path always generates synthetic data.
    if args.ci_mode:
        log.info("CI mode enabled – generating synthetic raw data.")
    else:
        log.info(
            "Real‑data download not yet implemented – falling back to synthetic data."
        )
    _generate_synthetic_data()

    log.info("Download (synthetic) step completed successfully.")

if __name__ == "__main__":
    # When executed as a script ``python -m code.download`` the
    # function receives ``sys.argv[1:]`` automatically via argparse.
    main()
