"""
CLI script to update the project state.
Usage:
  python scripts/update_state.py --stage <stage_name> --status <status>
  python scripts/update_state.py --register <path> --type <type>
  python scripts/update_state.py --status
"""
import argparse
import sys
from datetime import datetime
from typing import Optional

from src.utils.state_manager import (
    get_state,
    update_stage_status,
    register_artifact,
    verify_artifact_integrity,
    get_artifact_checksum
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update project state for molecular reactivity pipeline.")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Update stage status
    parser_stage = subparsers.add_parser("stage", help="Update a pipeline stage status")
    parser_stage.add_argument("--stage", required=True, help="Name of the stage (e.g., ingestion, training)")
    parser_stage.add_argument("--status", required=True, help="Status to set (pending, running, completed, failed)")
    parser_stage.add_argument("--started-at", help="ISO timestamp for start time (optional)")
    parser_stage.add_argument("--completed-at", help="ISO timestamp for completion time (optional)")
    
    # Register artifact
    parser_artifact = subparsers.add_parser("artifact", help="Register a new artifact")
    parser_artifact.add_argument("--path", required=True, help="Path to the artifact file")
    parser_artifact.add_argument("--type", required=True, help="Type of artifact (data, model, report, config)")
    parser_artifact.add_argument("--metadata", help="JSON string of additional metadata (optional)")
    
    # Show current state
    parser_show = subparsers.add_parser("show", help="Display current project state")
    
    # Verify artifact integrity
    parser_verify = subparsers.add_parser("verify", help="Verify artifact integrity")
    parser_verify.add_argument("--path", required=True, help="Path to the artifact to verify")
    
    # Get checksum
    parser_checksum = subparsers.add_parser("checksum", help="Get stored checksum for an artifact")
    parser_checksum.add_argument("--path", required=True, help="Path to the artifact")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command is None:
        print("Error: No command provided. Use --help for usage.")
        return 1

    try:
        if args.command == "stage":
            update_stage_status(
                stage_name=args.stage,
                status=args.status,
                started_at=args.started_at,
                completed_at=args.completed_at or datetime.utcnow().isoformat() if args.status == "completed" else None
            )
            print(f"Stage '{args.stage}' updated to '{args.status}'.")

        elif args.command == "artifact":
            metadata = None
            if args.metadata:
                import json
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON for metadata: {args.metadata}")
                    return 1
            
            register_artifact(
                artifact_path=args.path,
                artifact_type=args.type,
                metadata=metadata
            )
            print(f"Artifact '{args.path}' registered.")

        elif args.command == "show":
            state = get_state()
            import json
            print(json.dumps(state, indent=2, default=str))

        elif args.command == "verify":
            if verify_artifact_integrity(args.path):
                print(f"Artifact '{args.path}' integrity verified.")
                return 0
            else:
                print(f"Artifact '{args.path}' integrity check FAILED.")
                return 1

        elif args.command == "checksum":
            checksum = get_artifact_checksum(args.path)
            if checksum:
                print(f"Checksum for '{args.path}': {checksum}")
            else:
                print(f"No checksum found for '{args.path}'.")
                return 1

        else:
            print(f"Unknown command: {args.command}")
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
