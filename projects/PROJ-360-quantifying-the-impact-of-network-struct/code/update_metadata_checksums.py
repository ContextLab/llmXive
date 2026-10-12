"""
Update the project's metadata.yaml with SHA‑256 checksums for all
derived artifacts (graphs, metric tables, result JSON files, etc.).
The script is idempotent: existing entries are refreshed, new files are added.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import logging
import yaml
from llmxive_toolkit import paths, get_logger

# Use the existing logger utility
log = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of the file at *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_metadata(metadata_path: Path) -> dict:
    """Load the existing metadata.yaml (or create a new skeleton)."""
    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    # Ensure required top‑level keys exist
    data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    data.setdefault("project_id", "PROJ-360-quantifying-the-impact-of-network-struct")
    data.setdefault("schema_version", "1.0.0")
    data.setdefault("downloads", [])
    data.setdefault("derived_artifacts", [])
    return data


def save_metadata(metadata_path: Path, data: dict) -> None:
    """Write *data* back to metadata_path preserving a readable layout."""
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )


def collect_artifact_paths() -> list[Path]:
    """
    Return a list of Path objects for all derived artifacts that should be
    tracked. This includes:
    - Network graph pickles (data/processed/networks/*.pkl)
    - Metrics CSV (data/processed/metrics.csv)
    - Correlation JSON (results/correlations.json)
    - Model performance JSON (results/model_performance.json)
    - Any additional result files that exist at runtime.
    """
    roots = [
        paths.data("processed", "networks"),
        paths.data("processed", "metrics.csv"),
        paths.results("correlations.json"),
        paths.results("model_performance.json"),
        paths.results("quickstart_validation_report.json"),
    ]
    artifacts = []
    for root in roots:
        if root.is_dir():
            artifacts.extend(root.rglob("*"))  # include all files in a directory
        elif root.is_file():
            artifacts.append(root)
    # Filter out directories; keep only files
    return [p for p in artifacts if p.is_file()]


def update_derived_section(metadata: dict, artifacts: list[Path]) -> None:
    """
    Refresh the ``derived_artifacts`` section with the current SHA‑256
    checksums. Existing entries are updated; missing ones are added.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    # Build a lookup for quick updates
    existing = {
        entry["artifact_path"]: entry for entry in metadata.get("derived_artifacts", [])
    }

    updated_entries = []
    for art_path in artifacts:
        rel_path = str(art_path.relative_to(paths.root))
        sha = compute_sha256(art_path)
        entry = {
            "artifact_path": rel_path,
            "sha256": sha,
            "timestamp": timestamp,
        }
        updated_entries.append(entry)

    metadata["derived_artifacts"] = updated_entries


def main() -> None:
    """
    Entry point used by the task runner. It updates ``data/metadata.yaml``
    with up‑to‑date checksums for all derived artifacts.
    """
    metadata_path = paths.data("metadata.yaml")
    log.info("Updating metadata at %s", metadata_path)

    metadata = load_metadata(metadata_path)
    artifact_paths = collect_artifact_paths()
    if not artifact_paths:
        log.warning("No derived artifacts found to checksum.")
    else:
        log.info("Found %d artifact(s) to process.", len(artifact_paths))

    update_derived_section(metadata, artifact_paths)
    save_metadata(metadata_path, metadata)
    log.info("Metadata update complete.")


if __name__ == "__main__":
    main()