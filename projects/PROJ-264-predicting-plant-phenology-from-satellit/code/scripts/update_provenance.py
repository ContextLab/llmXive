"""
Script to update data/provenance.yaml with checksums and execution details
after each data ingestion step (T011-T013).
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import hashlib

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.provenance import (
    load_provenance,
    save_provenance,
    update_source_checksum,
    update_step_checksum,
    mark_step_executed,
    add_provenance_entry,
    PROVENANCE_FILE_PATH
)
from src.lib.utils import setup_logging

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_provenance_for_step(
    step_id: str,
    output_file: str,
    source_name: str = None,
    processing_params: dict = None
):
    """
    Update provenance file with checksums and execution status for a step.
    
    Args:
        step_id: The step identifier (e.g., "step_002")
        output_file: Path to the output file relative to project root
        source_name: Optional data source name to update checksums for
        processing_params: Optional additional processing parameters to record
    """
    logger = logging.getLogger(__name__)
    
    # Load current provenance
    provenance = load_provenance()
    
    # Resolve output file path
    output_path = project_root / output_file
    
    if not output_path.exists():
        logger.error(f"Output file not found: {output_path}")
        return False
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Computed checksum for {output_file}: {checksum}")
    
    # Update step checksum and mark as executed
    step_updated = False
    for step in provenance.get("processing_steps", []):
        if step.get("id") == step_id:
            # Update checksums for this step's outputs
            if "checksums" not in step:
                step["checksums"] = {}
            step["checksums"][output_file] = checksum
            
            # Mark step as executed
            step["status"] = "completed"
            step["executed_at"] = datetime.utcnow().isoformat() + "Z"
            step_updated = True
            logger.info(f"Updated step {step_id} status to completed")
            break
    
    if not step_updated:
        logger.warning(f"Step {step_id} not found in processing_steps")
    
    # Update source checksum if specified
    if source_name:
        source_updated = False
        for source in provenance.get("data_sources", []):
            if source.get("name") == source_name:
                if "checksums" not in source:
                    source["checksums"] = {}
                source["checksums"][output_file] = checksum
                source["status"] = "available"
                source["last_accessed"] = datetime.utcnow().isoformat() + "Z"
                source_updated = True
                logger.info(f"Updated source {source_name} status to available")
                break
        
        if not source_updated:
            logger.warning(f"Source {source_name} not found in data_sources")
    
    # Update last_updated timestamp
    provenance["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Add additional processing parameters if provided
    if processing_params:
        if "processing_params" not in provenance:
            provenance["processing_params"] = {}
        provenance["processing_params"].update(processing_params)
    
    # Save updated provenance
    save_provenance(provenance)
    logger.info(f"Updated provenance file: {PROVENANCE_FILE_PATH}")
    
    return True

def main():
    """
    Main entry point for updating provenance after ingestion steps.
    
    Usage:
    python scripts/update_provenance.py --step step_002 --output data/processed/sentinel_data.parquet --source sentinel-s2-l2a
    """
    import argparse
    
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Update provenance.yaml after data ingestion steps")
    parser.add_argument("--step", required=True, help="Step ID to update (e.g., step_002)")
    parser.add_argument("--output", required=True, help="Output file path relative to project root")
    parser.add_argument("--source", required=False, help="Optional data source name to update")
    parser.add_argument("--params", required=False, help="Optional JSON string of additional processing parameters")
    
    args = parser.parse_args()
    
    # Parse additional parameters if provided
    processing_params = None
    if args.params:
        import json
        try:
            processing_params = json.loads(args.params)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON for --params: {e}")
            sys.exit(1)
    
    # Update provenance
    success = update_provenance_for_step(
        step_id=args.step,
        output_file=args.output,
        source_name=args.source,
        processing_params=processing_params
    )
    
    if success:
        logger.info("Provenance updated successfully")
        sys.exit(0)
    else:
        logger.error("Failed to update provenance")
        sys.exit(1)

if __name__ == "__main__":
    main()