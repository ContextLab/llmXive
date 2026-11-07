#!/usr/bin/env python
"""
Script to create the project's raw data directory.
This satisfies task T001b by ensuring that `data/raw/` exists.
"""

from llmxive_toolkit import paths


def main() -> None:
    # `paths.data` creates the directory if it does not exist.
    raw_dir = paths.data("raw")
    print(f"Raw data directory created at: {raw_dir}")


if __name__ == "__main__":
    main()