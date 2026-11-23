"""Create the data directory tree for the inverse-square-law project.

Task T001-B-INIT-DATA: creates data/raw/, data/processed/, data/results/
under the project root.
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def main() -> None:
    for sub in ("raw", "processed", "results"):
        d = paths.data(sub)
        d.mkdir(parents=True, exist_ok=True)
        if not d.is_dir():
            raise RuntimeError(f"Failed to create data directory: {d}")
        log.info("Ensured data directory exists: %s", d)
    print("Data directory tree created: raw/, processed/, results/")


if __name__ == "__main__":
    main()