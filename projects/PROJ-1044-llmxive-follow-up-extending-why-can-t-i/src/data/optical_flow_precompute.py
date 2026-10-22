"""
Wrapper around the existing optical‑flow pre‑compute script to ensure that the
``flow_features`` directory exists (used by the counterfactual generator) even
when no pre‑computed FlowNet‑C features are present. This lightweight script
simply creates the directory so that downstream code does not fail.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create placeholder flow_features directory if missing."
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("./output"),
        help="Root output directory (unused, kept for API compatibility).",
    )
    args = parser.parse_args(argv)

    flow_dir = paths.data("flow_features")
    flow_dir.mkdir(parents=True, exist_ok=True)
    log.info("Ensured flow_features directory exists at %s", flow_dir)
    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main())