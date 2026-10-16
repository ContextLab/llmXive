"""Initialise project-owned reproducibility artifacts (Task T004).

The platform owns ``state/`` (including ``state/artifact_hashes.json``);
it is derived at verification time, so this task must NOT create it.
The only project-owned artifact required here is the placeholder
checksum manifest ``data/checksums.json`` (SC-III), initialised to an
empty JSON object ``{}`` if it does not already contain a valid dict.
"""

import json

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def ensure_checksums_manifest() -> None:
    """Create/validate ``data/checksums.json`` as an empty JSON object."""
    path = paths.data("checksums.json")
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            if isinstance(content, dict):
                log.info("Checksum manifest already valid at %s", path)
                return
            log.warning(
                "Existing %s is not a JSON object; resetting to {}", path
            )
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Failed to read existing checksum manifest {path}: {exc}"
            ) from exc
    with open(path, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
        f.write("\n")
    log.info("Initialised empty checksum manifest at %s", path)


def main() -> None:
    ensure_checksums_manifest()
    print("Reproducibility state initialised (project-owned paths only).")


if __name__ == "__main__":
    main()
