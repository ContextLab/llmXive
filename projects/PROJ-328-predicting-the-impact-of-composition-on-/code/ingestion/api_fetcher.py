"""
API Fetcher for Solder Hardness Data Ingestion.

This script retrieves raw composition‑hardness data from open, publicly
accessible APIs (Materials Project, OpenAlloy, etc.).  The fetched JSON is
stored at ``data/raw/api_fetched.json`` and its SHA‑256 checksum is appended
to ``data/checksums.txt``.

The script is deliberately lightweight: it only performs a single request
to each verified source, logs progress, and fails loudly if any step cannot
be completed.  No synthetic data is generated.
"""
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

import requests
import yaml

# Project‑root utilities
from utils.logger import get_logger
from utils.error_handlers import ConfigurationError, DataFetchError

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
DEFAULT_SOURCES_CONFIG = {
    "materials_project": {
        "verified": False,
        "api_key_env": "MP_API_KEY",
        "url": "https://materialsproject.org/rest/v2",
        "endpoint": "/materials"
    },
    "nist_uci": {
        "verified": False
    },
    "openalloy": {
        "verified": True,
        "url": "https://openalloy.org/api/v1",
        "endpoint": "/compositions"
    }
}

CONFIG_PATH = Path("data/config/sources.yaml")
CHECKSUMS_FILE = Path("data/checksums.txt")
RAW_OUTPUT_FILE = Path("data/raw/api_fetched.json")
RATE_LIMIT_DELAY = 1.0  # seconds between requests


def load_sources_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load the YAML sources configuration, falling back to defaults."""
    if path.exists():
        logger.info(f"Loading sources configuration from {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    else:
        logger.warning(
            f"Sources config file not found at {path}. "
            "Using built‑in default configuration."
        )
        return DEFAULT_SOURCES_CONFIG


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def append_checksum(file_path: Path, checksum: str) -> None:
    """Append a ``filename:checksum`` line to ``data/checksums.txt``."""
    CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHECKSUMS_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{file_path.name}:{checksum}\n")
    logger.info(f"Appended checksum for {file_path.name} to {CHECKSUMS_FILE}")


# ----------------------------------------------------------------------
# API fetch implementations
# ----------------------------------------------------------------------
class APIFetcher:
    """Handles fetching data from the configured API sources."""

    def __init__(self, sources_config: Dict[str, Any] | None = None):
        self.sources_config = sources_config or load_sources_config()
        self.fetched_records: List[Dict[str, Any]] = []
        self.fetch_log: List[Dict[str, Any]] = []

    # ---- Materials Project ------------------------------------------------
    def _fetch_materials_project(self) -> List[Dict[str, Any]]:
        cfg = self.sources_config.get("materials_project", {})
        if not cfg.get("verified", False):
            logger.info("Materials Project source not marked as verified – skipping.")
            return []

        api_key = cfg.get("api_key_env", "MP_API_KEY")
        key = os.getenv(api_key)
        if not key:
            logger.info("MP_API_KEY not set – skipping Materials Project fetch.")
            return []

        base = cfg.get("url", "https://materialsproject.org/rest/v2")
        endpoint = cfg.get("endpoint", "/materials")
        url = f"{base}{endpoint}/v2"

        params = {
            "elements": "Sn",
            "fields": "material_id,pretty_formula,composition",
            "limit": 10
        }
        headers = {"X-Api-Key": key, "Accept": "application/json"}

        logger.info(f"Requesting Materials Project data from {url}")
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("data", [])
            transformed = []
            for item in records:
                transformed.append({
                    "source": "materials_project",
                    "material_id": item.get("material_id"),
                    "formula": item.get("pretty_formula"),
                    "composition": item.get("composition", {}),
                    "hardness_hv": None,
                    "citation": f"Materials Project {item.get('material_id')}"
                })
            logger.info(f"Materials Project: retrieved {len(transformed)} records.")
            return transformed
        except requests.RequestException as exc:
            logger.error(f"Materials Project request failed: {exc}")
            raise DataFetchError("Materials Project fetch failed") from exc

    # ---- NIST/UCI --------------------------------------------------------
    def _fetch_nist_uci(self) -> List[Dict[str, Any]]:
        cfg = self.sources_config.get("nist_uci", {})
        if not cfg.get("verified", False):
            logger.info("NIST/UCI source not verified – skipping.")
            return []

        # No public JSON endpoint is known; we intentionally skip to avoid
        # fabricating data.  The function returns an empty list but logs the
        # decision so the overall pipeline still succeeds.
        logger.info("NIST/UCI: no verified download URL – skipping.")
        return []

    # ---- OpenAlloy --------------------------------------------------------
    def _fetch_openalloy(self) -> List[Dict[str, Any]]:
        cfg = self.sources_config.get("openalloy", {})
        if not cfg.get("verified", False):
            logger.info("OpenAlloy source not verified – skipping.")
            return []

        base = cfg.get("url", "https://openalloy.org/api/v1")
        endpoint = cfg.get("endpoint", "/compositions")
        url = f"{base}{endpoint}"
        params = {"limit": 20}

        logger.info(f"Requesting OpenAlloy data from {url}")
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("data", [])
            transformed = []
            for item in items:
                comp = item.get("composition", {})
                if "Sn" not in comp:
                    continue  # keep only Sn‑based solder candidates
                transformed.append({
                    "source": "openalloy",
                    "alloy_id": item.get("id"),
                    "formula": item.get("name", "unknown"),
                    "composition": comp,
                    "hardness_hv": item.get("hardness_hv"),
                    "citation": f"OpenAlloy {item.get('id')}"
                })
            logger.info(f"OpenAlloy: retrieved {len(transformed)} Sn‑based records.")
            return transformed
        except requests.RequestException as exc:
            logger.error(f"OpenAlloy request failed: {exc}")
            raise DataFetchError("OpenAlloy fetch failed") from exc

    # ------------------------------------------------------------------
    def fetch_all(self) -> Dict[str, Any]:
        """Execute all enabled fetchers and write the combined output."""
        logger.info("Starting API fetch sequence...")

        # Materials Project
        mp = self._fetch_materials_project()
        self.fetched_records.extend(mp)
        self.fetch_log.append(
            {"source": "materials_project", "count": len(mp), "status": "success" if mp else "skipped"}
        )
        time.sleep(RATE_LIMIT_DELAY)

        # NIST/UCI
        nist = self._fetch_nist_uci()
        self.fetched_records.extend(nist)
        self.fetch_log.append(
            {"source": "nist_uci", "count": len(nist), "status": "success" if nist else "skipped"}
        )
        time.sleep(RATE_LIMIT_DELAY)

        # OpenAlloy
        oa = self._fetch_openalloy()
        self.fetched_records.extend(oa)
        self.fetch_log.append(
            {"source": "openalloy", "count": len(oa), "status": "success" if oa else "failed"}
        )

        output = {
            "fetched_data": self.fetched_records,
            "fetch_log": self.fetch_log,
            "total_records": len(self.fetched_records)
        }

        # Ensure output directory exists
        RAW_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON output
        with RAW_OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        logger.info(f"Wrote fetched data to {RAW_OUTPUT_FILE}")

        # Compute and record checksum
        checksum = calculate_sha256(RAW_OUTPUT_FILE)
        append_checksum(RAW_OUTPUT_FILE, checksum)

        return output


def main() -> int:
    """Entry point for ``python -m code.ingestion.api_fetcher``."""
    try:
        fetcher = APIFetcher()
        result = fetcher.fetch_all()
        logger.info(f"API fetch completed – total records: {result['total_records']}")
        return 0
    except ConfigurationError as cfg_err:
        logger.error(f"Configuration error: {cfg_err}")
        return 1
    except DataFetchError as fetch_err:
        logger.error(f"Data fetch error: {fetch_err}")
        return 1
    except Exception as exc:  # pragma: no cover – unexpected failures
        logger.exception(f"Unexpected error during fetch: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
