"""
Script to generate feature‑space clustering proxies (K‑Means with k=3) for all
datasets listed in the manifest. The resulting proxy information is saved
to ``data/manifests/spatial_proxy_report.json`` as required by task T037.
"""

import json
import traceback
from pathlib import Path

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger

# Local imports
from data_loader import load_manifest, _read_dataset_file  # noqa: F401
from dependency_injector import (
    generate_spatial_proxy,
    save_spatial_proxy_report,
    validate_feature_space_proxy,
    save_proxy_validation_report,
)

log = get_logger(__name__)

def _load_dataset_from_manifest(entry: dict) -> pd.DataFrame:
    """
    Load a dataset file referenced in the manifest.
    The manifest contains ``name`` and ``url``; the file is expected to have
    been downloaded already by ``code/main.py --action download`` into
    ``data/raw/``.
    """
    name = entry["name"]
    # Determine expected file extension from URL
    url = entry["url"]
    if url.lower().endswith((".xls", ".xlsx")):
        filename = f"{name}.xls"
    else:
        filename = f"{name}.csv"

    file_path = paths.data("raw", filename)
    if not file_path.is_file():
        raise FileNotFoundError(f"Dataset file not found for {name}: {file_path}")

    return _read_dataset_file(str(file_path))

def main():
    """
    Generate proxies for every dataset in the manifest and write a combined
    report. If proxy generation fails for a particular dataset we log a
    warning and continue with the remaining ones (no fallback injection).
    """
    try:
        manifest_path = paths.data("manifests", "datasets.yaml")
        datasets = load_manifest(str(manifest_path))

        combined_report = {}
        validation_reports = {}

        for entry in datasets:
            name = entry.get("name", "unknown")
            log.info(f"Generating spatial proxy for dataset: {name}")

            try:
                df = _load_dataset_from_manifest(entry)

                # Use only numeric columns for clustering; non‑numeric are dropped
                numeric_df = df.select_dtypes(include=[np.number])
                if numeric_df.empty:
                    log.warning(f"No numeric columns in dataset {name}; skipping proxy generation.")
                    continue

                data_array = numeric_df.to_numpy()

                # Generate proxy (k=3 enforced by default)
                proxy = generate_spatial_proxy(data_array, n_clusters=3, seed=42)

                # Validate proxy
                validation = validate_feature_space_proxy(proxy, data_array)

                # Store per‑dataset proxy info
                combined_report[name] = proxy
                validation_reports[name] = validation

            except Exception as e:
                log.error(f"Failed to generate proxy for dataset {name}: {e}")
                log.debug(traceback.format_exc())
                continue

        # Write the combined proxy report
        proxy_report_path = paths.data("manifests", "spatial_proxy_report.json")
        save_spatial_proxy_report(combined_report, str(proxy_report_path))
        log.info(f"Spatial proxy report written to {proxy_report_path}")

        # Write the validation report (required by T041, but generated here for completeness)
        validation_path = paths.data("manifests", "spatial_proxy_validation.json")
        save_proxy_validation_report(validation_reports, str(validation_path))
        log.info(f"Spatial proxy validation report written to {validation_path}")

    except Exception as e:
        log.critical(f"Unexpected error during proxy generation: {e}")
        log.debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
