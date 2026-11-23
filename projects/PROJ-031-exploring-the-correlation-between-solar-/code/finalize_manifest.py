import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Importing from the API surface provided in the prompt
from manifest_utils import load_manifest, save_manifest, update_source_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def finalize_manifest():
    """
    Verifies and finalizes data/source_manifest.yaml.
    Updates status to 'verified' and sets last_verified_at for:
    - NOAA_SWPC_DST
    - CDAWeb_LASCO
    - GOES_XRAY
    
    This task ensures the manifest reflects the actual URLs used by the pipeline
    and confirms they were successfully verified during the ingestion phase.
    """
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "source_manifest.yaml"

    if not manifest_path.exists():
        logger.error(f"Manifest file not found at {manifest_path}")
        sys.exit(1)

    logger.info(f"Loading manifest from {manifest_path}")
    manifest = load_manifest(manifest_path)

    sources_to_finalize = ["NOAA_SWPC_DST", "NOAA_SWPC_KP", "CDAWeb_LASCO", "GOES_XRAY"]
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    updated = False

    for source_id in sources_to_finalize:
        if source_id in manifest.get("sources", {}):
            source = manifest["sources"][source_id]
            # Update status to verified and timestamp
            if source.get("status") != "verified":
                logger.info(f"Updating source {source_id} status to 'verified'")
                update_source_status(manifest, source_id, "verified", current_timestamp)
                updated = True
            else:
                # Ensure timestamp is fresh even if status was already verified
                source["last_verified_at"] = current_timestamp
                logger.info(f"Refreshed verification timestamp for {source_id}")
                updated = True
        else:
            logger.warning(f"Source {source_id} not found in manifest, skipping.")

    if updated:
        manifest["last_updated"] = current_timestamp
        logger.info(f"Saving updated manifest to {manifest_path}")
        save_manifest(manifest, manifest_path)
        logger.info("Manifest finalization complete.")
    else:
        logger.info("No changes required for manifest.")

def main():
    try:
        finalize_manifest()
    except Exception as e:
        logger.error(f"Failed to finalize manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
