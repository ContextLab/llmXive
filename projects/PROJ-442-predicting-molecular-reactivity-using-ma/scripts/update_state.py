import argparse
import sys
from datetime import datetime
from typing import Optional
from src.utils.state_manager import (
    update_stage_status,
    register_artifact,
    get_state,
    verify_artifact_integrity
)
from src.utils.logging import setup_logger, get_logger

logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update project state for molecular reactivity pipeline.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: update-stage
    parser_stage = subparsers.add_parser("update-stage", help="Update the status of a pipeline stage")
    parser_stage.add_argument("stage_name", type=str, help="Name of the stage (e.g., ingestion, training)")
    parser_stage.add_argument("status", type=str, choices=["pending", "running", "completed", "failed"],
                              help="New status for the stage")
    parser_stage.add_argument("--details", type=str, default="{}",
                              help="JSON string with additional details")

    # Command: register-artifact
    parser_artifact = subparsers.add_parser("register-artifact", help="Register an output artifact")
    parser_artifact.add_argument("path", type=str, help="Path to the artifact file")
    parser_artifact.add_argument("type", type=str, help="Type of artifact (e.g., dataset, model, report)")
    parser_artifact.add_argument("--metadata", type=str, default="{}",
                                 help="JSON string with additional metadata")

    # Command: verify-artifact
    parser_verify = subparsers.add_parser("verify-artifact", help="Verify artifact integrity")
    parser_verify.add_argument("path", type=str, help="Path to the artifact file")

    # Command: get-state
    parser_get = subparsers.add_parser("get-state", help="Print the current state")

    return parser.parse_args()

def main() -> int:
    args = parse_args()

    if args.command == "update-stage":
        try:
            details = eval(args.details) if isinstance(args.details, str) else args.details
            if not isinstance(details, dict):
                details = {}
            update_stage_status(args.stage_name, args.status, details)
            print(f"Stage '{args.stage_name}' updated to '{args.status}'")
            return 0
        except Exception as e:
            logger.error(f"Failed to update stage: {e}")
            return 1

    elif args.command == "register-artifact":
        try:
            metadata = eval(args.metadata) if isinstance(args.metadata, str) else args.metadata
            if not isinstance(metadata, dict):
                metadata = {}
            register_artifact(args.path, args.type, metadata)
            print(f"Artifact registered: {args.path}")
            return 0
        except Exception as e:
            logger.error(f"Failed to register artifact: {e}")
            return 1

    elif args.command == "verify-artifact":
        is_valid = verify_artifact_integrity(args.path)
        if is_valid:
            print(f"Artifact integrity verified: {args.path}")
            return 0
        else:
            print(f"Artifact integrity check FAILED: {args.path}")
            return 1

    elif args.command == "get-state":
        state = get_state()
        import json
        print(json.dumps(state, indent=2))
        return 0

    else:
        print("Error: No command specified. Use --help for usage.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
