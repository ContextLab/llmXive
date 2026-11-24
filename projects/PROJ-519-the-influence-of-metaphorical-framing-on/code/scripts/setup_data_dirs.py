"""Create the data/ directory structure (raw, processed, derived).

Task T001b: Create `data/` directory structure with `raw`, `processed`,
and `derived` subdirectories, each containing a `.gitkeep` file so the
empty directories are tracked by version control.
"""

from llmxive_toolkit import paths

SUBDIRS = ("raw", "processed", "derived")


def main() -> None:
    for sub in SUBDIRS:
        d = paths.data(sub)
        keep = d / ".gitkeep"
        keep.touch()
        print(f"created: {d} (with .gitkeep)")


if __name__ == "__main__":
    main()