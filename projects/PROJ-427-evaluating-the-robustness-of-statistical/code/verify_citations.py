"""
verify_citations.py
--------------------
This module provides a simple citation verification step that scans project
artifacts for URLs (including arXiv identifiers) and checks whether they are
reachable via an HTTP GET request. The results are written to
``state/citation_log.yaml``. If any citation cannot be reached, the script
exits with a non‑zero status, causing the task to fail as required.

The implementation purposefully uses only the standard library plus the
``requests`` and ``pyyaml`` packages, which are already declared in the
project's ``requirements.txt``.
"""

import argparse
import datetime
import json
import logging
import os
import re
import sys
from pathlib import Path

import requests
import yaml

# --------------------------------------------------------------------------- #
# Configuration handling
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG_PATH = Path("config") / "citation_validator.yaml"


def load_config(config_path: str | None = None) -> dict:
    """
    Load a YAML configuration file for the citation validator.

    The configuration is optional; if the file does not exist we fall back
    to a minimal default configuration.

    Parameters
    ----------
    config_path: str | None
        Path to the configuration file. If ``None`` the default location
        ``config/citation_validator.yaml`` is used.

    Returns
    -------
    dict
        Configuration dictionary.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            logging.debug("Loaded citation validator config from %s", path)
            return cfg
    logging.debug("No config file found at %s – using defaults.", path)
    return {
        "file_extensions": [".py", ".md", ".txt", ".yaml", ".yml"],
        "url_regex": r"https?://[^\s\)\"']+",
        "timeout_seconds": 10,
    }

# --------------------------------------------------------------------------- #
# Artifact discovery
# --------------------------------------------------------------------------- #
def find_artifacts(root: Path | str = Path("."), extensions: list[str] | None = None) -> list[Path]:
    """
    Recursively locate files that could contain citations.

    Parameters
    ----------
    root : Path | str
        Directory from which to start the search.
    extensions : list[str] | None
        List of file extensions to include. If ``None`` the extensions from
        the configuration are used.

    Returns
    -------
    list[Path]
        List of file paths.
    """
    root_path = Path(root)
    if extensions is None:
        cfg = load_config()
        extensions = cfg.get("file_extensions", [])
    artifacts = []
    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            artifacts.append(path)
    logging.info("Discovered %d artifact(s) for citation scanning.", len(artifacts))
    return artifacts

# --------------------------------------------------------------------------- #
# Citation extraction
# --------------------------------------------------------------------------- #
URL_PATTERN = re.compile(r"https?://[^\s\)\"']+")
ARXIV_PATTERN = re.compile(r"arxiv\.org/abs/[\d\.]+", re.IGNORECASE)


def extract_citations(file_path: Path) -> list[str]:
    """
    Extract citation URLs from a file.

    Both generic HTTP(S) URLs and arXiv identifiers are captured.

    Parameters
    ----------
    file_path : Path
        Path to the file to be scanned.

    Returns
    -------
    list[str]
        List of unique citation strings found in the file.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logging.warning("Unable to decode %s – skipping.", file_path)
        return []

    citations = set()
    for match in URL_PATTERN.finditer(text):
        citations.add(match.group(0).rstrip(".,"))

    for match in ARXIV_PATTERN.finditer(text):
        # Normalise to a full HTTPS URL for verification
        url = f"https://{match.group(0)}"
        citations.add(url)

    return list(citations)

# --------------------------------------------------------------------------- #
# Citation verification
# --------------------------------------------------------------------------- #
def verify_citation(url: str, timeout: int = 10) -> dict:
    """
    Verify that a citation URL is reachable.

    Parameters
    ----------
    url : str
        The URL to verify.
    timeout : int
        Seconds to wait for a response before considering it unreachable.

    Returns
    -------
    dict
        ``{'url': <url>, 'status': 'reachable'|'unreachable', 'http_code': int|None}``
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        status = "reachable" if response.status_code == 200 else "unreachable"
        return {"url": url, "status": status, "http_code": response.status_code}
    except requests.RequestException as exc:
        logging.debug("Request exception for %s: %s", url, exc)
        return {"url": url, "status": "unreachable", "http_code": None}

# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
def verify_all_citations(root: Path | str = Path("."), config_path: str | None = None) -> dict:
    """
    Scan the project for citations, verify each, and return a consolidated
    report.

    Parameters
    ----------
    root : Path | str
        Directory to start scanning from.
    config_path : str | None
        Optional path to a custom configuration file.

    Returns
    -------
    dict
        Mapping ``url -> verification dict``.
    """
    cfg = load_config(config_path)
    extensions = cfg.get("file_extensions", [])
    timeout = cfg.get("timeout_seconds", 10)

    artifacts = find_artifacts(root=root, extensions=extensions)
    all_citations = set()
    for artifact in artifacts:
        citations = extract_citations(artifact)
        all_citations.update(citations)

    logging.info("Found %d unique citation(s) to verify.", len(all_citations))

    report = {}
    for citation in sorted(all_citations):
        result = verify_citation(citation, timeout=timeout)
        report[citation] = result
    return report

# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def write_citation_log(report: dict, output_path: Path | str = Path("state") / "citation_log.yaml") -> None:
    """
    Write the verification report to a YAML file.

    Parameters
    ----------
    report : dict
        The verification dictionary produced by ``verify_all_citations``.
    output_path : Path | str
        Destination path for the log file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Enrich with timestamp
    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "citations": report,
    }
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    logging.info("Citation verification log written to %s", output_path)

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    """
    Command‑line interface for the citation verification step.

    Returns
    -------
    int
        Exit code: ``0`` on success, ``1`` if any citation is unreachable.
    """
    parser = argparse.ArgumentParser(
        description="Verify citations in project artifacts and record results."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory from which to scan for artifacts (default: current directory).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional path to a YAML configuration file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path("state") / "citation_log.yaml"),
        help="Path where the citation verification log will be written.",
    )
    args = parser.parse_args(argv)

    # Configure a basic logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    report = verify_all_citations(root=args.root, config_path=args.config)
    write_citation_log(report, output_path=args.output)

    # Determine overall success
    unreachable = [url for url, info in report.items() if info["status"] != "reachable"]
    if unreachable:
        logging.error(
            "Citation verification failed – %d unreachable citation(s): %s",
            len(unreachable),
            ", ".join(unreachable),
        )
        return 1
    logging.info("All citations verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
