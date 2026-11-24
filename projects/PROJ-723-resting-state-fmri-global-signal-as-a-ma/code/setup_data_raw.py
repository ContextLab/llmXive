"""Create the data/raw/ directory at the repository root (Task T001b).

This directory will hold the downloaded HCP resting-state fMRI data in a
BIDS-compatible structure (sub-<label>/func/) once ingestion (T009) runs.
"""

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

if __name__ == "__main__":
    raw_dir = paths.data("raw")
    # paths.data("raw") already creates the directory; assert it exists.
    assert raw_dir.is_dir(), f"Failed to create {raw_dir}"
    log.info(f"data/raw directory ready at {raw_dir}")
    print(f"OK: {raw_dir} exists")