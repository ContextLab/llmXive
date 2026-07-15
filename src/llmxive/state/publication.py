"""Publication-metadata reader/writer (spec 013 / FR-032).

Owns `projects/<PROJ-ID>/paper/publication.yaml` — the authoritative
record of every published version of a paper. `paper/metadata.json`
mirrors `doi`/`doi_url`/`zenodo_id`/`volume`/`issue` for callers that
only consume JSON, but readers must consult `publication.yaml` for any
authoritative claim about publication state.

Contract: specs/013-paper-revision-implementer/contracts/publication-yaml.md
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from llmxive.state._io import atomic_write_text
from llmxive.types import DOIVersion, Publication

_MIRROR_FIELDS = ("doi", "doi_url", "zenodo_id", "volume", "issue", "doi_versions")


def _yaml_path(project_id: str, *, repo_root: Path) -> Path:
    return repo_root / "projects" / project_id / "paper" / "publication.yaml"


def _metadata_path(project_id: str, *, repo_root: Path) -> Path:
    return repo_root / "projects" / project_id / "paper" / "metadata.json"


def load(project_id: str, *, repo_root: Path) -> Publication | None:
    """Return the canonical Publication, or None if the project hasn't
    been published yet."""
    p = _yaml_path(project_id, repo_root=repo_root)
    if not p.is_file():
        return None
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return Publication.model_validate(data)


def save(
    project_id: str, pub: Publication, *, repo_root: Path, mirror_metadata: bool = True,
) -> None:
    """Write `publication.yaml`. If `mirror_metadata`, also update the
    mirror fields in `paper/metadata.json` (the canonical-but-redundant
    JSON copy that legacy code paths read)."""
    if pub.project_id != project_id:
        raise ValueError(
            f"pub.project_id={pub.project_id!r} != project_id={project_id!r}"
        )
    atomic_write_text(
        _yaml_path(project_id, repo_root=repo_root),
        yaml.safe_dump(pub.model_dump(mode="json"), sort_keys=False),
    )
    if mirror_metadata:
        _mirror_to_metadata_json(project_id, pub, repo_root=repo_root)


def append_version(
    project_id: str,
    version: DOIVersion,
    *,
    repo_root: Path,
    new_canonical: bool = True,
) -> Publication:
    """Append a new DOI version (FR-027). The newly-appended DOI becomes
    the canonical `doi`/`doi_url` if `new_canonical=True` (the default —
    matches Zenodo's newversion semantics). Returns the updated
    Publication. Raises if the project has no existing publication
    (call `save()` first for the initial publication)."""
    pub = load(project_id, repo_root=repo_root)
    if pub is None:
        raise FileNotFoundError(
            f"no publication.yaml for {project_id}; call save() first"
        )
    if any(v.doi == version.doi for v in pub.doi_versions):
        raise ValueError(f"version {version.doi!r} already recorded")
    pub.doi_versions.append(version)
    pub.doi_versions.sort(key=lambda v: v.version_index)
    if new_canonical:
        pub.doi = version.doi
        pub.doi_url = f"https://doi.org/{version.doi}"
        pub.published_at = version.published_at
    save(project_id, pub, repo_root=repo_root)
    return pub


def _mirror_to_metadata_json(
    project_id: str, pub: Publication, *, repo_root: Path
) -> None:
    """Update `paper/metadata.json` with the publication's mirror fields.
    Other fields (authors, arxiv_id, title) are left untouched per FR-016.
    """
    p = _metadata_path(project_id, repo_root=repo_root)
    data: dict[str, object] = {}
    if p.is_file():
        data = json.loads(p.read_text(encoding="utf-8")) or {}
    data["doi"] = pub.doi
    data["doi_url"] = pub.doi_url
    data["zenodo_id"] = pub.zenodo_id
    data["volume"] = pub.volume
    data["issue"] = pub.issue
    data["doi_versions"] = [v.model_dump(mode="json") for v in pub.doi_versions]
    atomic_write_text(p, json.dumps(data, indent=2, sort_keys=False) + "\n")
