"""
Hygiene script: locate and delete all stray ``t0*.py`` scripts that should have
been migrated into the canonical modules. After successful deletion it logs
the outcome and exits with status 0.
"""

import logging
from pathlib import Path
import sys

from utils import setup_logging


def delete_t0_scripts(base_dir: Path = Path(__file__).resolve().parent.parent / "code") -> None:
    """
    Delete every file matching the pattern ``t0*.py`` inside the supplied
    ``base_dir`` (which defaults to the project’s top‑level ``code`` folder).
    """
    logger = setup_logging(log_level="INFO")
    t0_files = list(base_dir.glob("t0*.py"))
    if not t0_files:
        logger.info("No t0*.py scripts found – nothing to delete.")
        return

    for file_path in t0_files:
        try:
            file_path.unlink()
            logger.info("Deleted %s", file_path.relative_to(base_dir))
        except Exception as exc:
            logger.error("Failed to delete %s: %s", file_path, exc)
            raise

    # Verify deletion
    remaining = list(base_dir.glob("t0*.py"))
    if remaining:
        logger.error("Deletion incomplete – %d t0 scripts remain.", len(remaining))
        raise RuntimeError("Some t0*.py files were not removed.")
    else:
        logger.info("All t0*.py scripts successfully removed.")


def main() -> None:
    """
    Entry‑point used by the quick‑start run‑book. Exits with a non‑zero status
    if anything goes wrong.
    """
    try:
        delete_t0_scripts()
    except Exception as e:
        logging.getLogger(__name__).exception("t0 script cleanup failed: %s", e)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()