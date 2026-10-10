"""
Main entry point for the HEA elastic modulus prediction pipeline.

The command ``python -m code.main --stage all`` is the canonical
entry used throughout the documentation.  At this stage of the
project the script only provides a lightweight dispatcher that
acknowledges the requested stage; subsequent tasks will flesh out
the actual pipeline logic.
"""

import argparse
import sys

def _stage_all() -> None:
    """Placeholder for the full pipeline execution."""
    print("🚀 Running full pipeline (stage: all).")
    # Future implementation will invoke fetch → clean → engineer → train → evaluate → report
    # For now we simply acknowledge the request.
    sys.exit(0)

def _stage_fetch() -> None:
    print("⚙️ Fetch stage requested – not yet implemented.")
    sys.exit(0)

def _stage_engineer() -> None:
    print("⚙️ Engineer stage requested – not yet implemented.")
    sys.exit(0)

def _stage_train() -> None:
    print("⚙️ Train stage requested – not yet implemented.")
    sys.exit(0)

def _stage_report() -> None:
    print("⚙️ Report stage requested – not yet implemented.")
    sys.exit(0)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="HEA Elastic Modulus Prediction Pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["all", "fetch", "engineer", "train", "report"],
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args()

    stage_dispatch = {
        "all": _stage_all,
        "fetch": _stage_fetch,
        "engineer": _stage_engineer,
        "train": _stage_train,
        "report": _stage_report,
    }

    # Dispatch to the appropriate stage function
    stage_func = stage_dispatch.get(args.stage)
    if stage_func is None:
        parser.error(f"Unknown stage: {args.stage}")
    else:
        stage_func()

if __name__ == "__main__":
    main()
