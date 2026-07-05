import argparse
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code.src.utils.reproducibility import inject_seed_to_log

def main():
    parser = argparse.ArgumentParser(
        description="Inject a random seed into the run log for reproducibility."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="The random seed to inject."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to the data directory (defaults to project/data)."
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional specific run ID. If not provided, a new one is generated."
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="Optional JSON string of metadata to include."
    )

    args = parser.parse_args()

    metadata = None
    if args.metadata:
        import json
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in metadata: {args.metadata}")
            sys.exit(1)

    try:
        entry = inject_seed_to_log(
            seed=args.seed,
            data_dir=args.data_dir,
            run_id=args.run_id,
            metadata=metadata
        )
        print(f"Successfully injected seed {args.seed}")
        print(f"Run ID: {entry['run_id']}")
        print(f"Log entry: {entry}")
    except Exception as e:
        print(f"Error injecting seed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()