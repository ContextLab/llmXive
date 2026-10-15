"""
generate_terms.py

Utility script to generate a default list of technical terms used for
computing semantic density. The script writes the list to
`code/config/density_terms.json`. If a user‑provided `user_terms.json` exists,
its terms are used instead of the defaults.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Configure a simple logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_DIR = Path("code/config")
TERMS_FILE = CONFIG_DIR / "density_terms.json"
USER_TERMS_FILE = CONFIG_DIR / "user_terms.json"


def ensure_config_directory() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured config directory exists at {CONFIG_DIR}")


def load_user_terms() -> Optional[List[str]]:
    """
    Load technical terms from a user‑provided JSON file.

    Returns
    -------
    list or None
        List of terms if the file exists and is valid, otherwise None.
    """
    if not USER_TERMS_FILE.exists():
        logger.debug(f"No user terms file found at {USER_TERMS_FILE}")
        return None

    try:
        with USER_TERMS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        terms = data.get("terms")
        if isinstance(terms, list):
            logger.info(f"Loaded {len(terms)} user‑provided terms.")
            return terms
        else:
            logger.error(
                f"User terms file {USER_TERMS_FILE} does not contain a list under the 'terms' key."
            )
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse user terms JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading user terms: {e}")
        return None


def generate_default_terms() -> List[str]:
    """
    Return the built‑in default list of technical terms.

    The list matches the one originally committed in `density_terms.json`.
    """
    default_terms = [
        "entropy",
        "retrieval",
        "context",
        "density",
        "horizon",
        "masking",
        "trajectory",
        "agent",
        "search",
        "stale",
    ]
    logger.info(f"Generated default list of {len(default_terms)} technical terms.")
    return default_terms


def write_terms_file(terms: List[str]) -> None:
    """
    Write the list of terms to `density_terms.json`.

    Parameters
    ----------
    terms : list[str]
        The technical terms to serialize.
    """
    data = {"terms": terms}
    try:
        with TERMS_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(terms)} terms to {TERMS_FILE}")
    except Exception as e:
        logger.error(f"Failed to write terms file {TERMS_FILE}: {e}")
        sys.exit(1)


def main() -> None:
    """
    Entry point for the script.

    The script follows these steps:
    1. Ensure the config directory exists.
    2. Attempt to load user‑provided terms.
    3. If none are found, fall back to the default list.
    4. Write the selected list to `density_terms.json`.
    """
    ensure_config_directory()

    terms = load_user_terms()
    if not terms:
        terms = generate_default_terms()

    write_terms_file(terms)


if __name__ == "__main__":
    main()
