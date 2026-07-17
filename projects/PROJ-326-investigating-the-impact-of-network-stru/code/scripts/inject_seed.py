import argparse
import sys
from pathlib import Path

from code.src.utils.reproducibility import inject_seed_to_log

def main():
    parser = argparse.ArgumentParser(
        description="Inject random seeds from config into the run log for reproducibility."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file (default: code/config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/run_log.json",
        help="Path to the output run log file (default: data/run_log.json)"
    )
    
    args = parser.parse_args()
    
    try:
        result = inject_seed_to_log(args.config, args.output)
        print(f"Seed injected successfully into {args.output}")
        print(f"Verification status: {result['verification']['status']}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
