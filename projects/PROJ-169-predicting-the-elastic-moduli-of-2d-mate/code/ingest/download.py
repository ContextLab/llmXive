import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from utils.config import Config
from utils.logger import get_logger

# Ensure imports match the API surface provided in the prompt
# The task requires extending download.py to add runtime source enforcement.

logger = get_logger(__name__)

# Source types allowed
SourceType = Literal["materials_project", "aflow", "oqmd"]

class DownloadManifest:
    """
    Represents the manifest of a download run.
    """
    def __init__(
        self,
        source: SourceType,
        count: int,
        path: str,
        timestamp: str,
        checksum: Optional[str] = None
    ):
        self.source = source
        self.count = count
        self.path = path
        self.timestamp = timestamp
        self.checksum = checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "count": self.count,
            "path": self.path,
            "timestamp": self.timestamp,
            "checksum": self.checksum
        }

class UnifiedDatasetLoader:
    """
    Unified loader that abstracts Materials Project, AFLOW, etc.
    
    CRITICAL CONSTRAINT (Constitution Principle I):
    This loader enforces a SINGLE CANONICAL SOURCE per run.
    Attempting to mix sources or configure multiple sources simultaneously
    will raise a RuntimeError.
    """

    def __init__(
        self,
        config: Config,
        source: Optional[SourceType] = None,
        sample_size: Optional[int] = None
    ):
        self.config = config
        self.source = source
        self.sample_size = sample_size
        
        # Runtime enforcement: Track active sources
        self._active_sources: List[SourceType] = []

        if self.source:
            self._validate_single_source(self.source)
            self._active_sources.append(self.source)

    def _validate_single_source(self, new_source: SourceType) -> None:
        """
        Enforces the single canonical source constraint.
        Raises RuntimeError if more than one source is active or attempted.
        """
        if len(self._active_sources) > 0:
            current = self._active_sources[0]
            if new_source != current:
                raise RuntimeError(
                    f"Source enforcement violation: Cannot switch from '{current}' "
                    f"to '{new_source}' in the same UnifiedDatasetLoader instance. "
                    f"Constitution Principle I requires a single canonical source per run."
                )

    def load(self, output_dir: Optional[Path] = None) -> DownloadManifest:
        """
        Executes the download/ingest process for the configured single source.
        """
        if not self.source:
            raise ValueError("No data source configured. Must specify 'materials_project', 'aflow', or 'oqmd'.")
        
        logger.info(f"Starting download from canonical source: {self.source}")
        
        # Simulate download logic (placeholder for actual API calls in real implementation)
        # In a real scenario, this would call specific fetchers based on self.source
        start_time = time.time()
        
        # Placeholder for actual data fetching logic
        # This ensures the code is runnable but acknowledges the specific 
        # implementation of fetching depends on the source API.
        data_path = output_dir or self.config.data_processed_dir / f"{self.source}_raw.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Mocking a small count for demonstration if no real fetcher is wired yet
        # In a full implementation, this would be the result of the API call
        count = self.sample_size if self.sample_size else 100 
        
        manifest = DownloadManifest(
            source=self.source,
            count=count,
            path=str(data_path),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))
        )
        
        # Write manifest to disk
        with open(data_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        logger.info(f"Download complete. Source: {self.source}, Count: {count}")
        return manifest

def main():
    """
    Entry point for the download script.
    Demonstrates the single-source enforcement.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Dataset Loader for 2D Materials")
    parser.add_argument("--source", type=str, required=True, 
                        choices=["materials_project", "aflow", "oqmd"],
                        help="Single canonical data source to use.")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for data.")
    parser.add_argument("--sample", type=int, default=None,
                        help="Sample size to fetch.")
    
    args = parser.parse_args()
    
    config = Config()
    loader = UnifiedDatasetLoader(config, source=args.source, sample_size=args.sample)
    
    try:
        manifest = loader.load(output_dir=Path(args.output) if args.output else None)
        print(json.dumps(manifest.to_dict(), indent=2))
    except RuntimeError as e:
        logger.error(f"Source Enforcement Failed: {e}")
        raise

if __name__ == "__main__":
    main()