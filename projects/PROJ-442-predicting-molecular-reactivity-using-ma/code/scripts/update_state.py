#!/usr/bin/env python3
"""
Script to update the project state with new artifacts and checksums.
Usage: python scripts/update_state.py --artifact <path> [--name <name>] [--metadata <json>]
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.state_manager import update_artifact_state, update_pipeline_status
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

def main():
    parser = argparse.ArgumentParser(description="Update project state with artifact information")
    parser.add_argument("--artifact", required=True, help="Path to the artifact file to register")
    parser.add_argument("--name", default=None, help="Optional name for the artifact (defaults to filename)")
    parser.add_argument("--metadata", default=None, help="Optional JSON string for additional metadata")
    parser.add_argument("--status", default=None, help="Optional pipeline status to update (e.g., 'completed', 'failed')")
    
    args = parser.parse_args()
    
    artifact_path = Path(args.artifact)
    
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        sys.exit(1)
    
    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata: {e}")
            sys.exit(1)
    
    try:
        update_artifact_state(artifact_path, args.name, metadata)
        logger.info(f"Successfully registered artifact: {artifact_path}")
        
        if args.status:
            update_pipeline_status(args.status)
            logger.info(f"Pipeline status updated to: {args.status}")
            
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
