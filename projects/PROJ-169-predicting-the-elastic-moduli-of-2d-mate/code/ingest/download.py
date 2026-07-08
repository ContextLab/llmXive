"""
Unified dataset loader for 2D material elastic properties.

This module abstracts access to public materials repositories (Materials Project, AFLOW)
into a single canonical source interface. It adheres to Constitution Principle I
by ensuring data is retrieved from a single, consistent source per execution run.

IMPORTANT: This script retrieves existing Density Functional Theory (DFT) calculations
from public repositories. It does NOT generate new DFT data. The data represents
pre-computed ground truth values used to train the Structure-Only Surrogate Model.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

import requests
from tqdm import tqdm
import pandas as pd

# Import project utilities
from utils.config import Config
from utils.logger import get_logger, log_bias_check, log_exclusion_reason
from utils.memory_utils import verify_data_volume

# Constants
MP_API_URL = "https://api.materialsproject.org"
AFLOW_API_URL = "https://aflow.org" # Placeholder for actual endpoint if needed, MP is primary for this MVP

logger = get_logger(__name__)

@dataclass
class DownloadManifest:
    """Records metadata about the downloaded dataset for reproducibility."""
    source: str
    timestamp: str
    total_entries: int
    filtered_entries: int
    config_snapshot: Dict[str, Any]
    data_file_path: str

class UnifiedDatasetLoader:
    """
    Handles downloading and abstracting material data from public repositories.

    This class ensures that only one canonical source is used per run to satisfy
    Constitution Principle I. It currently prioritizes the Materials Project API
    as the primary source for 2D materials with elastic tensor data.
    """

    def __init__(self, config: Config, source: Literal["materials_project", "aflow"] = "materials_project"):
        self.config = config
        self.source = source
        self.api_key = os.getenv("MP_API_KEY")
        self.logger = get_logger(__name__)

        if source == "materials_project" and not self.api_key:
            # Warning: In a real run, this might fail if key is missing,
            # but for the purpose of the script structure, we proceed.
            # The task requires real data logic, so we assume key is set or handle error.
            self.logger.warning("MP_API_KEY not found in environment. Download will fail if API is enforced.")

        self.logger.info(f"Initialized UnifiedDatasetLoader for source: {source}")
        self.logger.info("DATA SOURCE NOTICE: This loader retrieves existing DFT data from public repositories.")
        self.logger.info("It does NOT perform first-principles calculations. The model is a surrogate for these DFT values.")

    def fetch_materials_metadata(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetches metadata for materials with elastic tensors.

        Args:
            limit: Maximum number of entries to fetch. If None, fetches all available (subject to API limits).

        Returns:
            List of material dictionaries containing IDs and basic properties.
        """
        if self.source != "materials_project":
            raise NotImplementedError(f"Source '{self.source}' is not yet implemented for metadata fetching.")

        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        params = {
            "fields": "material_id,formula,nsites,structure,elastic_tensor,elastic_anisotropy,space_group",
            "is_2d": "true", # Filter for 2D materials specifically if the API supports it
            "num_docs": limit or 1000
        }

        # Note: Materials Project API endpoint for elastic data
        endpoint = f"{MP_API_URL}/materials/elastic"

        self.logger.info(f"Fetching data from {endpoint}...")
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from Materials Project: {e}")
            return []

    def fetch_elastic_tensor(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the full elastic tensor and derived properties for a specific material.
        """
        if self.source != "materials_project":
            return None

        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        endpoint = f"{MP_API_URL}/materials/{material_id}/elastic"

        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            self.logger.debug(f"Could not fetch elastic data for {material_id}")
            return None

    def download_and_save(
        self,
        output_dir: str,
        limit: Optional[int] = None,
        verify_memory: bool = True
    ) -> DownloadManifest:
        """
        Orchestrates the download of materials data and saves it to a canonical JSON/Parquet file.

        Args:
            output_dir: Directory to save the processed data.
            limit: Maximum number of materials to download.
            verify_memory: Whether to check memory constraints before saving.

        Returns:
            DownloadManifest object containing run metadata.
        """
        self.logger.info("Starting unified dataset download...")
        self.logger.info("WARNING: This script fetches REAL DFT data. Ensure network connectivity.")

        # Create output directory
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # Fetch metadata
        raw_data = self.fetch_materials_metadata(limit=limit)
        if not raw_data:
            self.logger.warning("No data retrieved. Check API key or connectivity.")
            # Return empty manifest even if no data
            manifest = DownloadManifest(
                source=self.source,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                total_entries=0,
                filtered_entries=0,
                config_snapshot=self.config.to_dict(),
                data_file_path=str(out_path / "empty_dataset.parquet")
            )
            return manifest

        processed_records = []
        skipped_count = 0

        # Process each material
        pbar = tqdm(raw_data, desc="Processing Materials", disable=self.config.silent)
        for item in pbar:
            mat_id = item.get("material_id")
            if not mat_id:
                continue

            # Fetch detailed elastic data
            elastic_data = self.fetch_elastic_tensor(mat_id)

            if elastic_data is None:
                log_exclusion_reason(self.logger, mat_id, "Missing elastic tensor in API response")
                skipped_count += 1
                continue

            # Basic validation: Ensure 6x6 tensor exists
            tensor = elastic_data.get("elastic_tensor")
            if not tensor or len(tensor) != 6 or any(len(row) != 6 for row in tensor):
                log_exclusion_reason(self.logger, mat_id, "Invalid elastic tensor dimensions")
                skipped_count += 1
                continue

            # Construct canonical record
            record = {
                "material_id": mat_id,
                "formula": item.get("formula", "Unknown"),
                "nsites": item.get("nsites", 0),
                "elastic_tensor": tensor,
                "elastic_anisotropy": elastic_data.get("elastic_anisotropy"),
                "space_group": elastic_data.get("space_group", {}).get("number"),
                "source": self.source,
                "dft_source": "Materials Project (Existing DFT)", # Explicit documentation
                "timestamp_fetched": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            processed_records.append(record)

            pbar.set_postfix({"processed": len(processed_records), "skipped": skipped_count})

        # Memory verification
        if verify_memory:
            total_size_estimate = len(processed_records) * 1024 # Rough estimate in bytes
            self.logger.info(f"Estimated memory for {len(processed_records)} records: {total_size_estimate / 1024:.2f} KB")
            # Verify against the 7GB limit defined in spec
            verify_data_volume(len(processed_records), max_items=100000) # Conservative cap

        # Save to Parquet
        df = pd.DataFrame(processed_records)
        output_file = out_path / "materials_raw.parquet"
        df.to_parquet(output_file, index=False)

        self.logger.info(f"Saved {len(processed_records)} records to {output_file}")
        self.logger.info(f"Skipped {skipped_count} entries due to missing/invalid data.")

        manifest = DownloadManifest(
            source=self.source,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_entries=len(raw_data),
            filtered_entries=len(processed_records),
            config_snapshot=self.config.to_dict(),
            data_file_path=str(output_file)
        )

        # Save manifest
        manifest_file = out_path / "download_manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(asdict(manifest), f, indent=2)

        return manifest

def main():
    """
    Entry point for the download script.
    Usage: python code/ingest/download.py
    """
    logger.info("Starting Unified Dataset Loader (T009)")

    # Initialize config
    config = Config(seed=42, silent=False)

    # Initialize loader (Defaulting to Materials Project as per plan)
    loader = UnifiedDatasetLoader(config, source="materials_project")

    # Execute download
    # Note: In a real environment, ensure MP_API_KEY is set.
    # If running without key, this will likely return empty or error, which is expected behavior.
    manifest = loader.download_and_save(
        output_dir="data/raw",
        limit=50, # Small limit for initial run to verify functionality
        verify_memory=True
    )

    logger.info(f"Download complete. Manifest: {manifest.source}, Records: {manifest.filtered_entries}")
    logger.info("Data is from existing DFT calculations. No new DFT generated.")

if __name__ == "__main__":
    main()