"""
Entry point for the project skeleton initialization.

The script is invoked as:
    python -m code.main --phase init

It creates the required sub‑directories under ``code/`` as well as the
top‑level ``tests/``, ``data/`` and ``figures/`` directories.  After
successful creation it prints ``Initialization complete`` which is used
by the quick‑start verification.
"""
import argparse
import sys
from llmxive_toolkit import paths

# List of sub‑directories that must exist under ``code/``.
CODE_SUBDIRS = [
    "analysis",
    "models",
    "quantization",
    "evaluation",
    "utils",
    "data",
    "runners",
    "validation",
    "security",
]

def _create_code_subdirs():
    """Create all required ``code/<subdir>`` folders."""
    for sub in CODE_SUBDIRS:
        # ``paths.code`` returns a ``Path`` inside the project and creates the
        # parent folder if it does not exist.
        sub_path = paths.code(sub)
        sub_path.mkdir(parents=True, exist_ok=True)

def _create_common_dirs():
    """Create top‑level data and figures directories used by the project."""
    # Raw and processed data folders
    paths.data("raw").mkdir(parents=True, exist_ok=True)
    paths.data("processed").mkdir(parents=True, exist_ok=True)
    # Logs sub‑folder inside processed data
    paths.data("processed", "logs").mkdir(parents=True, exist_ok=True)
    # Figures folder
    paths.figures("").mkdir(parents=True, exist_ok=True)

def _create_tests_dir():
    """Create the ``tests/`` package."""
    # The toolkit provides a generic ``tests`` helper via the dynamic attribute.
    # If it does not exist we fall back to a manual Path construction.
    try:
        tests_path = paths.tests("")
    except Exception:
        from pathlib import Path
        tests_path = Path(__file__).resolve().parents[1] / "tests"
    tests_path.mkdir(parents=True, exist_ok=True)

def init_phase():
    """Run the ``init`` phase: create directory skeleton and report success."""
    _create_code_subdirs()
    _create_common_dirs()
    _create_tests_dir()
    print("Initialization complete")

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Project entry point – supports multiple phases."
    )
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        help="Execution phase (e.g. 'init')."
    )
    return parser.parse_args(argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    if args.phase == "init":
        init_phase()
    else:
        print(f"Unknown phase: {args.phase}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
