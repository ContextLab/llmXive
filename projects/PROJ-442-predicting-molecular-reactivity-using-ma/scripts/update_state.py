import argparse
import json
import sys
from pathlib import Path
from src.utils.state_manager import update_artifact_state, update_pipeline_status
from src.utils.logging import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Update project state")
    parser.add_argument("--artifact", type=str, help="Artifact name")
    parser.add_argument("--path", type=str, help="Artifact path")
    parser.add_argument("--checksum", type=str, help="Artifact checksum")
    parser.add_argument("--metadata", type=str, help="JSON metadata")
    parser.add_argument("--status", type=str, help="Pipeline status")
    args = parser.parse_args()

    logger = setup_logging()

    if args.status:
        update_pipeline_status(args.status)
        logger.info(f"Updated pipeline status to: {args.status}")
    elif args.artifact and args.path and args.checksum:
        metadata = json.loads(args.metadata) if args.metadata else {}
        update_artifact_state(args.artifact, args.path, args.checksum, metadata)
        logger.info(f"Updated artifact state: {args.artifact}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
